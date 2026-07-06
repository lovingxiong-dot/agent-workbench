"""v6/runtime/context.py — 单次任务运行时上下文。

设计来源：docs/v6/SPEC.md 第 4、8 节。

核心原则：
- RuntimeContext 是运行时唯一状态对象（Single Source of Truth）。
- Engine 不拥有状态，RuntimeContext 才拥有状态。
- RuntimeContext 是可演进对象，Engine 只访问自身职责需要的字段。
- messages 元素为 ChatMessage，不再使用裸 dict。
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v6.runtime.types import ChatMessage


@dataclass
class RuntimeContext:
    """维护单次任务的上下文状态。

    字段可演进，Engine 不应假设字段集合固定。
    """

    task_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    group_user_id: Optional[str] = None

    # 执行状态
    phase: str = ""
    mode: str = ""
    model: str = ""
    provider: str = ""

    # 项目与记忆
    project_path: str = ""
    memory: Dict[str, Any] = field(default_factory=dict)

    # 消息、工具、指标
    messages: List[ChatMessage] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    # 通用元数据容器，Engine 可读写自己负责的字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self._lock = threading.RLock()

    def add_message(self, role: str, content: str) -> None:
        """追加一条 ChatMessage 到上下文。"""
        with self._lock:
            self.messages.append(ChatMessage(role=role, content=content))

    def set_status(self, status: str) -> None:
        """线程安全地更新任务状态。"""
        with self._lock:
            self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """序列化上下文为字典。"""
        with self._lock:
            return {
                "task_id": self.task_id,
                "session_id": self.session_id,
                "conversation_id": self.conversation_id,
                "group_user_id": self.group_user_id,
                "phase": self.phase,
                "mode": self.mode,
                "model": self.model,
                "provider": self.provider,
                "project_path": self.project_path,
                "memory": dict(self.memory),
                "messages": [m.__dict__ for m in self.messages],
                "tool_calls": list(self.tool_calls),
                "metrics": dict(self.metrics),
                "metadata": dict(self.metadata),
                "status": self.status,
                "created_at": self.created_at,
            }
