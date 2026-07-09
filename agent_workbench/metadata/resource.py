"""agent_workbench/metadata/resource.py — Resource Metadata Contract.

Resource 表示 Capability 可以支配的执行目标或工具库存：
System / Python Env / IDE / CLI / Agent CLI。

Resource Metadata 与 Capability Metadata 使用同一套描述原语，但语义不同：
- Capability：What I can do（我会什么）。
- Resource：What I can use（我可以支配什么）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from agent_workbench.metadata.model import (
    MetadataAction,
    MetadataProperty,
    MetadataStatistics,
)


class ResourceType(str, Enum):
    """常见 Resource 类型。

    不限制自定义类型；Runtime / Plugin 可以返回任意字符串作为 Resource 类型。
    """

    SYSTEM = "system"
    PYTHON_ENV = "python_env"
    IDE = "ide"
    CLI = "cli"
    AGENT_CLI = "agent_cli"


@dataclass
class ResourceConnection:
    """Resource 的连接或定位信息。"""

    target: str = ""
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    working_dir: str = ""


@dataclass
class ResourceDefinition:
    """Resource 的静态描述。

    与 MetadataDefinition 共享同一套 Property / Statistics / Action 原语，
    但 type 是 ResourceType，并且包含 connection 字段描述如何连接该资源。
    """

    id: str
    type: str
    name: str
    description: str = ""
    icon: str = ""
    properties: List[MetadataProperty] = field(default_factory=list)
    statistics: List[MetadataStatistics] = field(default_factory=list)
    actions: List[MetadataAction] = field(default_factory=list)
    connection: ResourceConnection = field(default_factory=ResourceConnection)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
