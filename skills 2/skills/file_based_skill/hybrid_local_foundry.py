# Copyright (c) Microsoft. All rights reserved.
# 安装 Agent Framework（如果还没安装）
# pip install agent-framework-foundry azure-identity python-dotenv

# 安装 Playwright（用于浏览器自动化）
# pip install playwright

# 下载 Chromium 浏览器（首次使用必需）
# playwright install chromium

import asyncio
import os
import sys

from pathlib import Path

from agent_framework import Agent, SkillsProvider
from agent_framework.foundry import FoundryAgent, FoundryChatClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Add the skills folder root to sys.path so the shared subprocess_script_runner can be imported
_SKILLS_ROOT = str(Path(__file__).resolve().parent.parent)
if _SKILLS_ROOT not in sys.path:
    sys.path.insert(0, _SKILLS_ROOT)

from subprocess_script_runner import subprocess_script_runner  # noqa: E402

"""
混合架构: 本地 Agent (直连 LLM + Skills) + Foundry 托管智能体

架构:
    Triage Agent (本地, 直连 LLM)
        ├── 考勤导出 / 单位转换 → SkillsProvider (本地 Skills)
        ├── 公司规则 / 制度查询  → Foundry 托管智能体 (通过 as_tool 调用)
        └── 普通问答           → 直接调用 LLM 回答

职责分离:
    - 本地 Agent: 轻量级路由 + 本地操作类任务
    - Foundry 智能体: 公司知识库 / 规则引擎 (服务端管理、版本化、可共享)
"""

# Load environment variables from .env file
load_dotenv()


class Colors:
    """终端颜色输出."""

    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"


def _print_agent_header(agent_name: str, text: str) -> None:
    """打印 Agent 输出，带颜色区分."""
    color_map = {
        "triage": Colors.CYAN,
        "company-rules": Colors.MAGENTA,
    }
    color = color_map.get(agent_name, Colors.YELLOW)
    print(f"{color}[{agent_name}]{Colors.RESET} {text}")


async def main() -> None:
    """Run the hybrid local + Foundry agent demo."""
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    deployment = os.environ.get("FOUNDRY_MODEL", "gpt-5")
    credential = DefaultAzureCredential()

    # ================================================================
    # 1. 本地 Skills — 考勤导出、单位转换等操作类任务
    # ================================================================
    skills_dir = Path(__file__).parent / "skills"
    skills_provider = SkillsProvider.from_paths(
        skill_paths=str(skills_dir),
        script_runner=subprocess_script_runner,
    )

    # ================================================================
    # 2. Foundry 托管智能体 — 公司规则 / 制度查询
    #    这个智能体在 Foundry 平台上已经发布 (PromptAgent 或 HostedAgent)
    #    公司规则、FAQ、制度文档等知识都由它统一管理
    # ================================================================
    company_rules_agent = FoundryAgent(
        project_endpoint=endpoint,
        agent_name=os.environ.get("FOUNDRY_AGENT_NAME", "company-rules-agent"),
        # PromptAgent 需要版本号, HostedAgent 不需要
        agent_version=os.environ.get("FOUNDRY_AGENT_VERSION"),
        credential=credential,
    )

    # 将 Foundry 智能体包装成本地 Agent 的一个工具
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
    # 3. Triage Agent — 本地智能体（路由 + 调度）
    #    - 直连 LLM 处理普通对话
    #    - SkillsProvider 处理本地操作 (考勤导出等)
    #    - company_rules_tool 委派给 Foundry 智能体查询公司规则
    # ================================================================
    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=endpoint,
            model=deployment,
            credential=credential,
        ),
        name="triage",
        instructions=(
            "你是智能助手 Triage。\n\n"
            "你的能力分为三类：\n"
            "1. **操作类任务**（考勤导出、月末文件导出、单位转换等）→ 使用 skill 工具自行处理\n"
            "2. **公司规则查询**（人事政策、报销制度、休假规定等）→ 使用 query_company_rules 工具\n"
            "3. **普通问答**（天气、闲聊、知识问答）→ 直接回答\n\n"
            "你可以自行调用工具完成任务，无需等待用户确认。"
        ),
        context_providers=[skills_provider],
        tools=[company_rules_tool],
    )

    # ================================================================
    # 4. 交互式对话（带上下文记忆）
    # ================================================================
    # 创建会话对象 - Agent 会自动维护对话历史
    session = agent.create_session()

    print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}  混合架构 Demo: 本地 Agent + Foundry 智能体{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"  [本地] Triage Agent  →  直连 LLM + 本地 Skills")
    print(f"  [云端] 公司规则智能体 →  Foundry 托管")
    print(f"  {Colors.MAGENTA}✓ 对话上下文已启用{Colors.RESET} - 可以多轮对话")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"  输入你的问题，Enter 发送")
    print(f"  输入 {Colors.YELLOW}quit{Colors.RESET} 或 {Colors.YELLOW}exit{Colors.RESET} 退出")
    print(f"  试试:")
    print(f"    {Colors.CYAN}• 上级管理职去北京出差，交通和补助查询?{Colors.RESET}        → 走 Foundry 智能体")
    print(f"    {Colors.CYAN}• 帮我导出月末文件{Colors.RESET}               → 走本地 Skill (monthly-files-export)")
    print(f"    {Colors.CYAN}• Python是谁发明的{Colors.RESET}                 → 直连 LLM")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}\n")

    while True:
        try:
            prompt = input(f"{Colors.CYAN}>>> {Colors.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}再见！{Colors.RESET}")
            break

        if not prompt:
            continue
        if prompt.lower() in ("quit", "exit"):
            print(f"{Colors.YELLOW}再见！{Colors.RESET}")
            break

        print()
        try:
            # 传入 session - Agent 会自动加载历史消息并保存新的响应
            response = await agent.run(prompt, session=session)
            for msg in response.messages:
                speaker = msg.author_name or "unknown"
                _print_agent_header(speaker, msg.text or "")
        except Exception as e:
            print(f"{Colors.YELLOW}[ERROR] {e}{Colors.RESET}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
