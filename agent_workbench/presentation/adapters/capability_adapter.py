"""CapabilityAdapter - converts Runtime Capability/Tool objects to ViewModels.

Uses getattr() as transitional pattern until Runtime types are stable.
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.capability import (
    CapabilityViewModel,
    ToolViewModel,
)


class CapabilityAdapter:
    """Converts Runtime Capability/Tool objects to ViewModels for UI consumption."""

    def capability_to_view_model(self, cap: object) -> CapabilityViewModel:
        """Convert a Runtime Capability object to CapabilityViewModel."""
        return CapabilityViewModel(
            id=getattr(cap, "id", ""),
            name=getattr(cap, "name", ""),
            description=getattr(cap, "description", ""),
            category=getattr(cap, "category", ""),
            icon=getattr(cap, "icon", ""),
            input_schema=getattr(cap, "input_schema", {}),
            output_schema=getattr(cap, "output_schema", {}),
            provider=getattr(cap, "provider", ""),
            status=getattr(cap, "status", "unavailable"),
            is_enabled=getattr(cap, "is_enabled", getattr(cap, "enabled", False)),
        )

    def tool_to_view_model(self, tool: object) -> ToolViewModel:
        """Convert a Runtime Tool object to ToolViewModel."""
        return ToolViewModel(
            id=getattr(tool, "id", getattr(tool, "name", "")),
            name=getattr(tool, "name", ""),
            tool_type=getattr(tool, "tool_type", getattr(tool, "type", "")),
            description=getattr(tool, "description", ""),
            status=getattr(tool, "status", "available"),
            icon=getattr(tool, "icon", ""),
        )

    def capabilities_to_view_models(self, caps: List[object]) -> List[CapabilityViewModel]:
        """Convert a list of Runtime Capability objects to CapabilityViewModels."""
        return [self.capability_to_view_model(c) for c in caps]

    def tools_to_view_models(self, tools: List[object]) -> List[ToolViewModel]:
        """Convert a list of Runtime Tool objects to ToolViewModels."""
        return [self.tool_to_view_model(t) for t in tools]
