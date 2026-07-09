"""agent_workbench/ui/workbench/view_component.py — View 层组件契约定义。

职责：
- 定义 ViewComponentDefinition：View 层组件的最小元数据契约。
- Registry 只负责「找得到」，不负责「做出来」。
- 具体 Qt 控件（Terminal / Editor / Chart 等）属于 Builtin Component，不在此注册。

设计约束：
- 字段只保留最小集合，禁止膨胀。
- 不引用 Qt / Runtime / Provider。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ViewComponentDefinition:
    """View 层组件定义。

    Registry 只保存组件元数据，不保存组件实例。renderer 是 renderer 标识，
    由 ViewSchemaRenderer 根据 component_id 找到定义后再决定如何渲染。
    """

    id: str
    renderer: str  # toolbar | status_bar | inspector | workspace | ...
    supported_schema: list[str] = field(default_factory=list)
    supported_binding: list[str] = field(default_factory=list)
    default_size: dict[str, Any] | None = None  # e.g. {"width": 400, "height": 300}
