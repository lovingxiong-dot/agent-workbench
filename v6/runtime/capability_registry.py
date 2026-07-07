"""v6/runtime/capability_registry.py — Engine Capability Registry。

设计来源：V6.5 Runtime Foundation Layer Step 5.2。

核心原则：
- Capability Registry 负责按"能力需求"选择 Engine，不替代 EngineManager 的生命周期管理。
- 调用者从 `manager.execute("llm")` 升级为按需求查询：
  `{"capability": "text_generation", "priority": "high", "streaming": true}`。
- EngineDescriptor 中的 `capabilities` 列表是注册来源；Registry 只读描述符，不持有 Engine 实例。
- 匹配结果按得分排序，支持返回列表或单一最佳候选。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v6.runtime.engines.protocol import EngineDescriptor


@dataclass
class CapabilityQuery:
    """能力查询条件。

    字段说明：
    - capability: 必需能力名称，例如 "text_generation"。
    - priority: 优先级提示，例如 "high" / "normal" / "low"；仅用于打分，不影响匹配。
    - streaming: 是否要求支持流式输出。
    - metadata: 额外过滤条件，例如 {"provider": "openai"}。
    """

    capability: str
    priority: str = "normal"
    streaming: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityQuery":
        """从 dict 构造查询条件。"""
        return cls(
            capability=data.get("capability", ""),
            priority=data.get("priority", "normal"),
            streaming=bool(data.get("streaming", False)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class EngineMatch:
    """匹配结果。"""

    name: str
    score: float
    descriptor: EngineDescriptor


class CapabilityRegistry:
    """Engine 能力注册表。

    只维护 EngineDescriptor，不参与 Engine 实例的生命周期管理。
    """

    def __init__(self) -> None:
        self._descriptors: Dict[str, EngineDescriptor] = {}

    def register(self, descriptor: EngineDescriptor) -> None:
        """注册一个 EngineDescriptor。"""
        self._descriptors[descriptor.name] = descriptor

    def unregister(self, name: str) -> bool:
        """注销描述符。"""
        if name in self._descriptors:
            del self._descriptors[name]
            return True
        return False

    def clear(self) -> None:
        """清空注册表。"""
        self._descriptors.clear()

    def names(self) -> List[str]:
        """返回已注册 Engine 名称。"""
        return list(self._descriptors.keys())

    def capabilities(self) -> List[str]:
        """返回所有不重复的能力名称。"""
        caps: set[str] = set()
        for desc in self._descriptors.values():
            caps.update(desc.capabilities)
        return sorted(caps)

    def names_for(self, capability: str) -> List[str]:
        """返回具备指定能力的 Engine 名称列表。"""
        return [
            name
            for name, desc in self._descriptors.items()
            if capability in desc.capabilities
        ]

    def find(self, query: CapabilityQuery) -> List[EngineMatch]:
        """按查询条件返回匹配结果，按得分降序排列。"""
        matches: List[EngineMatch] = []
        for desc in self._descriptors.values():
            if query.capability not in desc.capabilities:
                continue
            if query.metadata:
                desc_meta = desc.metadata or {}
                if not all(desc_meta.get(k) == v for k, v in query.metadata.items()):
                    continue
            score = self._score(desc, query)
            matches.append(EngineMatch(name=desc.name, score=score, descriptor=desc))
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    def select(self, query: CapabilityQuery) -> Optional[str]:
        """返回最佳匹配的 Engine 名称；无匹配返回 None。"""
        matches = self.find(query)
        if not matches:
            return None
        return matches[0].name

    def _score(self, descriptor: EngineDescriptor, query: CapabilityQuery) -> float:
        """简单打分：基础分 + metadata 匹配加分 + streaming 支持加分。"""
        score = 1.0
        if query.priority == "high":
            score += 0.5
        elif query.priority == "low":
            score -= 0.2
        if query.streaming and descriptor.metadata.get("streaming"):
            score += 0.5
        if query.metadata:
            desc_meta = descriptor.metadata or {}
            matched = sum(1 for k, v in query.metadata.items() if desc_meta.get(k) == v)
            score += 0.3 * matched
        return score
