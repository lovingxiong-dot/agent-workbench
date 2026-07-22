"""MemoryViewModel.

Memory is not a key-value store. It supports multiple memory types
(short-term, long-term, knowledge) and future backends (vector, graph, document).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class MemoryViewModel:
    """A memory item displayed in the RightPanel context/memory panel.

    Memory types: short_term, conversation, long_term, knowledge.
    Future backends: embedding vector, graph node, document chunk.
    """

    id: str
    content: str
    memory_type: str = "short_term"
    source: str = ""
    importance: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
