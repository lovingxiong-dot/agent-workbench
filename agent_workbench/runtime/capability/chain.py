"""agent_workbench/runtime/capability/chain.py — Capability Chain 静态链契约。

设计约束：
- CapabilityChain 是 list[CapabilityStep] 与 metadata dict 之间的序列化工具。
- Chain 只控制 Capability 执行顺序，不控制 Engine / Provider / Policy / Retry。
- 第一版仅支持静态链：链在 Manager 阶段一次性生成，Orchestrator 按顺序执行。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityStep:
    """能力链单步。

    - capability_id: 能力节点 id（如 coding.python.debugging）。
    - engine_capability: 该步映射到的 Engine capability。
    - payload_overrides: 对该步 payload 的覆盖项。
    - persona: 该步可选的 Persona 覆盖（以 dict 形式存放，便于序列化）。
    """

    capability_id: str
    engine_capability: str
    payload_overrides: dict[str, Any] = field(default_factory=dict)
    persona: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "engine_capability": self.engine_capability,
            "payload_overrides": dict(self.payload_overrides),
            "persona": dict(self.persona),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityStep:
        return cls(
            capability_id=data["capability_id"],
            engine_capability=data["engine_capability"],
            payload_overrides=dict(data.get("payload_overrides", {})),
            persona=dict(data.get("persona", {})),
        )


class CapabilityChain:
    """Capability Chain 序列化工具类。

    不保存 Runtime 状态，仅提供静态链与 metadata dict 之间的转换。
    """

    @staticmethod
    def from_metadata(metadata: dict[str, Any]) -> list[CapabilityStep] | None:
        """从 metadata dict 中提取能力链。

        若 metadata 中不存在 capability_chain 键，或为空列表，返回 None。
        """
        chain_data = metadata.get("capability_chain")
        if not chain_data:
            return None
        if not isinstance(chain_data, list):
            return None
        return [CapabilityStep.from_dict(item) for item in chain_data]

    @staticmethod
    def to_metadata(chain: list[CapabilityStep]) -> dict[str, Any]:
        """将能力链序列化为可写入 metadata 的 dict。"""
        return {"capability_chain": [step.to_dict() for step in chain]}
