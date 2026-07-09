"""agent_workbench/ui/workbench/workbench_host.py — MainWindow 内的 Workbench 宿主。

WorkbenchHost 负责把 Workbench 嵌入到现有 MainWindow 中，并添加 Host 级 UI：
- TitleBar（标题、Runtime 状态、窗口控制）
- Workbench（Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar）

这样 MainWindow 可以一直存在，Workbench 可替换（Desktop / Web / Embedded）。
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from agent_workbench.ui.workbench.title_bar import WorkbenchTitleBar
from agent_workbench.ui.workbench.workbench import Workbench


class WorkbenchHost(QWidget):
    """Workbench 宿主：将 Workbench 嵌入到 MainWindow。"""

    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    feedback_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._title_bar = WorkbenchTitleBar(self)
        self._title_bar.minimize_requested.connect(self.minimize_requested.emit)
        self._title_bar.maximize_requested.connect(self.maximize_requested.emit)
        self._title_bar.close_requested.connect(self.close_requested.emit)
        self._title_bar.feedback_requested.connect(self.feedback_requested.emit)
        self._layout.addWidget(self._title_bar)

        self._workbench = Workbench(self)
        self._layout.addWidget(self._workbench, 1)

    @property
    def title_bar(self) -> WorkbenchTitleBar:
        return self._title_bar

    @property
    def workbench(self) -> Workbench:
        return self._workbench

    def set_status(self, running: bool) -> None:
        """更新标题栏 Runtime 状态。"""
        self._title_bar.set_status(running)
