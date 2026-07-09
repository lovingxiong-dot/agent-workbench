"""agent_workbench/metadata/types.py — Public type aliases and enums.

These types are part of the Cross-layer Metadata Contract and must remain
stable across V6 releases.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Literal, TypeAlias


class ValueType(str, Enum):
    """平台无关的值类型。

    不映射到任何 UI 控件。具体控件选择由 Workbench Layer 的 Schema 或
    PresentationModel 决定。
    """

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    SECRET = "secret"
    PATH = "path"
    ENUM = "enum"
    TEXT = "text"
    JSON = "json"


class MetadataType(str, Enum):
    """常见的 Metadata 对象类型。

    这个枚举只提供常见值，不限制自定义类型。Runtime 或 Plugin 可以返回
    任意字符串作为 `MetadataDefinition.type`。
    """

    RUNTIME = "runtime"
    SESSION = "session"
    CONFIG = "config"
    MODEL = "model"
    PROVIDER = "provider"
    MCP = "mcp"
    SKILL = "skill"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    MEMORY = "memory"
    TOOL = "tool"
    TRACE = "trace"
    STRATEGY = "strategy"
    PROFILE = "profile"
    RESOURCE = "resource"


# 兼容旧代码的字符串别名。新代码优先使用 ValueType / MetadataType 枚举。
LegacyValueType: TypeAlias = Literal[
    "string", "number", "boolean", "select", "textarea", "json"
]
