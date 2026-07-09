"""agent_workbench/metadata/model.py — Core Metadata Contract data models.

These dataclasses describe Runtime objects in a platform-agnostic way.
They must remain pure data: no Runtime imports, no UI imports, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List

from agent_workbench.metadata.types import ValueType


@dataclass
class MetadataProperty:
    """对象的可配置属性。

    示例：temperature、api_key、endpoint、enabled。
    """

    id: str
    name: str
    description: str = ""
    value_type: ValueType | str = ValueType.STRING
    current_value: Any = None
    default_value: Any = None
    options: List[Any] = field(default_factory=list)
    editable: bool = True
    sensitive: bool = False
    category: str = ""

    def __post_init__(self) -> None:
        # 允许 value_type 传入字符串，但内部优先保持字符串形式以保持兼容性。
        # 校验留给 validator，model.py 本身不做严格枚举检查。
        if self.value_type is None:
            self.value_type = ValueType.STRING


@dataclass
class MetadataStatistics:
    """对象的运行时统计。

    示例：tokens、latency、memory_usage、version。
    """

    id: str
    name: str
    value: Any = None
    unit: str = ""
    timestamp: datetime | None = None


@dataclass
class MetadataAction:
    """对象可触发的操作。

    示例：Connect、Disconnect、Refresh、Install、Remove。
    """

    id: str
    label: str
    description: str = ""
    icon: str = ""
    enabled: bool = True


@dataclass
class MetadataDefinition:
    """对象的静态描述。

    这是 Cross-layer Metadata Contract 的根对象。Runtime、Workbench、Plugin、
    CLI、Web 都围绕它进行交互。
    """

    id: str
    type: str
    name: str
    description: str = ""
    icon: str = ""
    properties: List[MetadataProperty] = field(default_factory=list)
    statistics: List[MetadataStatistics] = field(default_factory=list)
    actions: List[MetadataAction] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
