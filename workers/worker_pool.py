"""
WorkerPool — 多 Worker 生命周期管理

职责：
- 管理最多 N 个并发 AgentWorker 实例
- Worker 与 UI 信号解耦：切会话时 detach/attach 信号
- 任务完成或超时后回收 Worker 资源
"""
import threading
from typing import Dict, Optional, Callable, List, Any
from datetime import datetime

from PySide6.QtCore import QObject

from workers.agent_worker import AgentWorker
from workers.session_task import SessionTask, TaskStatus


class WorkerPool(QObject):
    """Worker 池：管理并发 AgentWorker 的生命周期。

    Worker 独立于 UI 运行，切会话时不停止，只在 detach/attach 信号。
    """

    def __init__(self, max_workers: int = 3):
        super().__init__()
        self._max_workers = max(1, int(max_workers))
        self._workers: Dict[str, AgentWorker] = {}          # session_id → Worker
        self._worker_tasks: Dict[str, SessionTask] = {}      # session_id → SessionTask
        self._phase_callbacks: Dict[str, Callable] = {}      # session_id → phase_change_callback
        self._done_callbacks: Dict[str, Callable] = {}       # session_id → task_done_callback
        self._thread_lock = threading.Lock()
        self._shutting_down = False

    @property
    def active_count(self) -> int:
        return len(self._workers)

    @property
    def has_capacity(self) -> bool:
        return self.active_count < self._max_workers

    def submit(
        self,
        task: SessionTask,
        phase_callback: Callable[[str, str, str], None],
        done_callback: Callable[[str, bool], None],
    ):
        """提交任务到 WorkerPool。创建 Worker 并连接信号。"""
        if self._shutting_down:
            done_callback(task.session_id, False)
            return

        with self._thread_lock:
            self._phase_callbacks[task.session_id] = phase_callback
            self._done_callbacks[task.session_id] = done_callback
            self._worker_tasks[task.session_id] = task

    def get_worker(self, session_id: str) -> Optional[AgentWorker]:
        """获取指定会话的 Worker（从外部注入）"""
        return self._workers.get(session_id)

    def add_worker(self, session_id: str, worker: AgentWorker):
        """将已创建的 Worker 注册到池中"""
        with self._thread_lock:
            self._workers[session_id] = worker

    def remove_worker(self, session_id: str):
        """从池中移除 Worker"""
        with self._thread_lock:
            self._workers.pop(session_id, None)

    def cancel(self, session_id: str):
        """取消指定会话的任务"""
        worker = self._workers.get(session_id)
        if worker:
            worker.stop()
        self.remove_worker(session_id)
        self._worker_tasks.pop(session_id, None)
        self._phase_callbacks.pop(session_id, None)

        cb = self._done_callbacks.pop(session_id, None)
        if cb:
            cb(session_id, False)

    def on_task_complete(self, session_id: str):
        """任务完成后回收 Worker 资源"""
        self.remove_worker(session_id)
        self._worker_tasks.pop(session_id, None)
        self._phase_callbacks.pop(session_id, None)
        self._done_callbacks.pop(session_id, None)

    def get_task(self, session_id: str) -> Optional[SessionTask]:
        return self._worker_tasks.get(session_id)

    def is_running(self, session_id: str) -> bool:
        return session_id in self._workers

    def list_active_sessions(self) -> List[str]:
        return list(self._workers.keys())

    def shutdown(self):
        """关闭所有 Worker"""
        self._shutting_down = True
        with self._thread_lock:
            workers = list(self._workers.values())
        for w in workers:
            w.stop()
        self._workers.clear()
        self._worker_tasks.clear()
        self._phase_callbacks.clear()
        self._done_callbacks.clear()
