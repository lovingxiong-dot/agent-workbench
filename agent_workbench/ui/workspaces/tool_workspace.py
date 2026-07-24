"""agent_workbench/ui/workspaces/tool_workspace.py — Tool Workspace。

v6.10.0-alpha Tool Runtime Product Layer。

原 ToolWorkspace 占位实现已存在；本扩展追加 ViewModel 接入。
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from agent_workbench.ui.workspace import Workspace


class ToolWorkspace(Workspace):
    """Tool Workspace（v6.10.0-alpha 扩展 ViewModel 接入）。"""

    workspace_id = "tool"
    title = "Tool"
    icon = "🛠️"

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: Tool 操作 signals
    # ──────────────────────────────────────────────────────────

    enable_requested = Signal(str)  # tool_id
    disable_requested = Signal(str)  # tool_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 占位 label（实际 UI 在 Phase 5 Product Shell Integration 中替换）
        self._placeholder = QLabel("Tool Management (v6.10.0-alpha ready)", self)
        self._layout.addWidget(self._placeholder)

        self._tools: list[Any] = []  # ToolViewModel 列表

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: ViewModel API
    # ──────────────────────────────────────────────────────────

    def set_view_models(self, view_models: list[Any]) -> None:
        """设置 Tool ViewModel 列表（v6.10 推荐入口）。

        Args:
            view_models: view_models.tool.ToolViewModel 列表。
        """
        self._tools = list(view_models)
        # 占位实现：仅记录，不做复杂 UI（Phase 5 扩展）
        enabled = sum(1 for t in self._tools if t.status == "enabled")
        self._placeholder.setText(
            f"Tool Management: {len(self._tools)} tools ({enabled} enabled)"
        )

    def get_view_models(self) -> list[Any]:
        """获取当前 ViewModel 列表。"""
        return list(self._tools)

    def request_enable(self, tool_id: str) -> None:
        """UI 请求启用 Tool（emit signal）。"""
        self.enable_requested.emit(tool_id)

    def request_disable(self, tool_id: str) -> None:
        """UI 请求禁用 Tool（emit signal）。"""
        self.disable_requested.emit(tool_id)