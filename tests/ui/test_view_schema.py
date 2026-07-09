"""Tests for ViewSchema layer (schema / registry / renderer)."""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.view_schema import (
    BindingSource,
    InspectorSchema,
    InspectorTabSchema,
    StatusItemSchema,
    StatusSchema,
    ToolbarGroupSchema,
    ToolbarSchema,
    ViewSchema,
    WorkspaceSchema,
)
from agent_workbench.ui.workbench.view_schema_registry import ViewSchemaRegistry


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestViewSchemaRegistry:
    def test_default_schemas_registered(self, qt_app):
        registry = ViewSchemaRegistry()
        for schema_id in (
            "chat_workspace",
            "settings_workspace",
            "trace_workspace",
            "config_workspace",
            "skill_workspace",
            "tool_workspace",
            "generic_workspace",
        ):
            assert registry.get(schema_id) is not None

    def test_resolve_by_explicit_view_schema_id(self, qt_app):
        registry = ViewSchemaRegistry()
        pres = ModulePresentation(id="x", type="unknown", name="X", view_schema_id="trace_workspace")
        schema = registry.resolve(pres)
        assert schema.schema_id == "trace_workspace"

    def test_resolve_settings_type(self, qt_app):
        registry = ViewSchemaRegistry()
        pres = ModulePresentation(id="model", type="settings", name="AI Models")
        schema = registry.resolve(pres)
        assert schema.schema_id == "settings_workspace"

    def test_resolve_chat_workspace(self, qt_app):
        registry = ViewSchemaRegistry()
        pres = ModulePresentation(id="chat", type="workspace", name="Chat")
        schema = registry.resolve(pres)
        assert schema.schema_id == "chat_workspace"

    def test_resolve_model_config(self, qt_app):
        registry = ViewSchemaRegistry()
        pres = ModulePresentation(id="model", type="model", name="AI Models")
        schema = registry.resolve(pres)
        assert schema.schema_id == "config_workspace"

    def test_resolve_fallback_to_generic(self, qt_app):
        registry = ViewSchemaRegistry()
        pres = ModulePresentation(id="unknown", type="unknown", name="Unknown")
        schema = registry.resolve(pres)
        assert schema.schema_id == "generic_workspace"


class TestViewSchemaRenderer:
    def _make_fake_ui(self):
        """返回一个轻量 fake Workbench UI，用于非 GUI 测试 Renderer。"""
        class FakeBar:
            def __init__(self):
                self.actions = []
                self.statistics = []

            def set_actions(self, actions):
                self.actions = actions

            def set_statistics(self, statistics):
                self.statistics = statistics

        class FakeInspector:
            def __init__(self):
                self.schema = None
                self.presentation = None

            def set_schema(self, schema):
                self.schema = schema

            def set_object(self, presentation):
                self.presentation = presentation

        class FakeWorkspace:
            def __init__(self):
                self.workspace_id = None

            def switch_to(self, workspace_id):
                self.workspace_id = workspace_id

        class FakeWorkbenchUI:
            def __init__(self):
                self.tool_bar = FakeBar()
                self.status_bar = FakeBar()
                self.inspector = FakeInspector()
                self.workspace = FakeWorkspace()

        return FakeWorkbenchUI()

    def test_renderer_orders_toolbar_actions(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(
            schema_id="test",
            name="Test",
            workspace=WorkspaceSchema(
                toolbar=ToolbarSchema(items=["b", "a"]),
            ),
        )
        pres = ModulePresentation(
            id="test",
            type="test",
            name="Test",
            actions=[
                ActionPresentation(name="a", label="A"),
                ActionPresentation(name="b", label="B"),
                ActionPresentation(name="c", label="C"),
            ],
        )
        renderer.render(schema, pres)
        names = [a.name for a in ui.tool_bar.actions]
        assert names == ["b", "a", "c"]

    def test_renderer_groups_toolbar_actions(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(
            schema_id="test",
            name="Test",
            workspace=WorkspaceSchema(
                toolbar=ToolbarSchema(
                    items=[
                        ToolbarGroupSchema(name="primary", items=["save", "run"]),
                    ]
                ),
            ),
        )
        pres = ModulePresentation(
            id="test",
            type="test",
            name="Test",
            actions=[
                ActionPresentation(name="run", label="Run"),
                ActionPresentation(name="save", label="Save"),
            ],
        )
        renderer.render(schema, pres)
        names = [a.name for a in ui.tool_bar.actions]
        assert names == ["save", "run"]

    def test_renderer_status_bar_selects_by_schema(self, qt_app):
        from agent_workbench.ui.workbench.binding_context import BindingContext, BindingProvider
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        runtime_data = {"runtime": "online"}
        binding = BindingContext()
        binding.registry.register(BindingProvider(namespace="runtime", getter=runtime_data.get))
        renderer = ViewSchemaRenderer(ui, binding_context=binding)
        schema = ViewSchema(
            schema_id="test",
            name="Test",
            workspace=WorkspaceSchema(
                status=StatusSchema(
                    items=[
                        StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.runtime")),
                        StatusItemSchema(name="hits", source="statistics"),
                    ]
                )
            ),
        )
        pres = ModulePresentation(
            id="test",
            type="test",
            name="Test",
            statistics=[
                StatisticPresentation(name="hits", label="Hits", value=42),
                StatisticPresentation(name="misses", label="Misses", value=3),
            ],
        )
        renderer.render(schema, pres)
        values = {s.name: s.value for s in ui.status_bar.statistics}
        assert values["runtime"] == "online"
        assert values["hits"] == 42
        assert "misses" in values  # 未在 schema 中声明的追加到末尾

    def test_renderer_sets_inspector_schema(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(
            schema_id="test",
            name="Test",
            workspace=WorkspaceSchema(
                inspector=InspectorSchema(
                    tabs=[
                        InspectorTabSchema(id="props", title="Properties", source="properties"),
                        InspectorTabSchema(id="stats", title="Statistics", source="statistics"),
                    ]
                )
            ),
        )
        pres = ModulePresentation(id="test", type="test", name="Test")
        renderer.render(schema, pres)
        assert ui.inspector.schema is schema.workspace.inspector
        assert ui.inspector.presentation is pres

    def test_renderer_switches_workspace_by_type(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(schema_id="test", name="Test")
        pres = ModulePresentation(id="chat", type="workspace", name="Chat")
        renderer.render(schema, pres)
        assert ui.workspace.workspace_id == "chat"


class TestMetadataAdapterViewSchema:
    def test_adapter_infers_view_schema_for_settings(self, qt_app):
        from agent_workbench.metadata import MetadataDefinition
        from agent_workbench.ui.workbench.metadata_adapter import PresentationMetadataAdapter

        adapter = PresentationMetadataAdapter()
        meta = MetadataDefinition(
            id="model",
            type="settings",
            name="AI Models",
            description="",
        )
        pres = adapter.adapt(meta)
        assert pres.view_schema_id == "settings_workspace"

    def test_adapter_respects_explicit_view_schema_id(self, qt_app):
        from agent_workbench.metadata import MetadataDefinition, MetadataType
        from agent_workbench.ui.workbench.metadata_adapter import PresentationMetadataAdapter

        adapter = PresentationMetadataAdapter()
        meta = MetadataDefinition(
            id="custom",
            type=MetadataType.RUNTIME,
            name="Custom",
            description="",
        )
        meta.view_schema_id = "trace_workspace"
        pres = adapter.adapt(meta)
        assert pres.view_schema_id == "trace_workspace"
