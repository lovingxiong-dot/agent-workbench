"""agent_workbench/ui/workbench/presentation.py — UI Presentation Model。

这些 PresentationModel 是 UI 层自己的数据模型，与 Runtime 的 Capability Metadata 解耦。
MetadataAdapter 负责把 Runtime Metadata 转换为 PresentationModel，供 Navigator / Inspector / StatusBar 使用。

设计约束：
- 只包含纯数据字段，不引用 Qt / Runtime / Provider。
- 字段必须覆盖 Metadata Contract 中所有常用属性，新增字段必须有默认值。
- 支持嵌套 children，允许 Resource 树等层级结构进入 PresentationModel。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from agent_workbench.ui.workbench.view_schema import PropertyBinding


@dataclass
class PropertyPresentation:
    """Inspector 中可编辑属性的 PresentationModel。"""

    name: str
    label: str
    type: str  # string, number, boolean, select, textarea, json, password
    value: Any
    options: List[Any] = field(default_factory=list)
    editable: bool = True
    description: str = ""
    default_value: Any = None
    category: str = ""
    sensitive: bool = False
    placeholder: str = ""
    required: bool = False
    binding: "PropertyBinding | None" = None  # 动态绑定 Runtime 数据


@dataclass
class StatisticPresentation:
    """Inspector / StatusBar 中只读统计项的 PresentationModel。"""

    name: str
    label: str
    value: Any
    format: str = "text"  # text, number, bytes, percent, duration
    description: str = ""
    unit: str = ""
    timestamp: datetime | None = None


@dataclass
class ActionPresentation:
    """Inspector 中可执行操作的 PresentationModel。"""

    name: str
    label: str
    icon: str = ""
    description: str = ""
    enabled: bool = True
    order: int = 0
    danger: bool = False


@dataclass
class ModulePresentation:
    """Navigator / Inspector / StatusBar 中模块或对象的 PresentationModel。

    既可用于 Capability Module，也可用于 Resource（通过 type / connection 区分）。
    """

    id: str
    type: str  # runtime, session, model, tool, memory, resource, ...
    name: str
    description: str = ""
    icon: str = ""
    properties: List[PropertyPresentation] = field(default_factory=list)
    statistics: List[StatisticPresentation] = field(default_factory=list)
    actions: List[ActionPresentation] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    order: int = 0
    category: str = ""
    view_schema_id: str = ""
    children: List["ModulePresentation"] = field(default_factory=list)
    connection: Dict[str, Any] = field(default_factory=dict)
