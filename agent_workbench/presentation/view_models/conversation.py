"""ConversationViewModel.

Represents a conversation between user and agent in the UI.
Internally backed by SessionRuntime - UI only sees Conversation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ConversationViewModel:
    """A conversation displayed in the LeftPanel conversation list."""

    id: str
    title: str
    agent_id: str = ""
    message_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False
    is_pinned: bool = False
    tags: List[str] = field(default_factory=list)
