"""Tests for StatusBar / ToolBar / Workspace consuming ModulePresentation."""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.generic_workspace import GenericWorkspaceItem
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.status_bar import StatusBar
from agent_workbench.ui.workbench.tool_bar import ToolBar
from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestStatusBarStatistics:
    def test_empty_statistics_clears_items(self, qt_app):
        bar = StatusBar()
        bar.set_statistics([])
        assert bar.values() == {}

    def test_single_statistic_renders_text(self, qt_app):
        bar = StatusBar()
        bar.set_statistics([
            StatisticPresentation(name="tokens", label="Tokens", value=1024),
        ])
        assert bar.values() == {"tokens": "Tokens: 1024"}

    def test_multiple_presentations_aggregate_statistics(self, qt_app):
        bar = StatusBar()
        presentations = [
            ModulePresentation(
                id="model",
                type="model",
                name="AI Models",
                statistics=[
                    StatisticPresentation(name="provider", label="Provider", value="openai"),
                    StatisticPresentation(name="model", label="Model", value="gpt-4o"),
                ],
            ),
            ModulePresentation(
                id="memory",
                type="memory",
                name="Memory",
                statistics=[
                    StatisticPresentation(name="records", label="Records", value=42),
                ],
            ),
        ]
        statistics = [stat for pres in presentations for stat in pres.statistics]
        bar.set_statistics(statistics)

        assert bar.values()["provider"] == "Provider: openai"
        assert bar.values()["model"] == "Model: gpt-4o"
        assert bar.values()["records"] == "Records: 42"

    def test_statistic_formats(self, qt_app):
        bar = StatusBar()
        bar.set_statistics([
            StatisticPresentation(name="bytes", label="Bytes", value=1536, format="bytes"),
            StatisticPresentation(name="pct", label="Progress", value=75, format="percent"),
            StatisticPresentation(name="dur", label="Latency", value=1.25, format="duration", unit="s"),
        ])
        values = bar.values()
        assert "KB" in values["bytes"]
        assert values["pct"] == "Progress: 75%"
        assert values["dur"] == "Latency: 1.2s"


class TestToolBarActions:
    def test_empty_actions_clears_buttons(self, qt_app):
        tb = ToolBar()
        tb.set_actions([])
        assert tb.actions_state() == {}

    def test_actions_create_buttons_with_enabled_state(self, qt_app):
        tb = ToolBar()
        tb.set_actions([
            ActionPresentation(name="save", label="Save", enabled=True),
            ActionPresentation(name="delete", label="Delete", enabled=False, danger=True),
        ])
        state = tb.actions_state()
        assert state == {"save": True, "delete": False}

    def test_button_click_emits_action_name(self, qt_app):
        tb = ToolBar()
        captured: list[str] = []
        tb.action_triggered.connect(captured.append)
        tb.set_actions([
            ActionPresentation(name="run", label="Run", enabled=True),
        ])
        btn = tb.findChild(QPushButton)
        assert btn is not None
        btn.click()
        assert captured == ["run"]

    def test_actions_sorted_by_order(self, qt_app):
        tb = ToolBar()
        tb.set_actions([
            ActionPresentation(name="b", label="B", order=2),
            ActionPresentation(name="a", label="A", order=1),
        ])
        buttons = tb.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert texts == ["A", "B"]


class TestWorkspaceResolve:
    def test_chat_workspace_from_presentation(self, qt_app):
        pres = ModulePresentation(id="chat", type="workspace", name="Chat")
        assert WorkbenchUIController._resolve_workspace_id(pres) == "chat"

    def test_trace_workspace_from_presentation(self, qt_app):
        pres = ModulePresentation(id="trace-1", type="trace", name="Trace")
        assert WorkbenchUIController._resolve_workspace_id(pres) == "trace"

    def test_settings_falls_back_to_generic(self, qt_app):
        pres = ModulePresentation(id="model", type="settings", name="AI Models")
        assert WorkbenchUIController._resolve_workspace_id(pres) == "generic"

    def test_unknown_type_falls_back_to_generic(self, qt_app):
        pres = ModulePresentation(id="x", type="unknown", name="X")
        assert WorkbenchUIController._resolve_workspace_id(pres) == "generic"


class TestGenericWorkspace:
    def test_set_module_updates_labels(self, qt_app):
        ws = GenericWorkspaceItem()
        ws.set_module("Memory", "Long-term memory module")
        # 通过 findChildren 定位 QLabel
        labels = ws.findChildren(QLabel)
        texts = [l.text() for l in labels]
        assert "Memory" in texts
        assert "Long-term memory module" in texts
