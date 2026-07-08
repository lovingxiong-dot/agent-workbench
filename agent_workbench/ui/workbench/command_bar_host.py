"""agent_workbench/ui/workbench/command_bar_host.py — CommandBar Host。

职责：
- 作为 Workbench 底部命令输入区域的稳定容器。
- 提供 set_enabled / clear / set_placeholder 等稳定接口，供 WorkbenchUIController 使用。
- 转发 command_submitted 信号。
"""
from __future__ import annotations

from PySide6.QtCore import Signal

from agent_workbench.ui.workbench.command_bar import CommandBar
from agent_workbench.ui.workbench.host_base import WorkbenchAreaHost


class CommandBarHost(WorkbenchAreaHost):
    """Workbench 底部命令输入 Host。"""

    command_submitted = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        command_bar = CommandBar(self)
        self.mount(command_bar)
        command_bar.command_submitted.connect(self.command_submitted.emit)

    def set_enabled(self, enabled: bool) -> None:
        content = self.content
        if isinstance(content, CommandBar):
            content.set_enabled(enabled)

    def clear(self) -> None:
        content = self.content
        if isinstance(content, CommandBar):
            content.set_enabled(True)
            # CommandBar 在提交后自动清空输入框，这里额外确保可输入状态。

    def set_placeholder(self, text: str) -> None:
        content = self.content
        if isinstance(content, CommandBar):
            content._input.setPlaceholderText(text)
