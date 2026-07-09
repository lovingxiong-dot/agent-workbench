"""Tests for ViewComponentRegistry and ViewSchemaRenderer component dispatch."""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.view_component import ViewComponentDefinition
from agent_workbench.ui.workbench.view_component_registry import ViewComponentRegistry
from agent_workbench.ui.workbench.view_schema import ViewSchema
from agent_workbench.ui.workbench.presentation import ModulePresentation


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestViewComponentRegistry:
    def test_register_and_resolve(self) -> None:
        registry = ViewComponentRegistry()
        definition = ViewComponentDefinition(
            id="status_bar",
            renderer="status_bar",
            supported_schema=["status_schema"],
            supported_binding=["runtime"],
            default_size={"width": 800, "height": 32},
        )
        registry.register(definition)
        assert registry.resolve("status_bar") is definition

    def test_resolve_missing_returns_none(self) -> None:
        registry = ViewComponentRegistry()
        assert registry.resolve("missing") is None

    def test_unregister(self) -> None:
        registry = ViewComponentRegistry()
        registry.register(ViewComponentDefinition(id="toolbar", renderer="toolbar"))
        registry.unregister("toolbar")
        assert registry.resolve("toolbar") is None

    def test_list_returns_all_registered(self) -> None:
        registry = ViewComponentRegistry()
        a = ViewComponentDefinition(id="a", renderer="a")
        b = ViewComponentDefinition(id="b", renderer="b")
        registry.register(a)
        registry.register(b)
        items = registry.list()
        assert len(items) == 2
        assert a in items
        assert b in items


class TestViewSchemaRendererComponentDispatch:
    def _make_fake_ui(self):
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

    def test_render_component_dispatches_status_bar(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer
        from agent_workbench.ui.workbench.view_schema import StatusItemSchema, StatusSchema, WorkspaceSchema

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(
            schema_id="test",
            name="Test",
            workspace=WorkspaceSchema(
                status=StatusSchema(items=[StatusItemSchema(name="hits", source="statistics")])
            ),
        )
        pres = ModulePresentation(
            id="test",
            type="test",
            name="Test",
        )
        renderer.render_component("status_bar", schema, pres)
        # Schema declares one item, no matching statistic, so statistics list is empty
        assert ui.status_bar.statistics == []

    def test_render_component_unknown_id_is_noop(self, qt_app):
        from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer

        ui = self._make_fake_ui()
        renderer = ViewSchemaRenderer(ui)
        schema = ViewSchema(schema_id="test", name="Test")
        pres = ModulePresentation(id="test", type="test", name="Test")
        # Should not raise
        renderer.render_component("unknown", schema, pres)
