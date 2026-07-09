"""Tests for Navigator / Inspector consuming ModulePresentation."""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QWidget,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.inspector import Inspector
from agent_workbench.ui.workbench.navigator import Navigator
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestNavigatorLoadPresentations:
    def test_workspaces_render_as_functional_tabs(self, qt_app):
        nav = Navigator()
        presentations = [
            ModulePresentation(id="chat", type="workspace", name="Chat", icon="💬", category="workspace"),
            ModulePresentation(id="skill", type="workspace", name="Skills", icon="🛠", category="workspace"),
        ]
        nav.load_presentations(presentations)

        assert nav._functional_list.count() == 2
        assert nav._settings_list.count() == 0

    def test_settings_render_in_settings_area(self, qt_app):
        nav = Navigator()
        presentations = [
            ModulePresentation(id="model", type="settings", name="AI Models", icon="🤖", category="settings"),
            ModulePresentation(id="mcp", type="settings", name="MCP", icon="🔌", category="settings"),
        ]
        nav.load_presentations(presentations)

        assert nav._functional_list.count() == 0
        assert nav._settings_list.count() == 2

    def test_mixed_presentations_group_correctly(self, qt_app):
        nav = Navigator()
        presentations = [
            ModulePresentation(id="chat", type="workspace", name="Chat", icon="💬", category="workspace"),
            ModulePresentation(id="model", type="settings", name="AI Models", icon="🤖", category="settings"),
        ]
        nav.load_presentations(presentations)

        assert nav._functional_list.count() == 1
        assert nav._settings_list.count() == 1

    def test_selection_emits_id_for_loaded_presentations(self, qt_app):
        nav = Navigator()
        nav.load_presentations([
            ModulePresentation(id="chat", type="workspace", name="Chat", icon="💬", category="workspace"),
        ])

        captured: list[str] = []
        nav.selection_changed.connect(captured.append)

        nav.set_selection("chat")
        QApplication.processEvents()

        assert captured == ["chat"]

    def test_add_requested_emits_for_settings_presentation(self, qt_app):
        nav = Navigator()
        nav.load_presentations([
            ModulePresentation(id="mcp", type="settings", name="MCP", icon="🔌", category="settings"),
        ])

        captured: list[str] = []
        nav.add_requested.connect(captured.append)

        widget = nav._settings_widgets["mcp"]
        widget._add_btn.click()
        QApplication.processEvents()

        assert captured == ["mcp"]


class TestInspectorPresentationRendering:
    def _render(self, qt_app, presentation: ModulePresentation) -> Inspector:
        inspector = Inspector()
        inspector.set_object(presentation)
        QApplication.processEvents()
        return inspector

    def test_property_categories_create_sections(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="api_key", label="API Key", type="string", value="secret", category="auth"),
                PropertyPresentation(name="model", label="Model", type="string", value="gpt-4o", category="basic"),
                PropertyPresentation(name="timeout", label="Timeout", type="number", value="30", category=""),
            ],
        ))

        labels = [
            inspector._content_layout.itemAt(i).widget().text()
            for i in range(inspector._content_layout.count() - 1)
            if isinstance(inspector._content_layout.itemAt(i).widget(), QLabel)
        ]
        assert "auth" in labels
        assert "basic" in labels
        assert "General" in labels

    def test_sensitive_property_uses_password_input(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="api_key", label="API Key", type="string", value="secret", sensitive=True),
            ],
        ))

        editor = self._find_first_widget(inspector, QLineEdit)
        assert editor is not None
        assert editor.echoMode() == QLineEdit.EchoMode.Password

    def test_textarea_property_uses_text_edit(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="prompt",
            type="prompt",
            name="Prompt",
            properties=[
                PropertyPresentation(name="template", label="Template", type="textarea", value="hello"),
            ],
        ))

        editor = self._find_first_widget(inspector, QTextEdit)
        assert editor is not None
        assert editor.toPlainText() == "hello"

    def test_boolean_property_uses_checkbox(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="stream", label="Stream", type="boolean", value=True),
            ],
        ))

        editor = self._find_first_widget(inspector, QCheckBox)
        assert editor is not None
        assert editor.isChecked() is True

    def test_select_property_uses_combobox(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="mode", label="Mode", type="select", value="agent", options=["agent", "chat"]),
            ],
        ))

        editor = self._find_first_widget(inspector, QComboBox)
        assert editor is not None
        assert editor.currentText() == "agent"

    def test_readonly_property_is_disabled(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="id", label="ID", type="string", value="model-1", editable=False),
            ],
        ))

        editor = self._find_first_widget(inspector, QLineEdit)
        assert editor is not None
        assert editor.isReadOnly() is True
        assert editor.isEnabled() is False

    def test_readonly_boolean_checkbox_is_disabled(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            properties=[
                PropertyPresentation(name="stream", label="Stream", type="boolean", value=True, editable=False),
            ],
        ))

        editor = self._find_first_widget(inspector, QCheckBox)
        assert editor is not None
        assert editor.isEnabled() is False

    def test_action_enabled_respected(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="runtime",
            type="runtime",
            name="Runtime",
            actions=[
                ActionPresentation(name="start", label="Start", enabled=True),
                ActionPresentation(name="stop", label="Stop", enabled=False),
            ],
        ))

        buttons = [
            inspector._content_layout.itemAt(i).widget()
            for i in range(inspector._content_layout.count() - 1)
            if isinstance(inspector._content_layout.itemAt(i).widget(), QPushButton)
        ]
        assert len(buttons) == 2
        assert buttons[0].isEnabled() is True
        assert buttons[1].isEnabled() is False

    def test_statistics_render(self, qt_app):
        inspector = self._render(qt_app, ModulePresentation(
            id="model",
            type="model",
            name="AI Models",
            statistics=[
                StatisticPresentation(name="tokens", label="Tokens", value=1024),
            ],
        ))

        labels = self._find_widgets(inspector, QLabel)
        value_labels = [lbl.text() for lbl in labels if "1024" in lbl.text()]
        assert value_labels

    @staticmethod
    def _find_first_widget(inspector: Inspector, widget_cls):
        widgets = TestInspectorPresentationRendering._find_widgets(inspector, widget_cls)
        return widgets[0] if widgets else None

    @staticmethod
    def _find_widgets(inspector: Inspector, widget_cls):
        found: list = []
        for i in range(inspector._content_layout.count() - 1):
            widget = inspector._content_layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                found.extend(widget.findChildren(widget_cls))
        return found
