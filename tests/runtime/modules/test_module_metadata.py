"""Tests for Runtime Module metadata migration to MetadataDefinition."""
from __future__ import annotations

import pytest

from agent_workbench.metadata import (
    MetadataDefinition,
    ResourceConnection,
    ResourceDefinition,
    ResourceType,
    ValueType,
)
from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.mcp_module import McpModule
from agent_workbench.runtime.modules.memory_module import MemoryModule
from agent_workbench.runtime.modules.model_module import ModelModule
from agent_workbench.runtime.modules.prompt_module import PromptModule
from agent_workbench.runtime.modules.skill_module import SkillModule
from agent_workbench.runtime.modules.workflow_module import WorkflowModule


def _empty_store(tmp_path) -> ConfigStore:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    return ConfigStore(config_path=str(path))


class TestModelModuleMetadata:
    def test_returns_metadata_definition(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("model.providers", [{"name": "echo", "type": "echo", "enabled": True}])
        store.set("model.default_provider", "echo")
        module = ModelModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "model"
        assert meta.type == "model"

        prop_ids = {p.id for p in meta.properties}
        assert "default_provider" in prop_ids
        assert "sampling.temperature" in prop_ids
        assert "sampling.max_tokens" in prop_ids

        default_provider = next(p for p in meta.properties if p.id == "default_provider")
        assert default_provider.value_type == ValueType.ENUM
        assert default_provider.current_value == "echo"

        temperature = next(p for p in meta.properties if p.id == "sampling.temperature")
        assert temperature.value_type == ValueType.FLOAT

        max_tokens = next(p for p in meta.properties if p.id == "sampling.max_tokens")
        assert max_tokens.value_type == ValueType.INT

        stat_ids = {s.id for s in meta.statistics}
        assert "providers" in stat_ids
        assert "active_provider" in stat_ids

        action_ids = {a.id for a in meta.actions}
        assert "validate" in action_ids


class TestMcpModuleMetadata:
    def test_returns_metadata_definition(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("mcp.servers", [{"name": "fs", "command": "npx", "enabled": True}])
        module = McpModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "mcp"
        assert meta.type == "mcp"

        servers = next(p for p in meta.properties if p.id == "servers")
        assert servers.value_type == ValueType.LIST
        assert len(servers.current_value) == 1

        total = next(s for s in meta.statistics if s.id == "total")
        assert total.value == 1


class TestSkillModuleMetadata:
    def test_returns_metadata_definition(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("skill.registry", [{"name": "hello", "type": "python", "enabled": True}])
        module = SkillModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "skill"
        assert meta.type == "skill"

        registry = next(p for p in meta.properties if p.id == "registry")
        assert registry.value_type == ValueType.LIST
        assert len(registry.current_value) == 1

        enabled = next(s for s in meta.statistics if s.id == "enabled")
        assert enabled.value == 1


class TestPromptModuleMetadata:
    def test_returns_metadata_definition(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("prompt.templates", [{"name": "coder", "template": "You are a coder.", "enabled": True}])
        module = PromptModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "prompt"
        assert meta.type == "prompt"

        renderer = next(p for p in meta.properties if p.id == "renderer")
        assert renderer.value_type == ValueType.ENUM
        assert renderer.current_value == "python"

        templates_count = next(s for s in meta.statistics if s.id == "templates_count")
        assert templates_count.value == 1


class TestMemoryModuleMetadata:
    def test_returns_metadata_definition_when_disabled(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("memory.enabled", False)
        store.set("memory.configs", [{"name": "default", "provider": "sqlite", "path": "memory.db", "enabled": True}])
        module = MemoryModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "memory"
        assert meta.type == "memory"

        enabled = next(p for p in meta.properties if p.id == "enabled")
        assert enabled.value_type == ValueType.BOOL
        assert enabled.current_value is False

        provider = next(p for p in meta.properties if p.id == "provider")
        assert provider.value_type == ValueType.ENUM
        assert provider.current_value == "sqlite"

        status = next(s for s in meta.statistics if s.id == "status")
        assert status.value == "inactive"


class TestWorkflowModuleMetadata:
    def test_returns_metadata_definition(self, tmp_path):
        store = _empty_store(tmp_path)
        store.set("workflow.templates", [{"name": "report", "steps": ["fetch"], "enabled": True}])
        module = WorkflowModule()
        module.apply_config(store)

        meta = module.metadata()
        assert isinstance(meta, MetadataDefinition)
        assert meta.id == "workflow"
        assert meta.type == "workflow"

        templates = next(p for p in meta.properties if p.id == "templates")
        assert templates.value_type == ValueType.LIST
        assert len(templates.current_value) == 1

        total = next(s for s in meta.statistics if s.id == "total")
        assert total.value == 1


class TestResourceMetadata:
    def test_resource_definition_creation(self):
        res = ResourceDefinition(
            id="local-python",
            type=ResourceType.PYTHON_ENV,
            name="Local Python",
            description="系统默认 Python 环境。",
            connection=ResourceConnection(
                target="python",
                command="python",
                args=["--version"],
                working_dir=".",
            ),
        )
        assert res.id == "local-python"
        assert res.type == ResourceType.PYTHON_ENV
        assert res.connection.command == "python"

    def test_resource_type_values(self):
        assert ResourceType.SYSTEM == "system"
        assert ResourceType.IDE == "ide"
        assert ResourceType.AGENT_CLI == "agent_cli"
