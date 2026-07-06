"""v6/runtime/context.py — 单次任务运行时上下文。

设计来源：docs/v6/SPEC.md 第 4 节。
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeContext:
    """维护单次任务的上下文状态。"""

    task_id: str
    session_id: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self._lock = threading.RLock()

    def add_message(self, role: str, content: str) -> None:
        """追加一条消息到上下文。"""
        with self._lock:
            self.messages.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": time.time(),
                }
            )

    def set_status(self, status: str) -> None:
        """线程安全地更新任务状态。"""
        with self._lock:
            self.status = status

    def to_dict(self) -> dict[str, Any]:
        """序列化上下文为字典。"""
        with self._lock:
            return {
                "task_id": self.task_id,
                "session_id": self.session_id,
                "messages": list(self.messages),
                "tools": list(self.tools),
                "metadata": dict(self.metadata),
                "status": self.status,
                "created_at": self.created_at,
            }
