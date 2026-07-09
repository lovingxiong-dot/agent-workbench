"""agent_workbench/ui/workbench/status_bar_host.py — StatusBar Host。

职责：
- 作为 Workbench 底部状态栏区域的稳定容器。
- 提供 set_runtime / set_provider / set_model 等稳定接口，供 WorkbenchUIController 使用。
- 当前挂载 StatusBar widget；未来可替换为更复杂的状态面板。
"""
from __future__ import annotations

from agent_workbench.ui.workbench.host_base import WorkbenchAreaHost
from agent_workbench.ui.workbench.status_bar import StatusBar


class StatusBarHost(WorkbenchAreaHost):
    """Workbench 底部状态栏 Host。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mount(StatusBar(self))

    def set_runtime(self, status: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_runtime(status)

    def set_provider(self, name: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_provider(name)

    def set_model(self, name: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_model(name)

    def set_session(self, info: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_session(info)

    def set_token(self, used: int, total: int) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_token(used, total)

    def set_latency(self, ms: float) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_latency(ms)

    def set_profile(self, name: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_profile(name)

    def set_trace(self, level: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_trace(level)

    def set_memory(self, status: str) -> None:
        content = self.content
        if isinstance(content, StatusBar):
            content.set_memory(status)

    def set_statistics(self, statistics: list) -> None:
        """聚合 PresentationModel.statistics 刷新状态栏。

        Args:
            statistics: StatisticPresentation 列表。
        """
        content = self.content
        if isinstance(content, StatusBar):
            content.set_statistics(statistics)

    def values(self) -> dict[str, str]:
        """返回状态栏当前所有文本值（供测试使用）。"""
        content = self.content
        if isinstance(content, StatusBar):
            return content.values()
        return {}
