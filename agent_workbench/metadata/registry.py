"""agent_workbench/metadata/registry.py — Metadata Registry.

A lightweight index for MetadataDefinition objects. Runtime modules, plugins,
and Workbench components can register definitions here so that consumers do not
need to maintain their own lists.

The registry does NOT depend on Runtime. It only knows about
`MetadataDefinition` objects.
"""
from __future__ import annotations

from typing import Dict, List

from agent_workbench.metadata.errors import MetadataNotFoundError
from agent_workbench.metadata.model import MetadataDefinition


class MetadataRegistry:
    """MetadataDefinition 的轻量索引。

    线程安全不是本类的职责；调用方负责在单线程或受控环境中使用。
    """

    def __init__(self) -> None:
        self._definitions: Dict[str, MetadataDefinition] = {}

    def register(self, definition: MetadataDefinition) -> None:
        """注册或更新一个 MetadataDefinition。"""
        self._definitions[definition.id] = definition

    def get(self, definition_id: str) -> MetadataDefinition | None:
        """按 id 获取 MetadataDefinition，不存在时返回 None。"""
        return self._definitions.get(definition_id)

    def require(self, definition_id: str) -> MetadataDefinition:
        """按 id 获取 MetadataDefinition，不存在时抛出 MetadataNotFoundError。"""
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise MetadataNotFoundError(
                f"MetadataDefinition not found: {definition_id}"
            )
        return definition

    def all(self) -> List[MetadataDefinition]:
        """返回所有已注册的 MetadataDefinition。"""
        return list(self._definitions.values())

    def unregister(self, definition_id: str) -> bool:
        """移除指定 id 的 MetadataDefinition。存在时返回 True，否则 False。"""
        return self._definitions.pop(definition_id, None) is not None

    def clear(self) -> None:
        """清空所有注册项。"""
        self._definitions.clear()

    def __len__(self) -> int:
        return len(self._definitions)

    def __contains__(self, definition_id: str) -> bool:
        return definition_id in self._definitions
