"""agent_workbench/ui/workbench/workbench.py — Workbench 核心骨架。

组装 NavigatorHost / WorkspaceHost / InspectorHost / StatusBarHost / CommandBarHost。
Workbench 不持有 Runtime，只持有 UI 区域 Host 和 Selection。
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
from agent_workbench.ui.workbench.command_bar_host import CommandBarHost
from agent_workbench.ui.workbench.inspector_host import InspectorHost
from agent_workbench.ui.workbench.navigator_host import NavigatorHost
from agent_workbench.ui.workbench.status_bar_host import StatusBarHost
from agent_workbench.ui.workbench.tool_bar_host import ToolBarHost
from agent_workbench.ui.workbench.workspace_host import WorkspaceHost
from agent_workbench.ui.workspace_registry import WorkspaceRegistry
from agent_workbench.ui.workspace_router import WorkspaceRouter


class Workbench(QWidget):
    """Workbench 核心骨架。"""

    property_changed = Signal(str, str, object)  # object_id, property_name, value
    action_triggered = Signal(str, str)  # object_id, action_name
    command_submitted = Signal(str)
    selection_changed = Signal(str)  # object_id
    tool_bar_action_triggered = Signal(str)  # action_name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 顶部：三栏（NavigatorHost | WorkspaceHost | InspectorHost）
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setHandleWidth(1)

        self._navigator = NavigatorHost(self)
        self._workspace = WorkspaceHost(self)
        self._inspector = InspectorHost(self)

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

        # 工具栏（根据选中 ModulePresentation.actions 动态生成）
        self._tool_bar = ToolBarHost(self)
        self._layout.addWidget(self._tool_bar)

        # 底部：StatusBarHost + CommandBarHost
        self._status_bar = StatusBarHost(self)
        self._command_bar = CommandBarHost(self)
        self._layout.addWidget(self._status_bar)
        self._layout.addWidget(self._command_bar)

        # Workspace 注册表与路由器
        self._workspace_registry = WorkspaceRegistry()
        self._workspace_router = WorkspaceRouter(self._workspace_registry, self._workspace)

        # 转发信号
        self._navigator.selection_changed.connect(self.selection_changed.emit)
        self._inspector.property_changed.connect(self.property_changed.emit)
        self._inspector.action_triggered.connect(self.action_triggered.emit)
        self._tool_bar.action_triggered.connect(self.tool_bar_action_triggered.emit)
        self._command_bar.command_submitted.connect(self.command_submitted.emit)

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    @property
    def navigator(self) -> NavigatorHost:
        return self._navigator

    @property
    def workspace(self) -> WorkspaceHost:
        return self._workspace

    @property
    def inspector(self) -> InspectorHost:
        return self._inspector

    @property
    def tool_bar(self) -> ToolBarHost:
        return self._tool_bar

    @property
    def status_bar(self) -> StatusBarHost:
        return self._status_bar

    @property
    def command_bar(self) -> CommandBarHost:
        return self._command_bar

    @property
    def workspace_registry(self) -> WorkspaceRegistry:
        return self._workspace_registry

    @property
    def workspace_router(self) -> WorkspaceRouter:
        return self._workspace_router
