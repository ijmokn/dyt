"""后端 mock 认证服务。

当前只提供演示账号，用于验证前端登录成功和登录失败两条路径。
后续接入 Microsoft、企业 SSO 或第三方 API 时，只需要替换这里的实现，
不需要让登录弹窗直接请求第三方服务。
"""

from __future__ import annotations

from shared.protocol import LoginRequest, LoginResponse


DEMO_USERNAME = "admin"
DEMO_PASSWORD = "123456"


class BackendAuthService:
    """后端认证服务入口，当前是 mock 实现。"""

    def login(self, request: LoginRequest) -> LoginResponse:
        """校验登录请求并返回统一登录结果。"""
        username = request.username.strip()
        password = request.password
        if not username:
            return LoginResponse(success=False, message="请输入用户名")
        if not password:
            return LoginResponse(success=False, message="请输入密码")

        # mock 阶段使用固定演示账号，方便前端同时验证成功界面和失败界面。
        if username != DEMO_USERNAME or password != DEMO_PASSWORD:
            return LoginResponse(success=False, message="用户名或密码不正确，请重新输入。")

        return LoginResponse(
            success=True,
            user_id=f"mock:{username}",
            user_name=username,
            access_token=None,
            message="登录成功",
        )
