"""Tests for agent_workbench.metadata.adapter."""
from __future__ import annotations

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
)
from agent_workbench.metadata.adapter import IdentityMetadataAdapter, MetadataAdapter


def test_identity_adapter_returns_same_definition() -> None:
    adapter = IdentityMetadataAdapter()
    definition = MetadataDefinition(
        id="test",
        type="model",
        name="Test",
    )
    assert adapter.adapt(definition) is definition


def test_metadata_adapter_protocol() -> None:
    """MetadataAdapter 是一个 Protocol，实现者只需提供 adapt 方法。"""

    class CustomAdapter:
        def adapt(self, definition: MetadataDefinition) -> str:
            return definition.id

    adapter: MetadataAdapter = CustomAdapter()
    definition = MetadataDefinition(id="x", type="y", name="X")
    assert adapter.adapt(definition) == "x"


def test_identity_adapter_preserves_properties() -> None:
    adapter = IdentityMetadataAdapter()
    definition = MetadataDefinition(
        id="p",
        type="provider",
        name="Provider",
        properties=[
            MetadataProperty(id="key", name="Key"),
        ],
        statistics=[
            MetadataStatistics(id="s", name="Stat", value=1),
        ],
        actions=[
            MetadataAction(id="a", label="Action"),
        ],
    )
    result = adapter.adapt(definition)
    assert result.properties[0].id == "key"
    assert result.statistics[0].value == 1
    assert result.actions[0].label == "Action"
