"""Tests for agent_workbench.metadata.registry."""
from __future__ import annotations

import pytest

from agent_workbench.metadata import MetadataDefinition, MetadataType
from agent_workbench.metadata.errors import MetadataNotFoundError
from agent_workbench.metadata.registry import MetadataRegistry


def test_registry_register_and_get() -> None:
    registry = MetadataRegistry()
    definition = MetadataDefinition(
        id="m1",
        type=MetadataType.MODEL.value,
        name="Model Module",
    )
    registry.register(definition)
    assert registry.get("m1") is definition
    assert registry.get("missing") is None


def test_registry_all() -> None:
    registry = MetadataRegistry()
    registry.register(MetadataDefinition(id="a", type="x", name="A"))
    registry.register(MetadataDefinition(id="b", type="x", name="B"))
    assert len(registry.all()) == 2


def test_registry_require_raises() -> None:
    registry = MetadataRegistry()
    with pytest.raises(MetadataNotFoundError):
        registry.require("missing")


def test_registry_overwrite() -> None:
    registry = MetadataRegistry()
    first = MetadataDefinition(id="m1", type="x", name="First")
    second = MetadataDefinition(id="m1", type="x", name="Second")
    registry.register(first)
    registry.register(second)
    assert registry.get("m1") is second


def test_registry_unregister_and_clear() -> None:
    registry = MetadataRegistry()
    registry.register(MetadataDefinition(id="a", type="x", name="A"))
    assert registry.unregister("a") is True
    assert registry.unregister("a") is False
    assert len(registry) == 0


def test_registry_contains() -> None:
    registry = MetadataRegistry()
    registry.register(MetadataDefinition(id="a", type="x", name="A"))
    assert "a" in registry
    assert "b" not in registry
