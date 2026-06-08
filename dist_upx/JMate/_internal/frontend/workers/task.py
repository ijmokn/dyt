"""Simple worker utilities using QRunnable and Qt signals.

Provides a `Worker` that runs a callable on a threadpool and emits a `finished`
signal with the result, or `error` on exception.

提供一个 Worker，它会在线程池中执行一个可调用对象，
并在执行成功后通过 finished 信号返回结果；如果发生异常，则发送 error 信号。
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot, QThreadPool


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(object)


class Worker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001 - handle broadly
            self.signals.error.emit(exc)
        else:
            self.signals.finished.emit(result)


def submit(fn: Callable[..., Any], *args, **kwargs) -> Worker:
    """Submit a callable to the global thread pool and return the Worker."""
    worker = Worker(fn, *args, **kwargs)
    QThreadPool.globalInstance().start(worker)
    return worker
