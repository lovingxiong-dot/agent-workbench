"""agent_workbench/ui/workbench/presentation.py — UI Presentation Model。

这些 PresentationModel 是 UI 层自己的数据模型，与 Runtime 的 Capability Metadata 解耦。
MetadataAdapter 负责把 Runtime Metadata 转换为 PresentationModel，供 Navigator / Inspector 使用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class PropertyPresentation:
    """Inspector 中可编辑属性的 PresentationModel。"""

    name: str
    label: str
    type: str  # string, number, boolean, select, textarea, json
    value: Any
    options: List[str] = field(default_factory=list)
    editable: bool = True
    description: str = ""


@dataclass
class StatisticPresentation:
    """Inspector 中只读统计项的 PresentationModel。"""

    name: str
    label: str
    value: Any
    format: str = "text"  # text, number, bytes, percent
    description: str = ""


@dataclass
class ActionPresentation:
    """Inspector 中可执行操作的 PresentationModel。"""

    name: str
    label: str
    icon: str = ""
    description: str = ""


@dataclass
class ModulePresentation:
    """Navigator 中可选中模块的 PresentationModel。"""

    id: str
    type: str  # runtime, session, model, tool, memory, ...
    name: str
    description: str
    icon: str
    properties: List[PropertyPresentation] = field(default_factory=list)
    statistics: List[StatisticPresentation] = field(default_factory=list)
    actions: List[ActionPresentation] = field(default_factory=list)
