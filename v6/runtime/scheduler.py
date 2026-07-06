"""v6/runtime/scheduler.py — 任务调度器。

职责：任务队列、并发控制、取消。
设计来源：docs/v6/SPEC.md 第 4 节。
"""
from __future__ import annotations

import queue
import threading
import time
import traceback
import uuid
from typing import Callable

from v6.runtime.task import Task


class Scheduler:
    """任务调度器：维护队列、限制并发、支持取消。"""

    def __init__(
        self,
        concurrency: int = 1,
        executor: Callable[[Task], None] | None = None,
    ) -> None:
        self._concurrency = max(1, concurrency)
        self._executor = executor or self._default_executor
        self._task_queue: queue.Queue[Task | None] = queue.Queue()
        self._workers: list[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._pending: dict[str, Task] = {}
        self._cancelled: set[str] = set()
        self._running_tasks: set[str] = set()
        self._idle = threading.Condition(self._lock)

    @property
    def running(self) -> bool:
        return self._running

    def submit(self, task: Task) -> str:
        """提交任务到队列，返回 task_id。"""
        if not task.task_id:
            task.task_id = uuid.uuid4().hex
        with self._lock:
            self._pending[task.task_id] = task
        if self._running:
            self._task_queue.put(task)
        return task.task_id

    def cancel(self, task_id: str) -> bool:
        """取消尚未执行的任务。"""
        with self._lock:
            if task_id in self._cancelled:
                return False
            if task_id not in self._pending:
                return False
            self._cancelled.add(task_id)
            return True

    def running_count(self) -> int:
        """当前正在执行的任务数。"""
        with self._lock:
            return len(self._running_tasks)

    def wait_all(self, timeout: float | None = None) -> bool:
        """等待所有任务执行完成。"""
        with self._idle:
            deadline = time.time() + timeout if timeout is not None else None
            while self._running_tasks:
                if timeout is not None:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        return False
                    self._idle.wait(remaining)
                else:
                    self._idle.wait()
            return True

    def start(self) -> None:
        """启动工作线程。"""
        if self._running:
            return
        self._running = True
        self._workers = []
        for _ in range(self._concurrency):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        """停止工作线程并清空待处理任务。"""
        if not self._running:
            return
        self._running = False
        for _ in self._workers:
            self._task_queue.put(None)
        for worker in self._workers:
            worker.join(timeout=2.0)
        self._workers = []
        with self._lock:
            self._pending.clear()
            self._cancelled.clear()

    def _worker_loop(self) -> None:
        """工作线程循环：取任务并执行。"""
        while self._running:
            task = self._task_queue.get()
            if task is None:
                break
            task_id = task.task_id
            with self._lock:
                is_cancelled = task_id in self._cancelled
                if not is_cancelled:
                    self._running_tasks.add(task_id)
            if is_cancelled:
                with self._lock:
                    self._pending.pop(task_id, None)
                    self._cancelled.discard(task_id)
                continue
            try:
                self._executor(task)
            except Exception:  # pragma: no cover - defensive
                traceback.print_exc()
            finally:
                with self._idle:
                    self._pending.pop(task_id, None)
                    self._cancelled.discard(task_id)
                    self._running_tasks.discard(task_id)
                    self._idle.notify_all()

    def _default_executor(self, task: Task) -> None:
        """默认执行器占位：未注册处理器时无操作。"""
