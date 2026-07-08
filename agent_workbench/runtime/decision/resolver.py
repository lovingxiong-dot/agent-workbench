"""agent_workbench/runtime/decision/resolver.py — Intent → Capability Chain。

设计约束：
- 确定性路由，不是 LLM。
- 通过 CapabilityRegistry 查询能力定义，复用 Commit 4 的 leaves() 生成静态链。
- 不重新实现 Chain 逻辑；只负责把 Intent 映射到 capability_id。
"""
from __future__ import annotations

from agent_workbench.runtime.capability import CapabilityRegistry, CapabilityStep
from agent_workbench.runtime.decision.schema import Intent, IntentType, RuntimeMode


class CapabilityResolver:
    """Intent 到 Capability Chain 的解析器。"""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def resolve(self, intent: Intent) -> tuple[str, list[CapabilityStep] | None]:
        """将 Intent 解析为 (route, capability_chain)。

        返回：
            route: 能力路由标识，例如 "capability://coding.python"。
            capability_chain: 静态 CapabilityChain；CHAT 等无需执行链的场景返回 None。
        """
        if intent.mode == RuntimeMode.CHAT:
            return "capability://chat", None

        capability_id = self._map_intent_to_capability(intent)
        if capability_id is None:
            return "capability://chat", None

        chain = self._build_chain(capability_id)
        return f"capability://{capability_id}", chain

    def _map_intent_to_capability(self, intent: Intent) -> str | None:
        """根据 Intent 类型与实体映射到能力 id。"""
        if intent.mode != RuntimeMode.ACTION:
            return None

        entities = intent.entities
        intent_type = intent.type

        if intent_type == IntentType.CREATE_ARTIFACT:
            artifact = entities.get("artifact", "").lower()
            if artifact == "image":
                return "image_generation"
            return "chat"

        if intent_type == IntentType.ANALYZE:
            language = entities.get("language", "").lower()
            if language == "python":
                return "coding.python"
            return "analyze"

        if intent_type == IntentType.EXECUTE_ACTION:
            action = entities.get("action", "").lower()
            if action and self._registry.get(action) is not None:
                return action
            return "tool"

        if intent_type == IntentType.SEARCH:
            return "search"

        if intent_type == IntentType.TRANSFORM:
            return "transform"

        return "chat"

    def _build_chain(self, capability_id: str) -> list[CapabilityStep] | None:
        """复用 Registry leaves() 生成静态能力链。"""
        definition = self._registry.get(capability_id)
        if definition is None:
            return None

        leaves = self._registry.leaves(capability_id)
        if not leaves:
            # 单叶子能力直接执行自身。
            return [
                CapabilityStep(
                    capability_id=capability_id,
                    engine_capability=definition.engine_capability or capability_id,
                )
            ]

        if len(leaves) == 1 and leaves[0].id == capability_id:
            return [
                CapabilityStep(
                    capability_id=capability_id,
                    engine_capability=leaves[0].engine_capability or capability_id,
                )
            ]

        return [
            CapabilityStep(
                capability_id=leaf.id,
                engine_capability=leaf.engine_capability or leaf.id,
            )
            for leaf in leaves
        ]
