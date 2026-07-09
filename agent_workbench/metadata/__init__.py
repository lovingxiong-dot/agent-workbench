"""agent_workbench/metadata — Cross-layer Metadata Contract.

This package owns the platform-agnostic description language used by Runtime,
Workbench, CLI, Web, Plugin, and Marketplace. It must never depend on Runtime,
UI, or any specific consumer.

Dependency direction is strictly one-way:

    Runtime → Metadata
    Workbench → Metadata
    Plugin → Metadata
    CLI → Metadata
    Web → Metadata

Nothing inside this package may import from `agent_workbench.runtime.*` or
`agent_workbench.ui.*`.
"""
from agent_workbench.metadata.model import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
)
from agent_workbench.metadata.resource import (
    ResourceConnection,
    ResourceDefinition,
    ResourceType,
)
from agent_workbench.metadata.types import MetadataType, ValueType

__all__ = [
    "MetadataDefinition",
    "MetadataProperty",
    "MetadataAction",
    "MetadataStatistics",
    "ValueType",
    "MetadataType",
    "ResourceDefinition",
    "ResourceConnection",
    "ResourceType",
]
