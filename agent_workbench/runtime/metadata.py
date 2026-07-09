"""agent_workbench/runtime/metadata.py — Compatibility re-export layer.

DEPRECATED: This module exists only for backward compatibility with modules
that still import `ModuleMetadata`, `PropertyMetadata`, `StatisticMetadata`, or
`ActionMetadata` from `agent_workbench.runtime.metadata`.

New code MUST import from `agent_workbench.metadata` directly. The canonical
Metadata Contract lives in `agent_workbench/metadata/` and is owned by neither
Runtime nor UI.

Dependency direction: Runtime → Metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

# Re-export the new Cross-layer Contract so consumers can migrate gradually.
from agent_workbench.metadata import (  # noqa: F401
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
)


# Legacy dataclasses preserved for existing Runtime module implementations.
# New code should use the classes from agent_workbench.metadata.
@dataclass
class PropertyMetadata:
    """Legacy property metadata. Use MetadataProperty from agent_workbench.metadata."""

    name: str
    label: str
    type: str  # string, number, boolean, select, textarea, json
    value: Any
    options: List[str] = field(default_factory=list)
    editable: bool = True
    description: str = ""


@dataclass
class StatisticMetadata:
    """Legacy statistic metadata. Use MetadataStatistics from agent_workbench.metadata."""

    name: str
    label: str
    value: Any
    format: str = "text"  # text, number, bytes, percent
    description: str = ""


@dataclass
class ActionMetadata:
    """Legacy action metadata. Use MetadataAction from agent_workbench.metadata."""

    name: str
    label: str
    icon: str = ""
    description: str = ""


@dataclass
class ModuleMetadata:
    """Legacy module metadata. Use MetadataDefinition from agent_workbench.metadata."""

    id: str
    type: str  # runtime, session, model, tool, memory, ...
    name: str
    description: str
    icon: str
    properties: List[PropertyMetadata] = field(default_factory=list)
    statistics: List[StatisticMetadata] = field(default_factory=list)
    actions: List[ActionMetadata] = field(default_factory=list)
