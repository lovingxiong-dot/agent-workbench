"""agent_workbench/ui/workbench/view_component_registry.py — View 层组件注册表。

职责：
- 只负责「找得到」ViewComponentDefinition。
- 不负责创建任何 Qt 控件或具体 Renderer 实例。

接口限制（仅此四个）：
- register(definition)
- unregister(component_id)
- resolve(component_id)
- list()
"""
from __future__ import annotations

from agent_workbench.ui.workbench.view_component import ViewComponentDefinition


class ViewComponentRegistry:
    """View 层组件注册表。"""

    def __init__(self) -> None:
        self._components: dict[str, ViewComponentDefinition] = {}

    def register(self, definition: ViewComponentDefinition) -> None:
        """注册一个 ViewComponentDefinition。"""
        self._components[definition.id] = definition

    def unregister(self, component_id: str) -> None:
        """注销指定组件。"""
        self._components.pop(component_id, None)

    def resolve(self, component_id: str) -> ViewComponentDefinition | None:
        """按 ID 查找组件定义；找不到返回 None。"""
        return self._components.get(component_id)

    def list(self) -> list[ViewComponentDefinition]:
        """返回所有已注册组件定义。"""
        return list(self._components.values())
