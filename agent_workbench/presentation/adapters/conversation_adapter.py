"""ConversationAdapter - converts Runtime Session objects to ConversationViewModel.

Internally backed by SessionRuntime, but UI only sees Conversation.
Uses getattr() as transitional pattern until Runtime types are stable.
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.conversation import ConversationViewModel


class ConversationAdapter:
    """Converts Runtime Session objects to ConversationViewModel for UI consumption."""

    def to_view_model(self, session: object) -> ConversationViewModel:
        """Convert a Runtime Session object to ConversationViewModel."""
        return ConversationViewModel(
            id=getattr(session, "id", getattr(session, "session_id", "")),
            title=getattr(session, "title", getattr(session, "name", "")),
            agent_id=getattr(session, "agent_id", ""),
            message_count=getattr(session, "message_count", 0),
            created_at=getattr(session, "created_at", None),
            updated_at=getattr(session, "updated_at", None),
            is_active=getattr(session, "is_active", False),
            is_pinned=getattr(session, "is_pinned", False),
            tags=list(getattr(session, "tags", [])),
        )

    def to_view_models(self, sessions: List[object]) -> List[ConversationViewModel]:
        """Convert a list of Runtime Session objects to ConversationViewModels."""
        return [self.to_view_model(s) for s in sessions]
