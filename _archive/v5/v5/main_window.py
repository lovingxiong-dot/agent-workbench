"""v5 轻量化主窗口：仅 UI 组装 + 单层信号转发。"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QFileDialog, QInputDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from v5.widgets import LeftPanel, ChatArea, RightPanel
from v5.widgets.base import theme, InvisibleResizeHandle
from v5.widgets.settings_dialog import SettingsDialog
from v5.controller.work_controller import WorkController


class MainWindow(QMainWindow):
    def __init__(self, controller: WorkController, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self._ctrl = controller
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self._drag_pos = None
        self.setWindowTitle(controller._config.get("app.version", "AI Agent Workbench"))

        self._build_ui()
        self._apply_theme()
        self._bind_controller()
        theme.changed.connect(self._apply_theme)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setChildrenCollapsible(False)

        self._left = LeftPanel()
        self._center = ChatArea()
        self._center.set_modes(self._ctrl.manual_modes)
        self._right = RightPanel()

        self._splitter.addWidget(self._left)
        self._splitter.addWidget(self._center)
        self._splitter.addWidget(self._right)
        self._splitter.setSizes([220, 760, 400])

        self._handle0 = InvisibleResizeHandle(self._splitter, 0, central)
        self._handle1 = InvisibleResizeHandle(self._splitter, 1, central)

        root.addWidget(self._splitter)

    def _apply_theme(self):
        from v5.widgets.base import C
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def _bind_controller(self):
        """单层信号转发：UI -> Controller 方法，Controller -> UI 方法。"""
        # UI -> Controller
        self._left.sign_new_chat.connect(self._ctrl.handle_create_chat)
        self._left.sign_select_session.connect(self._ctrl.handle_switch_session)
        self._left.sign_session_action.connect(self._ctrl.handle_session_action)
        self._left.sign_search_input.connect(self._ctrl.handle_search_input)
        self._left.sign_switch_theme.connect(self._ctrl.handle_switch_theme)

        self._center.sign_send_msg.connect(self._ctrl.handle_send_message)
        self._center.sign_stop_msg.connect(self._ctrl.handle_stop_message)
        self._center.sign_mode_changed.connect(self._ctrl.handle_mode_changed)
        self._center.sign_model_changed.connect(self._ctrl.handle_model_changed)
        self._center.sign_export_requested.connect(self._on_export_requested)
        self._center.sign_settings_requested.connect(self._on_settings_requested)
        self._center.sign_toggle_right.connect(self.toggle_panels)
        self._center.analyze_project_clicked.connect(self._ctrl.handle_analyze_project)
        self._center.confirmation_clicked.connect(self._ctrl.handle_confirmation_result)

        self._ctrl.sign_analyze_button_visible.connect(self._center.set_analyze_button_visible)
        self._ctrl.sign_rename_requested.connect(self._on_rename_requested)
        self._ctrl.sign_tool_executed.connect(self._center.append_tool)
        self._ctrl.sign_confirm_required.connect(self._center.show_confirmation)

        self._right.sign_open_file.connect(self._ctrl.handle_open_file)
        self._right.sign_load_url.connect(self._ctrl.handle_load_url)
        self._right.sign_terminal_command.connect(self._ctrl.handle_terminal_command)

        # Controller -> UI
        self._ctrl.sign_update_sessions.connect(self._left.refresh)
        self._ctrl.sign_set_active_session.connect(self._left.set_active_session)
        self._ctrl.sign_set_title.connect(self._center.set_title)
        self._ctrl.sign_chat_user.connect(self._center.append_user)
        self._ctrl.sign_chat_ai.connect(self._center.append_ai)
        self._ctrl.sign_stream_chunk.connect(self._center.append_chunk)
        self._ctrl.sign_stream_end.connect(self._center.finalize_stream)
        self._ctrl.sign_set_streaming.connect(self._center.set_streaming)
        self._ctrl.sign_open_file_right.connect(self._right.open_file)
        self._ctrl.sign_update_terminal.connect(self._right.update_terminal)
        self._ctrl.sign_switch_tab.connect(self._right.switch_tab)

        # 全局快捷键
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._center._toggle_search)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.toggle_panels)
        QShortcut(QKeySequence("Esc"), self, activated=self._on_escape_pressed)

    def toggle_panels(self):
        """同时切换左右面板可见性，中间栏自适应。"""
        if self._left.isVisible() or self._right.isVisible():
            self._left.hide()
            self._right.hide()
            self._splitter.setSizes([0, self.width(), 0])
            self._center._header.set_expanded_state(False)
        else:
            self._left.show()
            self._right.show()
            self._splitter.setSizes([220, self.width() - 620, 400])
            self._center._header.set_expanded_state(True)

    def _on_escape_pressed(self):
        if self._center._search_bar.isVisible():
            self._center._toggle_search()
        if self._center._more_dropdown.isVisible():
            self._center._more_dropdown.hide()

    def _on_rename_requested(self, sid: str, current_title: str):
        new_title, ok = QInputDialog.getText(
            self, "重命名会话", "新标题：", text=current_title
        )
        if ok and new_title.strip():
            self._ctrl.handle_session_rename(sid, new_title.strip())

    def _on_export_requested(self):
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出会话",
            "",
            "Markdown (*.md);;JSON (*.json)",
        )
        if not path:
            return
        fmt = "json" if selected_filter and "JSON" in selected_filter else "markdown"
        if fmt == "markdown" and not path.lower().endswith(".md"):
            path += ".md"
        elif fmt == "json" and not path.lower().endswith(".json"):
            path += ".json"
        self._ctrl.export_session(path, fmt)

    def _on_settings_requested(self):
        dlg = SettingsDialog(self._ctrl._config, modes=self._ctrl.manual_modes, parent=self)

        def _apply():
            self._ctrl.apply_settings(
                dlg._theme_box.currentText(),
                dlg._mode_box.currentText(),
                dlg._model_box.currentText(),
            )
            self._center.set_mode(self._ctrl._current_mode)
            self._center.set_model(self._ctrl._current_model)

        dlg.settings_applied.connect(_apply)
        dlg.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
