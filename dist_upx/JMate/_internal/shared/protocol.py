"""Typed request/response objects shared by the frontend and backend.

The frontend and backend should communicate through these simple protocol
objects instead of importing each other's UI or agent implementation details.
This keeps the PySide6 interface replaceable when the mock backend later
becomes a WebSocket, HTTP, or Node-powered agent service.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class MessageRole(StrEnum):
    """Roles used by chat messages exchanged across the boundary."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LoginProvider(StrEnum):
    """登录来源标识。

    现在先使用 mock/password，后续接入 Microsoft、企业 SSO、设备码登录时，
    前端仍然只传 provider，具体认证细节留给后端处理。
    """

    MOCK = "mock"
    PASSWORD = "password"
    MICROSOFT = "microsoft"
    DEVICE_CODE = "device_code"


@dataclass(frozen=True)
class ChatRequest:
    """Input sent from the desktop frontend to the backend layer."""

    text: str
    active_skill_id: Optional[str] = None
    active_skill_name: str = "通用助手"


@dataclass(frozen=True)
class ChatResponse:
    """Final response returned by the current mock backend.

    Later, streaming backends can emit smaller event objects while still
    preserving this response as the simple synchronous fallback.
    """

    role: MessageRole
    text: str


@dataclass(frozen=True)
class LoginRequest:
    """前端发给后端的登录请求。

    注意：这个对象只描述“用户想登录”，不要在前端里写第三方 API 细节。
    例如 Microsoft OAuth、设备码、token 刷新等，都应该由后端服务处理。
    """

    provider: LoginProvider = LoginProvider.MOCK
    username: str = ""
    password: str = ""


@dataclass(frozen=True)
class LoginResponse:
    """后端返回给前端的登录结果。

    前端只根据 success/user_name/message 更新界面状态；后续如果有真实 token，
    也应该由后端决定是否返回短期会话标识，而不是暴露第三方密钥。
    """

    success: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    access_token: Optional[str] = None
    message: str = ""
