"""agent_workbench/ui/workbench/workbench.py — Workbench 核心骨架。

组装 Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar。
Workbench 不持有 Runtime，只持有 UI 组件和 Selection。
外部（WorkbenchUIController）负责：
- 注册 ModulePresentation
- 切换 Workspace
- 刷新 StatusBar
- 响应 property_changed / action_triggered / command_submitted 信号
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from v6.ui.base import C, install_invisible_handles
from agent_workbench.ui.workbench.command_bar import CommandBar
from agent_workbench.ui.workbench.inspector import Inspector
from agent_workbench.ui.workbench.navigator import Navigator
from agent_workbench.ui.workbench.status_bar import StatusBar
from agent_workbench.ui.workbench.workspace_host import WorkspaceHost


class Workbench(QWidget):
    """Workbench 核心骨架。"""

    property_changed = Signal(str, str, object)  # object_id, property_name, value
    action_triggered = Signal(str, str)  # object_id, action_name
    command_submitted = Signal(str)
    selection_changed = Signal(str)  # object_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 顶部：三栏（Navigator | WorkspaceHost | Inspector）
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setHandleWidth(1)

        self._navigator = Navigator(self)
        self._workspace = WorkspaceHost(self)
        self._inspector = Inspector(self)

        self._navigator.setMinimumWidth(180)
        self._inspector.setMinimumWidth(260)
        self._workspace.setMinimumWidth(240)

        self._splitter.addWidget(self._navigator)
        self._splitter.addWidget(self._workspace)
        self._splitter.addWidget(self._inspector)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        self._splitter.setSizes([220, 640, 320])
        install_invisible_handles(self._splitter, 4)

        self._layout.addWidget(self._splitter, 1)

        # 底部：StatusBar + CommandBar
        self._status_bar = StatusBar(self)
        self._command_bar = CommandBar(self)
        self._layout.addWidget(self._status_bar)
        self._layout.addWidget(self._command_bar)

        # 转发信号
        self._navigator.selection_changed.connect(self.selection_changed.emit)
        self._inspector.property_changed.connect(self.property_changed.emit)
        self._inspector.action_triggered.connect(self.action_triggered.emit)
        self._command_bar.command_submitted.connect(self.command_submitted.emit)

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    @property
    def navigator(self) -> Navigator:
        return self._navigator

    @property
    def workspace(self) -> WorkspaceHost:
        return self._workspace

    @property
    def inspector(self) -> Inspector:
        return self._inspector

    @property
    def status_bar(self) -> StatusBar:
        return self._status_bar

    @property
    def command_bar(self) -> CommandBar:
        return self._command_bar
