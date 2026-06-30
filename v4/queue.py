"""queue.py — v4 会话级双槽位队列管理器"""
from dataclasses import dataclass, field
from typing import Optional, List
from PySide6.QtCore import QObject, Signal
import threading
import time
import uuid


@dataclass
class QueuedTask:
    task_id: str
    user_text: str
    mode: str
    context: str
    session_id: str = ""
    cancelled: threading.Event = field(default_factory=threading.Event)
    created_at: float = field(default_factory=time.time)


class QueueManager(QObject):
    """会话级双槽位队列"""

    MAX_SLOTS = 2

    state_changed = Signal(str)
    send_enabled_changed = Signal(bool)
    queue_bar_text_changed = Signal(str)
    task_ready = Signal(object)
    task_complete = Signal(str)

    def __init__(self, session_id: str, parent=None):
        super().__init__(parent)
        self._session_id = session_id
        self._slots = [None, None]
        self._lock = threading.RLock()

    def enqueue(self, user_text: str, mode: str, context: str) -> Optional[QueuedTask]:
        with self._lock:
            for i in range(self.MAX_SLOTS):
                if self._slots[i] is None:
                    task = QueuedTask(
                        task_id=f"task_{uuid.uuid4().hex[:8]}",
                        user_text=user_text,
                        mode=mode,
                        context=context,
                        session_id=self._session_id,
                    )
                    self._slots[i] = task
                    if i == 0:
                        self.task_ready.emit(task)
                    self._emit_state()
                    return task
            return None

    def mark_done(self, task_id: str) -> Optional[QueuedTask]:
        with self._lock:
            if self._slots[0] and self._slots[0].task_id == task_id:
                self._slots[0] = None
                self.task_complete.emit(task_id)
                self._compact()
                self._emit_state()
                if self._slots[0] is not None:
                    self.task_ready.emit(self._slots[0])
                return self._slots[0]
            return None

    def cancel_current(self):
        with self._lock:
            if self._slots[0]:
                self._slots[0].cancelled.set()
                self._slots[0] = None
                self._compact()
                self._emit_state()

    def _compact(self):
        if self._slots[0] is None and self._slots[1] is not None:
            self._slots[0] = self._slots[1]
            self._slots[1] = None

    def _emit_state(self):
        if self.is_empty:
            name = "idle"
        elif self.has_streaming and not self.has_pending:
            name = "streaming"
        else:
            name = "queued_1"
        self.state_changed.emit(name)
        self.send_enabled_changed.emit(not self.is_full)
        self.queue_bar_text_changed.emit(self._build_bar_text())

    @property
    def is_full(self) -> bool:
        with self._lock:
            return all(s is not None for s in self._slots)

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return all(s is None for s in self._slots)

    @property
    def has_streaming(self) -> bool:
        with self._lock:
            return self._slots[0] is not None

    @property
    def has_pending(self) -> bool:
        with self._lock:
            return self._slots[1] is not None

    def get_streaming_task(self) -> Optional[QueuedTask]:
        with self._lock:
            return self._slots[0]

    def _build_bar_text(self) -> str:
        parts = []
        if self._slots[0]:
            p = self._slots[0].user_text[:40]
            parts.append(f"🔄 处理中: {p}...")
        if self._slots[1]:
            p = self._slots[1].user_text[:40]
            parts.append(f"📋 排队中: {p}...")
        return "  |  ".join(parts)
