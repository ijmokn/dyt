"""前端聊天服务。

这个模块负责把界面输入转换成 shared 协议对象，并通过 BackendClient 发送给后端。
ChatView 不直接知道后端实现，因此后续切换 HTTP、WebSocket 或 Node.js 不需要改页面。
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QThreadPool

from frontend.services.backend_client import BackendClient
from shared.protocol import ChatRequest
from workers.task import Worker


class ChatService:
    """协调 UI 到后端客户端的聊天请求。"""

    def __init__(self, backend_client: BackendClient | None = None) -> None:
        # 保留 Worker 引用直到信号结束，避免 mock 回复太快时 QRunnable 被回收导致 UI 收不到结果。
        self._workers = []
        self._backend_client = backend_client or BackendClient()

    def get_reply(
        self,
        user_input: str,
        active_skill_id: Optional[str],
        active_skill_name: str,
    ) -> str:
        """同步获取一条后端回复，供测试或简单调用使用。"""
        request = ChatRequest(
            text=user_input,
            active_skill_id=active_skill_id,
            active_skill_name=active_skill_name,
        )
        response = self._backend_client.send_chat(request)
        return response.text

    def get_reply_async(
        self,
        user_input: str,
        active_skill_id: Optional[str],
        active_skill_name: str,
        callback: Callable[[str], None],
        errback: Callable[[Exception], None] | None = None,
    ) -> None:
        """在线程池中获取回复，完成后通过 callback 通知界面。"""

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
