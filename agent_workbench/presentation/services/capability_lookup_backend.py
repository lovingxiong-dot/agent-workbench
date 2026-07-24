"""presentation/services/capability_lookup_backend.py — Runtime Capability Lookup Adapter。

v6.10.0-alpha Skill System Foundation。

职责：
  - 适配 Runtime CapabilityRegistry / ToolRegistry 为 RuntimeCapabilityLookup Protocol
  - 让 WorkbenchSkillRegistry.verify_composition() 不直接依赖 Runtime 类

边界：
  - 不修改 CapabilityRegistry / ToolRegistry
  - 仅做数据投影（list_capability_ids / list_tool_ids）
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.services.skill_service import RuntimeCapabilityLookup


class CapabilityRegistryBackend:
    """CapabilityRegistry → RuntimeCapabilityLookup Adapter。

    RuntimeCapabilityLookup.list_capability_ids()
      → CapabilityRegistry.roots() / all nodes 的 capability id
    """

    def __init__(self, capability_registry) -> None:
        self._registry = capability_registry

    def list_capability_ids(self) -> List[str]:
        """列出所有 Capability ID。

        Note: CapabilityRegistry 没有直接的 list_all()，
        通过遍历返回所有节点 ID。
        """
        ids = []
        if hasattr(self._registry, "_nodes"):
            ids.extend(self._registry._nodes.keys())
        elif hasattr(self._registry, "roots"):
            # 回退方案：遍历 roots 的子树
            for root in self._registry.roots():
                ids.extend(self._collect_ids(root))
        return ids

    def _collect_ids(self, node) -> List[str]:
        ids = []
        stack = [node]
        while stack:
            current = stack.pop()
            if hasattr(current, "definition") and hasattr(current.definition, "id"):
                ids.append(current.definition.id)
            if hasattr(current, "children"):
                stack.extend(current.children)
        return ids

    def list_tool_ids(self) -> List[str]:
        """列出所有 Tool ID。"""
        return []  # Tool ID 由 ToolModuleBackend 提供


class ToolIdsBackend:
    """ToolModule → list_tool_ids 提供者。

    组合到 RuntimeCapabilityLookup 实现。
    """

    def __init__(self, tool_module) -> None:
        self._module = tool_module

    def list_tool_ids(self) -> List[str]:
        """列出所有 Tool ID。"""
        return [t.get("name", "") for t in self._module.list_tools()]


class CompositeCapabilityLookup:
    """组合 CapabilityRegistry + ToolModule 的 Capability Lookup。

    RuntimeCapabilityLookup 的实现：
      - list_capability_ids() ← CapabilityRegistryBackend
      - list_tool_ids()       ← ToolIdsBackend
    """

    def __init__(self, capability_backend: CapabilityRegistryBackend, tool_backend: ToolIdsBackend) -> None:
        self._capability = capability_backend
        self._tool = tool_backend

    def list_capability_ids(self) -> List[str]:
        return self._capability.list_capability_ids()

    def list_tool_ids(self) -> List[str]:
        return self._tool.list_tool_ids()