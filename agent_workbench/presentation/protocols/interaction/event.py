"""presentation/protocols/interaction/event.py — InteractionEvent 协议。

InteractionEvent 是 Runtime → UI 的标准化事件协议。
它屏蔽了内部 RuntimeEventType 的细节，使 UI 不会被 Runtime 事件命名绑定。

Phase 2-C.1：从 runtime/interaction/event.py 迁移至 protocols/interaction/event.py。
原路径保留为 re-export 别名（向后兼容）。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InteractionEventType(str, Enum):
    """UI 层事件类型。"""

    MESSAGE_USER = "message.user"
    MESSAGE_DELTA = "message.delta"
    MESSAGE_COMPLETE = "message.complete"
    STATUS_UPDATE = "status.update"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TASK_STARTED = "task.started"
    TASK_FINISHED = "task.finished"
    CAPABILITY_STEP = "capability.step"
    ERROR = "error"


@dataclass
class InteractionEvent:
    """UI 层事件对象。

    字段：
    - type: 事件类型。
    - request_id: 产生该事件的 RuntimeRequest 标识。
    - source: 请求来源（如 "chat_box", "command_bar", "mcp"），用于区分多入口。
    - task_id: 关联的 Task 标识；CHAT 等无 Task 场景为 None。
    - payload: 事件载荷。
    - timestamp: 事件发生时间戳。
    """

    type: InteractionEventType
    request_id: str
    source: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}