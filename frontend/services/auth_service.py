"""前端认证服务。

登录弹窗只负责收集用户输入；这个服务负责把输入转换成 shared 协议对象，
再交给 BackendClient。这样以后登录方式变成 Microsoft、设备码或 SSO 时，
UI 不需要直接接触第三方 API。
"""

from __future__ import annotations

from frontend.services.backend_client import BackendClient
from shared.protocol import LoginProvider, LoginRequest, LoginResponse


class AuthService:
    """前端认证入口，供 LoginDialog 调用。"""

    def __init__(self, backend_client: BackendClient | None = None) -> None:
        self._backend_client = backend_client or BackendClient()

    def login(self, username: str, password: str) -> LoginResponse:
        """提交登录请求，当前走 mock 登录协议。"""
        request = LoginRequest(
            provider=LoginProvider.MOCK,
            username=username,
            password=password,
        )
        return self._backend_client.login(request)
