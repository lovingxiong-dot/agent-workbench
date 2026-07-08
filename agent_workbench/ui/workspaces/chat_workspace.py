"""agent_workbench/ui/workspaces/chat_workspace.py — Chat Workspace。"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from agent_workbench.ui.workspace import Workspace


class ChatWorkspace(Workspace):
    """Chat Workspace 占位实现。"""

    workspace_id = "chat"
    title = "Chat"
    icon = "💬"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
