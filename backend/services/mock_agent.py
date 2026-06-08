"""后端 mock Agent 入口。

这个模块不依赖 PySide6，只接收 shared.protocol 中定义的请求对象并返回响应对象。
未来接真实 Agent、HTTP 服务或 Node 进程时，前端仍然只需要调用这一层暴露的接口。
"""

from __future__ import annotations

from shared.protocol import ChatRequest, ChatResponse, MessageRole

from .mock_reply_rules import match_mock_reply


class MockAgent:
    """演示阶段的后端 Agent。

    当前只返回固定 mock 文案，用来验证前端流程；真实智能体接入后可以替换这个类的实现。
    """

    def reply(self, request: ChatRequest) -> ChatResponse:
        """根据前端请求生成一条后端响应。"""
        reply = match_mock_reply(request.text, request.active_skill_id, request.active_skill_name)
        return ChatResponse(role=MessageRole.ASSISTANT, text=reply)
