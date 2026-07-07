"""agent_workbench/ui/main_window.py — Agent Workbench V6 主窗口。

架构：
- MainWindow：顶层窗口壳，只负责 OS 级窗口行为与无边框处理。
- WorkbenchHost：Host 层，装载 TitleBar + Workbench。
- Workbench：IDE 骨架（Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar）。

所有业务控制通过 WorkbenchUIController 完成；UI 只负责展示与信号转发。
"""
from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from v6.ui.base import theme
from v6.ui.window_frame import FramelessWindowHelper

from agent_workbench.ui.workbench import WorkbenchHost
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

        self._host = WorkbenchHost(self)
        self.setCentralWidget(self._host)

        if ui_controller is None:
            self._ctrl = WorkbenchUIController(workbench_host=self._host)
        else:
            self._ctrl = ui_controller
            if getattr(self._ctrl, "_host", None) is None:
                self._ctrl._host = self._host
        self._connect()
        self._ctrl.startup()
        self._helper = FramelessWindowHelper(self, self._host)
        self._apply_theme()

    def _connect(self) -> None:
        # TitleBar 窗口控制
        self._host.minimize_requested.connect(self.showMinimized)
        self._host.maximize_requested.connect(self._toggle_maximized)
        self._host.close_requested.connect(self.close)

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
