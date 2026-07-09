"""Tests for MetadataDefinition → PresentationModel mapping."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ResourceConnection,
    ResourceDefinition,
    ResourceType,
)
from agent_workbench.metadata.adapter import MetadataAdapter as MetadataAdapterProtocol
from agent_workbench.metadata.types import ValueType
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.ui.workbench.metadata_adapter import PresentationMetadataAdapter
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)


@pytest.fixture
def adapter():
    return PresentationMetadataAdapter()


class TestMetadataDefinitionMapping:
    def test_adapt_module_preserves_identity_and_lists(self, adapter):
        definition = MetadataDefinition(
            id="model",
            type="model",
            name="AI Models",
            description="Model management module",
            icon="🤖",
            tags=["core"],
            enabled=True,
        )
        pres = adapter.adapt(definition)

        assert isinstance(pres, ModulePresentation)
        assert pres.id == "model"
        assert pres.type == "model"
        assert pres.name == "AI Models"
        assert pres.description == "Model management module"
        assert pres.icon == "🤖"
        assert pres.tags == ["core"]
        assert pres.enabled is True
        assert pres.properties == []
        assert pres.statistics == []
        assert pres.actions == []
        assert pres.children == []
        assert pres.connection == {}

    def test_adapt_property_full_fields(self, adapter):
        definition = MetadataDefinition(
            id="cfg",
            type="config",
            name="Config",
            properties=[
                MetadataProperty(
                    id="api_key",
                    name="API Key",
                    description="Provider API key",
                    value_type=ValueType.STRING,
                    current_value="sk-secret",
                    default_value="",
                    options=["a", "b"],
                    editable=True,
                    sensitive=True,
                    category="auth",
                ),
            ],
        )
        prop = adapter.adapt(definition).properties[0]

        assert isinstance(prop, PropertyPresentation)
        assert prop.name == "api_key"
        assert prop.label == "API Key"
        assert prop.type == "string"
        assert prop.value == "sk-secret"
        assert prop.default_value == ""
        assert prop.options == ["a", "b"]
        assert prop.editable is True
        assert prop.sensitive is True
        assert prop.category == "auth"
        assert prop.description == "Provider API key"

    def test_adapt_statistic_full_fields(self, adapter):
        definition = MetadataDefinition(
            id="stats",
            type="stats",
            name="Stats",
            statistics=[
                MetadataStatistics(
                    id="tokens",
                    name="Tokens",
                    value=1024,
                    unit="tokens",
                ),
            ],
        )
        stat = adapter.adapt(definition).statistics[0]

        assert isinstance(stat, StatisticPresentation)
        assert stat.name == "tokens"
        assert stat.label == "Tokens"
        assert stat.value == 1024
        assert stat.unit == "tokens"

    def test_adapt_action_full_fields(self, adapter):
        definition = MetadataDefinition(
            id="actions",
            type="actions",
            name="Actions",
            actions=[
                MetadataAction(
                    id="connect",
                    label="Connect",
                    icon="🔗",
                    description="Connect to resource",
                    enabled=False,
                ),
            ],
        )
        action = adapter.adapt(definition).actions[0]

        assert isinstance(action, ActionPresentation)
        assert action.name == "connect"
        assert action.label == "Connect"
        assert action.icon == "🔗"
        assert action.description == "Connect to resource"
        assert action.enabled is False


class TestResourceDefinitionMapping:
    def test_adapt_resource_maps_connection_and_category(self, adapter):
        resource = ResourceDefinition(
            id="python-3.11",
            type=ResourceType.PYTHON_ENV,
            name="Python 3.11",
            description="Local Python environment",
            icon="🐍",
            tags=["env"],
            enabled=True,
            connection=ResourceConnection(
                target="python3.11",
                command="python",
                args=["-m", "venv"],
                env={"PATH": "/usr/bin"},
                working_dir="/home/user",
            ),
            properties=[MetadataProperty(id="path", name="Path")],
            statistics=[MetadataStatistics(id="version", name="Version", value="3.11")],
            actions=[MetadataAction(id="activate", label="Activate")],
        )
        pres = adapter.adapt_resource(resource)

        assert isinstance(pres, ModulePresentation)
        assert pres.id == "python-3.11"
        assert pres.type == "python_env"
        assert pres.name == "Python 3.11"
        assert pres.category == "resource"
        assert pres.tags == ["env"]
        assert pres.connection == {
            "target": "python3.11",
            "command": "python",
            "args": ["-m", "venv"],
            "env": {"PATH": "/usr/bin"},
            "working_dir": "/home/user",
        }
        assert len(pres.properties) == 1
        assert len(pres.statistics) == 1
        assert len(pres.actions) == 1


class TestLegacyMetadataMapping:
    def test_adapt_legacy_module(self, adapter):
        legacy = ModuleMetadata(
            id="legacy",
            type="legacy",
            name="Legacy Module",
            description="legacy desc",
            icon="📦",
            properties=[PropertyMetadata(name="key", label="Key", type="string", value="v")],
            statistics=[StatisticMetadata(name="s", label="S", value=1)],
            actions=[ActionMetadata(name="a", label="A")],
        )
        pres = adapter.adapt(legacy)

        assert pres.id == "legacy"
        assert pres.properties[0].name == "key"
        assert pres.statistics[0].value == 1
        assert pres.actions[0].label == "A"


class TestProtocolCompliance:
    def test_adapter_satisfies_metadata_adapter_protocol(self, adapter):
        assert isinstance(adapter, MetadataAdapterProtocol)
