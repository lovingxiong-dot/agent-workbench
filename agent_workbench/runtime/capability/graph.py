"""agent_workbench/runtime/capability/graph.py — Capability Tree 结构（Commit 1 实现）。

Commit 0 仅提供类结构占位；所有方法体留空或抛 NotImplementedError，
避免提前实现 resolve/find 等复杂逻辑，确保接口先稳定。
"""
from __future__ import annotations

from agent_workbench.runtime.capability.model import CapabilityDefinition, CapabilityIntent, CapabilityMatch


class CapabilityNode:
    """能力树节点。

    - definition: 节点能力定义。
    - parent: 父节点引用。
    - children: 子节点列表。
    """

    def __init__(self, definition: CapabilityDefinition) -> None:
        self.definition = definition
        self.parent: CapabilityNode | None = None
        self.children: list[CapabilityNode] = []


class CapabilityRegistry:
    """能力注册表：管理 Capability Tree。

    Commit 0 仅声明接口；Commit 1 实现 register / get / lineage / children /
    roots / find / resolve / load_defaults 等行为。
    """

    def __init__(self) -> None:
        self._nodes: dict[str, CapabilityNode] = {}

    def register(self, definition: CapabilityDefinition) -> None:
        raise NotImplementedError

    def get(self, capability_id: str) -> CapabilityDefinition | None:
        raise NotImplementedError

    def lineage(self, capability_id: str) -> list[str]:
        raise NotImplementedError

    def children(self, capability_id: str) -> list[CapabilityDefinition]:
        raise NotImplementedError

    def roots(self) -> list[CapabilityDefinition]:
        raise NotImplementedError

    def find(self, intent: CapabilityIntent) -> list[CapabilityMatch]:
        raise NotImplementedError

    def resolve(self, intent: CapabilityIntent) -> CapabilityMatch:
        raise NotImplementedError

    def load_defaults(self) -> None:
        raise NotImplementedError
