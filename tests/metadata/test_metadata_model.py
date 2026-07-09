"""Tests for agent_workbench.metadata.model."""
from __future__ import annotations

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ValueType,
)


def test_metadata_definition_defaults() -> None:
    definition = MetadataDefinition(
        id="test-module",
        type="model",
        name="Test Module",
    )
    assert definition.id == "test-module"
    assert definition.type == "model"
    assert definition.name == "Test Module"
    assert definition.description == ""
    assert definition.icon == ""
    assert definition.properties == []
    assert definition.statistics == []
    assert definition.actions == []
    assert definition.tags == []
    assert definition.enabled is True


def test_metadata_property_with_value_type() -> None:
    prop = MetadataProperty(
        id="api-key",
        name="API Key",
        value_type=ValueType.SECRET,
        current_value="sk-xxx",
        sensitive=True,
    )
    assert prop.id == "api-key"
    assert prop.name == "API Key"
    assert prop.value_type == ValueType.SECRET
    assert prop.current_value == "sk-xxx"
    assert prop.sensitive is True


def test_metadata_property_string_value_type() -> None:
    prop = MetadataProperty(
        id="endpoint",
        name="Endpoint",
        value_type="string",
    )
    assert prop.value_type == "string"


def test_metadata_action() -> None:
    action = MetadataAction(
        id="connect",
        label="Connect",
        icon="plug",
        enabled=False,
    )
    assert action.id == "connect"
    assert action.label == "Connect"
    assert action.icon == "plug"
    assert action.enabled is False


def test_metadata_statistics() -> None:
    stat = MetadataStatistics(
        id="tokens",
        name="Tokens",
        value=42,
        unit="count",
    )
    assert stat.id == "tokens"
    assert stat.name == "Tokens"
    assert stat.value == 42
    assert stat.unit == "count"
    assert stat.timestamp is None


def test_metadata_definition_full() -> None:
    definition = MetadataDefinition(
        id="openai-provider",
        type="provider",
        name="OpenAI",
        description="OpenAI API provider",
        icon="openai",
        tags=["llm", "cloud"],
        properties=[
            MetadataProperty(
                id="api-key",
                name="API Key",
                value_type=ValueType.SECRET,
                sensitive=True,
            ),
        ],
        statistics=[
            MetadataStatistics(
                id="latency",
                name="Latency",
                value=120,
                unit="ms",
            ),
        ],
        actions=[
            MetadataAction(
                id="validate",
                label="Validate",
            ),
        ],
    )
    assert len(definition.properties) == 1
    assert len(definition.statistics) == 1
    assert len(definition.actions) == 1
    assert definition.properties[0].id == "api-key"
