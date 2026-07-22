"""CapabilityViewModel + ToolViewModel.

Capability is the core unit of agent ability - not a menu item.
A Skill is a composition of Capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CapabilityViewModel:
    """A capability displayed in the LeftPanel function page.

    Capability is a first-class runtime concept: it describes what an agent
    can do, including its input/output contract and provider binding.
    """

    id: str
    name: str
    description: str = ""
    category: str = ""
    icon: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    status: str = "unavailable"
    is_enabled: bool = False


@dataclass
class ToolViewModel:
    """A tool displayed in the UI (RightPanel tool list, ChatArea tool calls)."""

    id: str
    name: str
    tool_type: str = ""
    description: str = ""
    status: str = "available"
    icon: str = ""
