"""JMate Hub Agent：本地 Skills 与 Foundry 托管智能体的混合架构。"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import sys
import threading
from concurrent.futures import Future
from pathlib import Path

from azure.identity import DefaultAzureCredential

from backend.services.agent_config import load_agent_config
from shared.protocol import ChatRequest, ChatResponse, MessageRole

logger = logging.getLogger(__name__)

hub_agent = None
session = None
hub_init_error: Exception | None = None
hub_initializing = False
hub_initialized = False

_init_lock = threading.Lock()
_event_loop: asyncio.AbstractEventLoop | None = None
_request_queue: queue.Queue[tuple[ChatRequest, Future]] = queue.Queue()


def _application_root() -> Path:
    """返回源码项目目录或 PyInstaller 单文件程序的解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def initialize_hub_agent() -> None:
    """按照 hybrid_local_foundry.py 的架构初始化 Hub Agent。"""
    global hub_agent, session, hub_init_error, hub_initializing, hub_initialized

    with _init_lock:
        if hub_initialized:
            logger.info("Hub Agent 已初始化，跳过重复操作")
            return
        if hub_initializing:
            logger.info("Hub Agent 正在初始化，跳过重复操作")
            return
        hub_initializing = True

    logger.info("Hub Agent 初始化开始")

    try:
        config = load_agent_config()

        # 当前版本的 Agent Framework 遥测存在异步上下文清理异常。
        # JMate 使用自己的 logging，因此关闭遥测不影响 Agent 和 Skill 功能。
        os.environ.setdefault("ENABLE_INSTRUMENTATION", "false")

        from agent_framework import Agent, SkillsProvider
        from agent_framework.foundry import FoundryAgent, FoundryChatClient
        from agent_framework.observability import disable_instrumentation

        from backend.services.skill_script_runner import subprocess_script_runner

        disable_instrumentation()

        endpoint = config.project_endpoint
        deployment = config.model
        credential = DefaultAzureCredential()

        # ================================================================
        # 1. 本地 Skills：考勤导出、单位转换等操作类任务
        # ================================================================
        skills_dir = _application_root() / "backend" / "skills"
        skills_provider = SkillsProvider.from_paths(
            skill_paths=str(skills_dir),
            script_runner=subprocess_script_runner,
        )

        # ================================================================
        # 2. Foundry 托管智能体：公司规则与制度查询
        # ================================================================
        company_rules_agent = FoundryAgent(
            project_endpoint=endpoint,
            agent_name=config.agent_name,
            agent_version=config.agent_version,
            credential=credential,
        )

        company_rules_tool = company_rules_agent.as_tool(
            name="query_company_rules",
            description=(
                "查询公司规章制度、人事政策、报销流程、休假规定等内部知识。"
                "当用户询问任何与公司规定相关的问题时，使用此工具。"
            ),
            arg_name="question",
            arg_description="要查询的公司规则相关问题",
        )

        # ================================================================
        # 3. Hub Agent：本地总编排与调度
        # ================================================================
        hub_agent = Agent(
            client=FoundryChatClient(
                project_endpoint=endpoint,
                model=deployment,
                credential=credential,
            ),
            name="hub",
            instructions=(
                "你是智能助手 Hub。\n\n"
                "你的能力分为三类：\n"
                "1. 操作类任务（考勤导出、月末文件导出、单位转换等）"
                "使用 skill 工具自行处理。\n"
                "2. 公司规则查询（人事政策、报销制度、休假规定等）"
                "使用 query_company_rules 工具。\n"
                "3. 普通问答（天气、闲聊、知识问答）直接调用 LLM 回答。\n\n"
                "你可以自行调用工具完成任务，无需等待用户确认。"
            ),
            context_providers=[skills_provider],
            tools=[company_rules_tool],
        )

        # ================================================================
        # 4. 会话：Hub Agent 自动维护多轮对话历史
        # ================================================================
        session = hub_agent.create_session()

        hub_init_error = None
        hub_initialized = True
        logger.info(
            "Hub Agent 初始化成功：model=%s, managed_agent=%s, version=%s",
            deployment,
            config.agent_name,
            config.agent_version,
        )
    except Exception as exc:
        hub_agent = None
        session = None
        hub_initialized = False
        hub_init_error = exc
        logger.exception("Hub Agent 初始化失败：%s", exc)
    finally:
        hub_initializing = False


def _hub_runtime_main() -> None:
    """在桌面程序专用后台线程中运行 Hub Agent。"""
    global _event_loop

    loop = asyncio.new_event_loop()
    _event_loop = loop
    asyncio.set_event_loop(loop)
    initialize_hub_agent()

    if hub_initialized:
        logger.info("Hub Agent 专用请求线程已启动")
        while True:
            request, result_future = _request_queue.get()
            try:
                prompt = request.text
                if not request.skills_enabled:
                    prompt = (
                        "[JMate 运行模式：本轮已关闭本地 Skills。禁止调用本地 Skill，"
                        "但公司规则工具和普通问答仍可正常使用。]\n"
                        f"用户问题：{request.text}"
                    )

                response = loop.run_until_complete(
                    hub_agent.run(prompt, session=session)
                )
                result_future.set_result(response)
            except Exception as exc:
                result_future.set_exception(exc)

    loop.close()


def start_initialize_hub_agent_async() -> threading.Thread:
    """程序启动时在后台初始化 Hub Agent，避免阻塞桌面窗口。"""
    thread = threading.Thread(
        target=_hub_runtime_main,
        name="HubAgentInit",
        daemon=True,
    )
    thread.start()
    logger.info("Hub Agent 后台初始化线程已启动：%s", thread.name)
    return thread


class HubAgent:
    """JMate 后端调用 Hub Agent 的同步入口。"""

    def reply(self, request: ChatRequest) -> ChatResponse:
        """提交聊天请求，并将 Agent Framework 响应转换为 JMate 响应。"""
        if hub_initializing:
            return ChatResponse(MessageRole.ASSISTANT, "Hub Agent 正在初始化，请稍后再试。")

        if hub_init_error is not None:
            return ChatResponse(MessageRole.ASSISTANT, f"Hub Agent 初始化失败：{hub_init_error}")

        if hub_agent is None or session is None or _event_loop is None:
            return ChatResponse(MessageRole.ASSISTANT, "Hub Agent 尚未完成程序启动初始化。")

        logger.info(
            "Hub Agent 收到消息：skills_enabled=%s, active_skill_id=%s",
            request.skills_enabled,
            request.active_skill_id,
        )

        try:
            future: Future = Future()
            _request_queue.put((request, future))
            response = future.result()
            logger.info("Hub Agent 调用成功")
            return ChatResponse(
                MessageRole.ASSISTANT,
                response.text or "Hub Agent 没有返回文本内容。",
            )
        except Exception as exc:
            logger.exception("Hub Agent 调用失败：%s", exc)
            return ChatResponse(MessageRole.ASSISTANT, f"Hub Agent 调用失败：{exc}")
