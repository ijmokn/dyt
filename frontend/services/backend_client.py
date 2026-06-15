"""前端访问后端的统一客户端。

界面层和前端 service 只能通过 BackendClient 访问后端能力。
当前默认实现是进程内本地 mock；后续切换为 HTTP、WebSocket、stdio 或 Node.js 时，
只需要替换内部 adapter，不需要修改 ChatView、LoginDialog 等界面组件。
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Protocol


# 前端目录和 backend/shared 是兄弟目录。开发阶段先把项目根目录加入 sys.path，
# 这样前端可以通过统一客户端访问 shared 协议和本地 mock 后端。
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.auth_service import BackendAuthService  # noqa: E402
from backend.services.azure_agent import AzureAgent  # noqa: E402
from shared.protocol import ChatRequest, ChatResponse, LoginRequest, LoginResponse  # noqa: E402


__all__ = ["BackendClient"]


class _BackendAdapter(Protocol):
    """后端适配器协议。

    不同后端接入方式都应该实现这两个方法，例如本地 Python mock、HTTP 客户端、
    WebSocket 客户端或 Node.js 子进程客户端。
    """

    def send_chat(self, request: ChatRequest) -> ChatResponse:
        """发送聊天请求并返回最终回复。"""

    def login(self, request: LoginRequest) -> LoginResponse:
        """发送登录请求并返回登录结果。"""


class _LocalBackendAdapter:
    """本地进程内后端适配器。
    这个类只服务于当前开发阶段，把前端请求转发给 Python mock 后端。
    未来接真实后端时，可以新增其他 adapter 并替换 BackendClient 的默认 adapter。
    """

    def __init__(self) -> None:
        # 程序启动时初始化 Azure Agent；点击发送时复用这个实例处理聊天请求。
        self._agent = AzureAgent()
        self._auth_service = BackendAuthService()

    def send_chat(self, request: ChatRequest) -> ChatResponse:
        """把聊天请求转发给当前 mock Agent。"""
        return self._agent.reply(request)

    def login(self, request: LoginRequest) -> LoginResponse:
        """把登录请求转发给当前 mock 认证服务。"""
        return self._auth_service.login(request)


class BackendClient:
    """前端 service 层使用的唯一后端入口。

    对外只暴露 send_chat 和 login。调用方不需要知道请求最终是发给本地 mock、
    HTTP 服务、WebSocket 服务，还是 Node.js 进程。
    """

    def __init__(self, adapter: _BackendAdapter | None = None) -> None:
        # 默认使用本地 mock 后端；测试或真实接入时可以注入其他 adapter。
        self._adapter = adapter or _LocalBackendAdapter()

    def send_chat(self, request: ChatRequest) -> ChatResponse:
        """发送聊天请求到后端边界。"""
        return self._adapter.send_chat(request)

    def login(self, request: LoginRequest) -> LoginResponse:
        """发送登录请求到后端边界。"""
        return self._adapter.login(request)
