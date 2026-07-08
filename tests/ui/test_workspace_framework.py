"""Tests for the Workbench Workspace Framework.

These tests verify Workspace registry, routing, and lifecycle without
requiring a visible GUI. They use off-screen QApplication fixtures.
"""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication, QWidget

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workspace import Workspace
from agent_workbench.ui.workspace_registry import WorkspaceRegistry
from agent_workbench.ui.workspace_router import WorkspaceRouter
from agent_workbench.ui.workbench.workspace_host import WorkspaceHost
from agent_workbench.ui.workspaces import (
    ChatWorkspace,
    ProviderWorkspace,
    SkillWorkspace,
    ToolWorkspace,
)


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class DummyWorkspace(Workspace):
    workspace_id = "dummy"
    title = "Dummy"
    icon = "🔘"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activated = 0
        self.deactivated = 0
        self.closed = 0

    def on_activate(self):
        self.activated += 1

    def on_deactivate(self):
        self.deactivated += 1

    def on_close(self):
        self.closed += 1


class TestWorkspaceRegistry:
    def test_register_and_list(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(ChatWorkspace)
        registry.register(SkillWorkspace)
        ids = [cls.workspace_id for cls in registry.list()]
        assert ids == ["chat", "skill"]

    def test_register_requires_workspace_subclass(self, qt_app):
        registry = WorkspaceRegistry()
        with pytest.raises(TypeError):
            registry.register(QWidget)

    def test_register_requires_workspace_id(self, qt_app):
        class BadWorkspace(Workspace):
            pass

        registry = WorkspaceRegistry()
        with pytest.raises(ValueError):
            registry.register(BadWorkspace)

    def test_duplicate_registration_fails(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(ChatWorkspace)
        with pytest.raises(ValueError):
            registry.register(ChatWorkspace)

    def test_get_and_contains(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(ToolWorkspace)
        assert "tool" in registry
        assert registry.get("tool") is ToolWorkspace
        assert registry.get("missing") is None


class TestWorkspaceRouter:
    def test_switch_to_creates_and_activates(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(DummyWorkspace)
        host = WorkspaceHost()
        router = WorkspaceRouter(registry, host)

        ws = router.switch_to("dummy")
        assert ws is not None
        assert isinstance(ws, DummyWorkspace)
        assert ws.activated == 1
        assert router.current_id == "dummy"
        assert router.current_workspace is ws

    def test_switch_to_same_does_nothing(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(DummyWorkspace)
        host = WorkspaceHost()
        router = WorkspaceRouter(registry, host)

        ws1 = router.switch_to("dummy")
        ws2 = router.switch_to("dummy")
        assert ws1 is ws2
        assert ws1.activated == 1

    def test_switch_deactivates_previous(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(DummyWorkspace)
        registry.register(ChatWorkspace)
        host = WorkspaceHost()
        router = WorkspaceRouter(registry, host)

        dummy = router.switch_to("dummy")
        chat = router.switch_to("chat")
        assert dummy.deactivated == 1
        assert chat is router.current_workspace
        assert router.current_id == "chat"

    def test_switch_to_unknown_returns_none(self, qt_app):
        registry = WorkspaceRegistry()
        host = WorkspaceHost()
        router = WorkspaceRouter(registry, host)
        assert router.switch_to("missing") is None

    def test_close_all_calls_lifecycle(self, qt_app):
        registry = WorkspaceRegistry()
        registry.register(DummyWorkspace)
        host = WorkspaceHost()
        router = WorkspaceRouter(registry, host)

        ws = router.switch_to("dummy")
        router.close_all()
        assert ws.deactivated == 1
        assert ws.closed == 1
        assert router.current_workspace is None


class TestBuiltinWorkspaces:
    def test_builtin_workspace_attributes(self, qt_app):
        assert ChatWorkspace.workspace_id == "chat"
        assert ChatWorkspace.title == "Chat"
        assert SkillWorkspace.workspace_id == "skill"
        assert ToolWorkspace.workspace_id == "tool"
        assert ProviderWorkspace.workspace_id == "provider"

    def test_builtin_workspaces_are_qwidgets(self, qt_app):
        assert issubclass(ChatWorkspace, QWidget)
        assert issubclass(SkillWorkspace, QWidget)
        assert issubclass(ToolWorkspace, QWidget)
        assert issubclass(ProviderWorkspace, QWidget)
