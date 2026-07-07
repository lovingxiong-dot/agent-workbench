"""agent_workbench/ui/main_window.py — Agent Workbench V6 主窗口。

基于 v6 三栏高级 UI 构建：
- 左栏：v6 会话/文件/功能列表 + 新增「设置」按钮。
- 中区：v6 聊天区域。
- 右栏：v6 文件/终端/浏览器 + 新增「配置」标签页（内嵌 Agent Configuration 面板）。
- 业务控制：WorkbenchUIController，聊天走 Agent Workbench Runtime。

完全保留 v6 UI 的设计风格与行为边界。
"""
from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from v6.layout_manager import LayoutManager
from v6.ui.base import theme
from v6.ui.chat_area import ChatArea
from v6.ui.window_frame import FramelessWindowHelper

from agent_workbench.ui.config_panel import AgentConfigPanel
from agent_workbench.ui.left_panel import WorkbenchLeftPanel
from agent_workbench.ui.right_panel import WorkbenchRightPanel
from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


class WorkbenchMainWindow(QMainWindow):
    """Agent Workbench V6 主窗口。"""

    def __init__(
        self,
        ui_controller: WorkbenchUIController | None = None,
        config: Dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._config = config or {}
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)

        self._central = QWidget()
        self.setCentralWidget(self._central)
        self._layout = LayoutManager(self._central)

        self._left = WorkbenchLeftPanel()
        self._chat = ChatArea()
        self._right = WorkbenchRightPanel()

        self._layout.left_panel.layout().addWidget(self._left)
        self._layout.chat_area.layout().addWidget(self._chat)
        self._layout.right_panel.layout().addWidget(self._right)

        self._ctrl = ui_controller or WorkbenchUIController()
        self._config_panel = AgentConfigPanel(self._ctrl.workbench_controller, self._right)
        self._right.set_config_panel(self._config_panel)

        self._connect()
        self._ctrl.startup()
        self._helper = FramelessWindowHelper(self, self._central)
        self._apply_theme()

    def _connect(self) -> None:
        # Widget -> UIController
        self._left.session_selected.connect(self._ctrl.on_session_selected)
        self._left.new_session_requested.connect(self._ctrl.on_new_session)
        self._left.session_action.connect(self._ctrl.on_session_action)
        self._left.search_text_changed.connect(self._ctrl.on_search_text_changed)
        self._left.theme_toggled.connect(self._ctrl.on_theme_toggled)
        self._left.settings_requested.connect(self._ctrl.on_settings_requested)
        self._left.file_selected.connect(self._ctrl.on_file_selected)
        self._chat.send_msg.connect(self._ctrl.on_send_msg)
        self._chat.stop_msg.connect(self._ctrl.on_stop_msg)
        self._chat.mode_changed.connect(self._ctrl.on_mode_changed)
        self._chat.model_changed.connect(self._ctrl.on_model_changed)
        self._chat.export_requested.connect(self._ctrl.on_export_requested)
        self._chat.settings_requested.connect(self._ctrl.on_settings_requested)
        self._chat.search_toggled.connect(self._ctrl.on_search_toggled)
        self._chat.more_clicked.connect(self._ctrl.on_more_clicked)
        self._right.open_file.connect(self._ctrl.on_open_file)
        self._right.load_url.connect(self._ctrl.on_load_url)
        self._right.terminal_command.connect(self._ctrl.on_terminal_command)
        self._right.tab_closed.connect(self._ctrl.on_tab_closed)

        # 窗口行为
        self._chat.left_expand_toggled.connect(self._layout.toggle_left)
        self._chat.toggle_right_panel.connect(self._layout.toggle_right)
        self._right.set_window_buttons(self.showMinimized, self._toggle_maximized, self.close)

        # UIController -> Widget
        self._ctrl.sign_update_sessions.connect(self._left.update_sessions)
        self._ctrl.sign_set_active_session.connect(self._left.set_active_session)
        self._ctrl.sign_theme_changed.connect(self._apply_theme)
        self._ctrl.sign_set_title.connect(self._chat.set_title)
        self._ctrl.sign_chat_user.connect(self._chat.append_user)
        self._ctrl.sign_chat_ai.connect(self._chat.append_ai)
        self._ctrl.sign_stream_chunk.connect(self._chat.stream_chunk)
        self._ctrl.sign_stream_end.connect(self._chat.stream_end)
        self._ctrl.sign_set_streaming.connect(self._chat.set_streaming)
        self._ctrl.sign_tool_executed.connect(self._chat.tool_executed)
        self._ctrl.sign_confirm_required.connect(self._chat.confirm_required)
        self._ctrl.sign_show_analyze_button.connect(self._chat.set_analyze_button_visible)
        self._ctrl.sign_open_file.connect(self._right.show_file)
        self._ctrl.sign_update_terminal.connect(self._right.append_terminal)
        self._ctrl.sign_switch_tab.connect(self._right.switch_tab)

    def _apply_theme(self) -> None:
        self.setStyleSheet(f"background-color: {theme.C['bg_primary']};")

    def _toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._ctrl.shutdown()
        event.accept()


def main() -> int:
    import sys

    app = QApplication(sys.argv)
    win = WorkbenchMainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    return app.exec()


if __name__ == "__main__":
    import sys

    sys.exit(main())
