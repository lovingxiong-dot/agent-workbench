"""agent_workbench/runtime/metadata.py — Runtime Capability Metadata。

这些 dataclass 只描述 Runtime Module 的能力与状态，不包含任何 UI 概念
（如 QWidget、Inspector、Editor、PropertyEditor、Dock、RuntimeObject）。

UI 通过 MetadataAdapter 将 Capability Metadata 翻译为自己的 PresentationModel，
Runtime 完全不依赖 UI。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class PropertyMetadata:
    """模块可配置属性。"""

    name: str
    label: str
    type: str  # string, number, boolean, select, textarea, json
    value: Any
    options: List[str] = field(default_factory=list)
    editable: bool = True
    description: str = ""


@dataclass
class StatisticMetadata:
    """模块运行时统计。"""

    name: str
    label: str
    value: Any
    format: str = "text"  # text, number, bytes, percent
    description: str = ""


@dataclass
class ActionMetadata:
    """模块可执行操作。"""

    name: str
    label: str
    icon: str = ""
    description: str = ""


@dataclass
class ModuleMetadata:
    """模块 Capability Metadata，供 UI Adapter 消费。"""

    id: str
    type: str  # runtime, session, model, tool, memory, ...
    name: str
    description: str
    icon: str
    properties: List[PropertyMetadata] = field(default_factory=list)
    statistics: List[StatisticMetadata] = field(default_factory=list)
    actions: List[ActionMetadata] = field(default_factory=list)
