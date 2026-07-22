"""AgentViewModel + AgentRuntimeViewModel.

Agent identity (who) and runtime configuration (how to run) are separate.
An Agent may have multiple runtime configurations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AgentViewModel:
    """Agent identity - the "who" (digital identity object)."""

    id: str
    name: str
    description: str = ""
    avatar: str = ""
    role: str = ""
    status: str = "idle"
    capability_ids: List[str] = field(default_factory=list)
    is_active: bool = False


@dataclass
class AgentRuntimeViewModel:
    """Agent runtime configuration - the "how to run"."""

    agent_id: str
    provider: str = ""
    model: str = ""
    context_window: int = 128000
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    system_prompt: str = ""
