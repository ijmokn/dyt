"""JMate 调用 Azure Foundry Agent。"""

from __future__ import annotations

import logging
import threading

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from backend.services.agent_config import load_agent_config
from shared.protocol import ChatRequest, ChatResponse, MessageRole

logger = logging.getLogger(__name__)

endpoint = ""
project_client = None
my_agent = ""
my_version = ""
openai_client = None
azure_init_error = None
azure_initializing = False
azure_initialized = False
_init_lock = threading.Lock()


def initialize_azure_agent() -> None:
    """程序启动初始化：在桌面程序启动时创建 Azure Agent 调用客户端。"""
    global endpoint, project_client, my_agent, my_version, openai_client, azure_init_error, azure_initializing, azure_initialized

    with _init_lock:
        if azure_initialized:
            logger.info("Azure Agent 已完成初始化，跳过重复初始化")
            return
        if azure_initializing:
            logger.info("Azure Agent 正在初始化，跳过重复初始化")
            return
        azure_initializing = True

    logger.info("Azure Agent 程序启动初始化开始")

    try:
        config = load_agent_config()

        # 程序启动初始化
        endpoint = config.project_endpoint
        logger.info("Azure Agent endpoint = %s", endpoint)

        logger.info("Azure Agent 创建 DefaultAzureCredential")
        credential = DefaultAzureCredential()

        logger.info("Azure Agent 创建 AIProjectClient")
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )

        my_agent = config.agent_name
        my_version = config.agent_version
        logger.info("Azure Agent agent_reference name=%s, version=%s", my_agent, my_version)

        logger.info("Azure Agent 获取 OpenAI client")
        openai_client = project_client.get_openai_client()
        azure_init_error = None
        azure_initialized = True
        logger.info("Azure Agent 程序启动初始化成功")
    except Exception as exc:
        openai_client = None
        azure_initialized = False
        azure_init_error = exc
        logger.exception("Azure Agent 程序启动初始化失败：%s", exc)
    finally:
        azure_initializing = False


def start_initialize_azure_agent_async() -> threading.Thread:
    """程序启动时开后台线程初始化 Azure Agent，避免阻塞桌面窗口显示。"""
    thread = threading.Thread(
        target=initialize_azure_agent,
        name="AzureAgentInit",
        daemon=True,
    )
    thread.start()
    logger.info("Azure Agent 初始化线程已启动：%s", thread.name)
    return thread


class AzureAgent:
    """把聊天输入框文本发送给 Azure Agent，并把结果返回给上方结果显示区。"""

    def reply(self, request: ChatRequest) -> ChatResponse:
        if azure_initializing:
            return ChatResponse(role=MessageRole.ASSISTANT, text="Azure Agent 正在初始化，请稍后再试。")

        if azure_init_error is not None:
            return ChatResponse(role=MessageRole.ASSISTANT, text=f"Azure Agent 初始化失败：{azure_init_error}")

        if openai_client is None:
            return ChatResponse(role=MessageRole.ASSISTANT, text="Azure Agent 尚未完成程序启动初始化。")

        # Reference the agent to get a response
        logger.info("Azure Agent 点击发送，调用 Agent。输入内容：%s", request.text)
        response = openai_client.responses.create(
            input=[{"role": "user", "content": request.text}],
            extra_body={"agent_reference": {"name": my_agent, "version": my_version, "type": "agent_reference"}}
        )
        logger.info("Azure Agent 调用成功，已收到 response.output_text")

        return ChatResponse(role=MessageRole.ASSISTANT, text=response.output_text)
