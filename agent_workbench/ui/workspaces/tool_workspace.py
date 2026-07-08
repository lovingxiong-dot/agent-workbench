"""agent_workbench/ui/workspaces/tool_workspace.py — Tool Workspace。"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from agent_workbench.ui.workspace import Workspace


class ToolWorkspace(Workspace):
    """Tool Workspace 占位实现。"""

    workspace_id = "tool"
    title = "Tool"
    icon = "🛠️"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
