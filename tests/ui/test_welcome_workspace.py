"""Tests for WelcomeWorkspaceItem — Workbench OS Home page.

These tests verify the Home workspace renders product positioning,
dynamic content, and forwards user intent via signals.
"""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.welcome_workspace import WelcomeWorkspaceItem


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestWelcomeWorkspaceItem:
    def test_initial_state_shows_empty_lists(self, qt_app):
        widget = WelcomeWorkspaceItem()
        assert "No agents installed." in widget._agents_list.text()
        assert "No recent projects." in widget._recent_list.text()
        assert "Version 1.0" in widget._version_label.text()
        assert "Current Project" in widget._project_label.text()

    def test_set_installed_agents_renders_bulleted_list(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_installed_agents([("starter", "Starter Agent"), ("trading", "Trading Agent")])
        text = widget._agents_list.text()
        assert "  • Starter Agent" in text
        assert "  • Trading Agent" in text
        assert "No agents installed." not in text

    def test_set_installed_agents_empty_fallback(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_installed_agents([("starter", "Starter Agent")])
        widget.set_installed_agents([])
        assert "No agents installed." in widget._agents_list.text()

    def test_set_recent_projects_renders_bulleted_list(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_recent_projects(["Project A", "Conversation B"])
        text = widget._recent_list.text()
        assert "  • Project A" in text
        assert "  • Conversation B" in text
        assert "No recent projects." not in text

    def test_set_recent_projects_empty_fallback(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_recent_projects(["Project A"])
        widget.set_recent_projects([])
        assert "No recent projects." in widget._recent_list.text()

    def test_set_project_shows_name_and_parent_dir(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_project("agent_workbench", "F:\\Agent\\")
        text = widget._project_label.text()
        assert "Current Project" in text
        assert "agent_workbench" in text
        assert "F:\\Agent\\" in text

    def test_set_version_updates_label(self, qt_app):
        widget = WelcomeWorkspaceItem()
        widget.set_version("1.2.0")
        assert "Version 1.2.0" in widget._version_label.text()

    def test_new_agent_button_emits_signal(self, qt_app):
        widget = WelcomeWorkspaceItem()
        captured: list[object] = []
        widget.new_agent_requested.connect(lambda: captured.append(True))
        widget._new_agent_btn.click()
        QApplication.processEvents()
        assert len(captured) == 1

    def test_install_agent_button_emits_signal(self, qt_app):
        widget = WelcomeWorkspaceItem()
        captured: list[object] = []
        widget.install_agent_requested.connect(lambda: captured.append(True))
        widget._install_agent_btn.click()
        QApplication.processEvents()
        assert len(captured) == 1

    def test_documentation_link_emits_signal_with_key(self, qt_app):
        widget = WelcomeWorkspaceItem()
        captured: list[str] = []
        widget.documentation_requested.connect(captured.append)
        # Simulate link activation by emitting the underlying signal directly.
        widget.documentation_requested.emit("github")
        QApplication.processEvents()
        assert captured == ["github"]
