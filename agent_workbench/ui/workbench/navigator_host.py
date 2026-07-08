"""agent_workbench/ui/workbench/navigator_host.py — Navigator Host。

职责：
- 作为 Workbench 左侧区域的稳定容器。
- 提供 register / clear / select / modules 等稳定接口，供 WorkbenchUIController 使用。
- 当前挂载 Navigator widget；未来可替换为 Project Explorer / Trace Explorer 等内容。
"""
from __future__ import annotations

from PySide6.QtCore import Signal

from agent_workbench.ui.workbench.host_base import WorkbenchAreaHost
from agent_workbench.ui.workbench.navigator import Navigator
from agent_workbench.ui.workbench.presentation import ModulePresentation


class NavigatorHost(WorkbenchAreaHost):
    """Workbench 左侧导航 Host。"""

    selection_changed = Signal(str)  # module_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        navigator = Navigator(self)
        self.mount(navigator)
        navigator.selection_changed.connect(self.selection_changed.emit)

    def register_module(self, presentation: ModulePresentation) -> None:
        """注册一个模块到导航。"""
        content = self.content
        if isinstance(content, Navigator):
            content.register_module(presentation)

    def clear_modules(self) -> None:
        """清空所有模块。"""
        content = self.content
        if isinstance(content, Navigator):
            content.clear_modules()

    def set_selection(self, module_id: str) -> None:
        """设置当前选中项。"""
        content = self.content
        if isinstance(content, Navigator):
            content.set_selection(module_id)

    def modules(self) -> set[str]:
        """返回已注册模块的 id 集合。"""
        content = self.content
        if isinstance(content, Navigator):
            return set(content._modules.keys())
        return set()

    def dispose(self) -> None:
        """释放导航内容。"""
        self.clear_modules()
        super().dispose()
