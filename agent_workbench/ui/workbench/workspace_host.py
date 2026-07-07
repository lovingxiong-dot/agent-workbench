"""agent_workbench/ui/workbench/workspace_host.py — 中间工作区宿主。

WorkspaceHost 不固定内容。每个 Workspace（Chat / Dashboard / Trace / Task / Editor）
都是可注册的 QWidget，由外部根据 Runtime 状态切换。
"""
from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from v6.ui.base import C


class WorkspaceHost(QWidget):
    """Workbench 中间工作区宿主。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._workspaces: dict[str, int] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._stack = QStackedWidget(self)
        self._layout.addWidget(self._stack)
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def register_workspace(self, workspace_id: str, widget: QWidget) -> None:
        """注册一个 Workspace。"""
        if workspace_id in self._workspaces:
            return
        idx = self._stack.addWidget(widget)
        self._workspaces[workspace_id] = idx

    def switch_to(self, workspace_id: str) -> None:
        """切换到指定 Workspace。"""
        idx = self._workspaces.get(workspace_id)
        if idx is not None:
            self._stack.setCurrentIndex(idx)
