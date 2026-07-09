"""Tests for the redesigned Workbench Navigator."""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.navigator import Navigator


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestNavigatorFunctionalTabs:
    def test_functional_tabs_registered_and_selection_emits_id(self, qt_app):
        nav = Navigator()
        nav.register_functional_tab("chat", "Chat", "💬")
        nav.register_functional_tab("skill", "Skills", "🛠")
        nav.register_functional_tab("tool", "Tools", "🔧")

        assert nav._functional_list.count() == 3

        captured: list[str] = []
        nav.selection_changed.connect(captured.append)

        nav.set_selection("skill")
        QApplication.processEvents()

        assert captured == ["skill"]


class TestNavigatorSettings:
    def test_settings_categories_registered(self, qt_app):
        nav = Navigator()
        categories = [
            ("provider", "Provider", "🏭"),
            ("llm", "LLM", "🧠"),
            ("mcp", "MCP", "🔌"),
            ("workflow", "Workflow", "🔄"),
            ("prompt", "Prompt", "📝"),
            ("memory", "Memory", "🧠"),
            ("knowledge", "Knowledge", "📚"),
        ]
        for cid, title, icon in categories:
            nav.register_settings_category(cid, title, icon)

        assert nav._settings_list.count() == len(categories)

    def test_settings_expand_and_collapse(self, qt_app):
        nav = Navigator()
        nav.register_settings_category("provider", "Provider", "🏭")

        assert not nav._settings_list.isHidden()
        assert nav._settings_header.text() == "▼ Settings"

        nav.set_settings_expanded(False)
        assert nav._settings_list.isHidden()
        assert nav._settings_header.text() == "▶ Settings"

        nav.set_settings_expanded(True)
        assert not nav._settings_list.isHidden()
        assert nav._settings_header.text() == "▼ Settings"

    def test_settings_category_selection_emits_id(self, qt_app):
        nav = Navigator()
        nav.register_settings_category("provider", "Provider", "🏭")

        captured: list[str] = []
        nav.selection_changed.connect(captured.append)

        nav.set_selection("provider")
        QApplication.processEvents()

        assert captured == ["provider"]

    def test_add_requested_emits_category_id(self, qt_app):
        nav = Navigator()
        nav.register_settings_category("mcp", "MCP", "🔌")

        captured: list[str] = []
        nav.add_requested.connect(captured.append)

        widget = nav._settings_widgets["mcp"]
        widget._add_btn.click()
        QApplication.processEvents()

        assert captured == ["mcp"]
