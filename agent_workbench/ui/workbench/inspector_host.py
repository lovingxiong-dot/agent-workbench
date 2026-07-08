"""agent_workbench/ui/workbench/inspector_host.py — Inspector Host。

职责：
- 作为 Workbench 右侧属性检查器区域的稳定容器。
- 提供 set_object / clear 等稳定接口，供 WorkbenchUIController 使用。
- 当前挂载 Inspector widget；未来可替换为 Property / Statistics / Actions 的其他渲染实现。
"""
from __future__ import annotations

from PySide6.QtCore import Signal

from agent_workbench.ui.workbench.host_base import WorkbenchAreaHost
from agent_workbench.ui.workbench.inspector import Inspector
from agent_workbench.ui.workbench.presentation import ModulePresentation


class InspectorHost(WorkbenchAreaHost):
    """Workbench 右侧 Inspector Host。"""

    property_changed = Signal(str, str, object)  # object_id, property_name, new_value
    action_triggered = Signal(str, str)  # object_id, action_name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        inspector = Inspector(self)
        self.mount(inspector)
        inspector.property_changed.connect(self.property_changed.emit)
        inspector.action_triggered.connect(self.action_triggered.emit)

    def set_object(self, presentation: ModulePresentation) -> None:
        """根据 PresentationModel 渲染 Inspector。"""
        content = self.content
        if isinstance(content, Inspector):
            content.set_object(presentation)

    def clear(self) -> None:
        """清空 Inspector 内容。"""
        content = self.content
        if isinstance(content, Inspector):
            content.set_object(ModulePresentation(id="", type="", name="Inspector", description="", icon=""))

    @property
    def object_id(self) -> str:
        """当前展示对象的 id。"""
        content = self.content
        if isinstance(content, Inspector):
            return content._object_id
        return ""

    @property
    def title(self) -> str:
        """当前展示对象的标题。"""
        content = self.content
        if isinstance(content, Inspector):
            return content._title.text()
        return ""

    def dispose(self) -> None:
        """释放 Inspector 内容。"""
        self.clear()
        super().dispose()
