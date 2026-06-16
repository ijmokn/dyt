"""后端 mock 认证服务。"""

from __future__ import annotations

from shared.protocol import LoginRequest, LoginResponse


class BackendAuthService:
    """当前演示阶段的登录校验：社员号必须为 8 位数字，密码可不填写。"""

    def login(self, request: LoginRequest) -> LoginResponse:
        member_id = request.username.strip()
        if not member_id:
            return LoginResponse(success=False, message="请输入社员号")
        if len(member_id) != 8 or not member_id.isdigit():
            return LoginResponse(success=False, message="社员号格式不正确，请输入8位数字。")

        return LoginResponse(
            success=True,
            user_id=f"mock:{member_id}",
            user_name=member_id,
            access_token=None,
            message="登录成功",
        )
