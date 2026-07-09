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

    selection_changed = Signal(str)  # workspace_id or category_id
    add_requested = Signal(str)  # category_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        navigator = Navigator(self)
        self.mount(navigator)
        navigator.selection_changed.connect(self.selection_changed.emit)
        navigator.add_requested.connect(self.add_requested.emit)

    def register_functional_tab(self, workspace_id: str, title: str, icon: str) -> None:
        """注册一个顶部功能 Tab。"""
        content = self.content
        if isinstance(content, Navigator):
            content.register_functional_tab(workspace_id, title, icon)

    def register_settings_category(self, category_id: str, title: str, icon: str) -> None:
        """注册一个 Settings 配置分类。"""
        content = self.content
        if isinstance(content, Navigator):
            content.register_settings_category(category_id, title, icon)

    def register_module(self, presentation: ModulePresentation) -> None:
        """注册一个模块到导航（兼容旧接口）。"""
        content = self.content
        if isinstance(content, Navigator):
            content.register_module(presentation)

    def load_presentations(self, presentations: list[ModulePresentation]) -> None:
        """从 ModulePresentation 列表重建导航。"""
        content = self.content
        if isinstance(content, Navigator):
            content.load_presentations(presentations)

    def clear_modules(self) -> None:
        """清空所有模块。"""
        content = self.content
        if isinstance(content, Navigator):
            content.clear_modules()

    def set_selection(self, item_id: str) -> None:
        """设置当前选中项。"""
        content = self.content
        if isinstance(content, Navigator):
            content.set_selection(item_id)

    def set_settings_expanded(self, expanded: bool) -> None:
        """展开或折叠 Settings 区。"""
        content = self.content
        if isinstance(content, Navigator):
            content.set_settings_expanded(expanded)

    def modules(self) -> set[str]:
        """返回已注册模块的 id 集合。"""
        content = self.content
        if isinstance(content, Navigator):
            return set(content._functional_items.keys())
        return set()

    def dispose(self) -> None:
        """释放导航内容。"""
        self.clear_modules()
        super().dispose()
