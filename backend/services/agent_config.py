"""JMate 智能体与 Azure AD 认证配置。"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

REQUIRED_AGENT_ENV_KEYS = (
    "FOUNDRY_PROJECT_ENDPOINT",
    "FOUNDRY_MODEL",
    "FOUNDRY_AGENT_NAME",
    "FOUNDRY_AGENT_VERSION",
    "AZURE_CLIENT_ID",
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_SECRET",
)


class AgentConfigError(Exception):
    """智能体配置缺失或格式不正确。"""


@dataclass(frozen=True)
class AgentConfig:
    """Hub、Foundry 托管 Agent 和 Azure AD 使用的完整配置。"""

    project_endpoint: str
    model: str
    agent_name: str
    agent_version: str
    azure_client_id: str
    azure_tenant_id: str
    azure_client_secret: str


def _application_root() -> Path:
    """返回源码项目目录或 PyInstaller 单文件程序的解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def _runtime_root() -> Path:
    """返回源码项目目录或打包后 EXE 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _application_root()


def _load_environment_files() -> None:
    """读取外部或打包内的环境配置，不覆盖系统已设置的环境变量。"""
    candidates = [
        _runtime_root() / ".env",
        _runtime_root() / "azure.env",
        _application_root() / ".env",
        _application_root() / "azure.env",
    ]
    loaded_paths: set[Path] = set()

    for path in candidates:
        resolved_path = path.resolve()
        if resolved_path in loaded_paths or not resolved_path.is_file():
            continue
        load_dotenv(resolved_path, override=False)
        loaded_paths.add(resolved_path)
        logger.info("已加载智能体配置文件：%s", resolved_path)


def load_agent_config() -> AgentConfig:
    """加载完整配置；任何必填项缺失时直接报错，不使用代码兜底值。"""
    _load_environment_files()

    values = {key: os.environ.get(key, "").strip() for key in REQUIRED_AGENT_ENV_KEYS}
    missing_keys = [key for key, value in values.items() if not value]
    if missing_keys:
        raise AgentConfigError("智能体配置缺少必填项：" + ", ".join(missing_keys))

    return AgentConfig(
        project_endpoint=values["FOUNDRY_PROJECT_ENDPOINT"],
        model=values["FOUNDRY_MODEL"],
        agent_name=values["FOUNDRY_AGENT_NAME"],
        agent_version=values["FOUNDRY_AGENT_VERSION"],
        azure_client_id=values["AZURE_CLIENT_ID"],
        azure_tenant_id=values["AZURE_TENANT_ID"],
        azure_client_secret=values["AZURE_CLIENT_SECRET"],
    )
