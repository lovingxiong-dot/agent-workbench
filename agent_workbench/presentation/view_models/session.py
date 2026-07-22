"""SessionViewModel + MessageViewModel — 会话与消息数据契约。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SessionViewModel:
    """会话列表项。"""

    id: str
    title: str
    preview: str = ""
    timestamp: str = ""
    message_count: int = 0
    is_active: bool = False
    group_id: str = ""


@dataclass
class MessageViewModel:
    """单条聊天消息。"""

    id: str
    role: str  # "user" | "assistant" | "tool"
    content: str
    timestamp: str = ""
    tool_calls: List[dict] = field(default_factory=list)