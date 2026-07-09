"""agent_workbench/ui/workbench/tool_bar_host.py — ToolBar Host。

职责：
- 作为 Workbench 快捷工具栏区域的稳定容器。
- 转发 action_triggered 信号到 Workbench。
"""
from __future__ import annotations

from PySide6.QtCore import Signal

from agent_workbench.ui.workbench.host_base import WorkbenchAreaHost
from agent_workbench.ui.workbench.tool_bar import ToolBar


class ToolBarHost(WorkbenchAreaHost):
    """Workbench 快捷工具栏 Host。"""

    action_triggered = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        tool_bar = ToolBar(self)
        self.mount(tool_bar)
        tool_bar.action_triggered.connect(self.action_triggered.emit)

    def set_actions(self, actions: list) -> None:
        """用 ActionPresentation 列表重建工具栏按钮。

        Args:
            actions: ActionPresentation 列表。
        """
        content = self.content
        if isinstance(content, ToolBar):
            content.set_actions(actions)

    def actions_state(self) -> dict[str, bool]:
        """返回当前按钮启用状态（供测试使用）。"""
        content = self.content
        if isinstance(content, ToolBar):
            return content.actions_state()
        return {}
