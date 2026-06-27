"""
TaskQueue — 任务队列 + 优先级调度

维护排队任务的 FIFO 队列，支持按优先级出队。
"""
from collections import deque
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class QueuedTask:
    """排队中的任务"""
    session_id: str
    mode: str
    user_input: str
    priority: int = 0  # 数字越大优先级越高，默认 0


class TaskQueue:
    """FIFO 任务队列，按优先级降序（同优先级按入队时间）"""

    def __init__(self, max_size: int = 5):
        self._queue: deque[QueuedTask] = deque()
        self._max_size = max_size

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def has_capacity(self) -> bool:
        return self.size < self._max_size

    def enqueue(self, session_id: str, mode: str, user_input: str, priority: int = 0) -> Optional[str]:
        """入队。返回 None 表示成功，返回错误信息表示队列满。"""
        if not self.has_capacity:
            return f"任务队列已满 ({self.size}/{self._max_size})，请等待"
        self._queue.append(QueuedTask(session_id, mode, user_input, priority))
        # 按优先级降序排序
        items = sorted(self._queue, key=lambda t: -t.priority)
        self._queue = deque(items)
        return None

    def dequeue(self) -> Optional[QueuedTask]:
        """出队优先级最高的任务"""
        if self._queue:
            return self._queue.popleft()
        return None

    def remove(self, session_id: str) -> bool:
        """从队列中移除指定会话的排队任务"""
        new_q = deque(t for t in self._queue if t.session_id != session_id)
        removed = len(new_q) != len(self._queue)
        self._queue = new_q
        return removed

    def list_ids(self) -> list:
        return [t.session_id for t in self._queue]

    def clear(self):
        self._queue.clear()
