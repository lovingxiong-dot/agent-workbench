"""MemoryAdapter - converts Runtime Memory objects to MemoryViewModel.

Supports multiple memory types (short_term, conversation, long_term, knowledge).
Uses getattr() as transitional pattern until Runtime types are stable.
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.memory import MemoryViewModel


class MemoryAdapter:
    """Converts Runtime Memory objects to MemoryViewModel for UI consumption."""

    def to_view_model(self, memory: object) -> MemoryViewModel:
        """Convert a Runtime Memory object to MemoryViewModel."""
        return MemoryViewModel(
            id=getattr(memory, "id", getattr(memory, "key", "")),
            content=getattr(memory, "content", getattr(memory, "value", "")),
            memory_type=getattr(memory, "memory_type", getattr(memory, "type", "short_term")),
            source=getattr(memory, "source", ""),
            importance=float(getattr(memory, "importance", 0.0)),
            created_at=getattr(memory, "created_at", None),
            updated_at=getattr(memory, "updated_at", None),
            tags=list(getattr(memory, "tags", [])),
        )

    def to_view_models(self, memories: List[object]) -> List[MemoryViewModel]:
        """Convert a list of Runtime Memory objects to MemoryViewModels."""
        return [self.to_view_model(m) for m in memories]
