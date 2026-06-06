"""Lightweight service layer for chat-related business logic.

This module provides a minimal `ChatService` with a `get_reply` method.
The implementation is currently frontend-only (stub), returning deterministic
responses based on active skill and user text. Later this can call network
APIs, models, or workers without changing UI code.
"""

from __future__ import annotations

from typing import Optional, Callable
from PySide6.QtCore import QThreadPool

from workers.task import Worker


class ChatService:
    """Encapsulate chat reply generation logic.

    The real implementation should be async or perform I/O in a worker and
    return results via callbacks/signals. This stub provides the same
    deterministic responses as the previous `_mock_reply` function.
    """

    def __init__(self) -> None:
        # Keep QRunnable wrappers alive until their signals finish.
        self._workers = []

    def get_reply(self, user_input: str, active_skill_id: Optional[str], active_skill_name: str) -> str:
        """Return a reply string for the given input and active skill."""
        skill_id = active_skill_id
        if skill_id == "email" or "考勤" in user_input:
            return (
                "⏰ 月末考勤助手\n"
                "已为你生成考勤核对示例：本月出勤记录待确认，异常打卡 2 条，建议先核对外勤和补卡记录。"
            )
        if skill_id == "summary" or "休假" in user_input:
            return (
                "📄 休假申请助手\n"
                "示例申请已生成：申请人、休假类型、起止时间与交接说明已预留字段，可继续补充具体日期。"
            )
        if skill_id == "schedule" or "加班" in user_input:
            return (
                "⏱ 加班申请助手\n"
                "已生成加班申请草稿：加班事由、预计时长、项目关联和审批备注均为前端占位展示。"
            )
        if skill_id == "report" or "填写" in user_input:
            return (
                "📊 **智能考勤填写** 【本周重点工作】\n"
                "1. 完成需求分析与技术方案设计，输出文档2份\n"
                "2. 修复线上故障3处，优化接口响应速度12%\n"
                "3. 协同跨部门推进项目里程碑\n"
                "【下周计划】核心功能开发与联调、用户反馈收集与迭代规划。"
            )
        return (
            f"✅ J-Mate 办公智能引擎（当前技能：{active_skill_name}）\n"
            f"已收到你的指令：“{user_input}”。这里是纯前端演示回复，没有调用模型或后端接口。"
        )

    def get_reply_async(self, user_input: str, active_skill_id: Optional[str], active_skill_name: str, callback: Callable[[str], None], errback: Callable[[Exception], None] | None = None) -> None:
        """Run `get_reply` in a worker and call `callback(reply)` on completion.

        `callback` will be invoked with the reply string. `errback` is optional
        and receives the exception instance if the worker raises.
        """

        def _run(u: str, a_id: Optional[str], a_name: str) -> str:
            return self.get_reply(u, a_id, a_name)

        worker = Worker(_run, user_input, active_skill_id, active_skill_name)
        self._workers.append(worker)

        def _release_worker(*_args) -> None:
            if worker in self._workers:
                self._workers.remove(worker)

        worker.signals.finished.connect(lambda result: callback(result))
        worker.signals.finished.connect(_release_worker)
        if errback:
            worker.signals.error.connect(lambda exc: errback(exc))
        worker.signals.error.connect(_release_worker)
        QThreadPool.globalInstance().start(worker)
