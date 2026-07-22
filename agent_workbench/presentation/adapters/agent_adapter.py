"""AgentAdapter - converts Runtime Agent objects to ViewModels.

Separates Agent identity (AgentViewModel) from runtime config (AgentRuntimeViewModel).
Uses getattr() as transitional pattern until Runtime types are stable.
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.agent import (
    AgentRuntimeViewModel,
    AgentViewModel,
)


class AgentAdapter:
    """Converts Runtime Agent objects to AgentViewModel + AgentRuntimeViewModel."""

    def to_view_model(self, agent: object) -> AgentViewModel:
        """Convert Runtime Agent to AgentViewModel (identity only)."""
        return AgentViewModel(
            id=getattr(agent, "id", getattr(agent, "agent_id", "")),
            name=getattr(agent, "name", ""),
            description=getattr(agent, "description", ""),
            avatar=getattr(agent, "avatar", getattr(agent, "icon", "")),
            role=getattr(agent, "role", ""),
            status=getattr(agent, "status", "idle"),
            capability_ids=list(getattr(agent, "capability_ids", [])),
            is_active=getattr(agent, "is_active", False),
        )

    def to_runtime_view_model(self, agent: object) -> AgentRuntimeViewModel:
        """Convert Runtime Agent to AgentRuntimeViewModel (config only)."""
        return AgentRuntimeViewModel(
            agent_id=getattr(agent, "id", getattr(agent, "agent_id", "")),
            provider=getattr(agent, "provider", ""),
            model=getattr(agent, "model", ""),
            context_window=int(getattr(agent, "context_window", 128000)),
            temperature=float(getattr(agent, "temperature", 0.7)),
            max_tokens=int(getattr(agent, "max_tokens", 4096)),
            top_p=float(getattr(agent, "top_p", 0.9)),
            system_prompt=getattr(agent, "system_prompt", ""),
        )

    def to_view_models(self, agents: List[object]) -> List[AgentViewModel]:
        """Convert a list of Runtime Agent objects to AgentViewModels."""
        return [self.to_view_model(a) for a in agents]
