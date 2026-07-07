"""agent_workbench/runtime/modules/strategy_module.py — Strategy 模块。

职责：
- Agent 行为策略。
- Planner 参数。
- Reflection 配置。
- 阈值配置。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ModuleMetadata,
    PropertyMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class StrategyModule(BaseRuntimeModule):
    """Strategy 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._planner: Dict[str, Any] = {}
        self._reflection: Dict[str, Any] = {}
        self._thresholds: Dict[str, Any] = {}

    @property
    def namespace(self) -> str:
        return "strategy"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新策略配置。"""
        self._planner = store.get("strategy.planner", {"policy": "rule_based", "threshold": 0.5})
        self._reflection = store.get("strategy.reflection", {"enabled": False, "rounds": 1})
        self._thresholds = store.get("strategy.thresholds", {"tool_confidence": 0.6})

    def get_threshold(self, name: str, default: float = 0.5) -> float:
        return self._thresholds.get(name, default)

    def metadata(self) -> ModuleMetadata:
        """返回 Strategy Capability Metadata。"""
        return ModuleMetadata(
            id="strategy",
            type="strategy",
            name="Strategy",
            description="管理 Agent 行为策略、Planner 参数与阈值。",
            icon="cog",
            properties=[
                PropertyMetadata(
                    name="planner.policy",
                    label="Planner Policy",
                    type="select",
                    value=self._planner.get("policy", "rule_based"),
                    options=["rule_based"],
                ),
                PropertyMetadata(
                    name="planner.threshold",
                    label="Planner Threshold",
                    type="number",
                    value=self._planner.get("threshold", 0.5),
                ),
                PropertyMetadata(
                    name="reflection.enabled",
                    label="Reflection Enabled",
                    type="boolean",
                    value=self._reflection.get("enabled", False),
                ),
                PropertyMetadata(
                    name="reflection.rounds",
                    label="Reflection Rounds",
                    type="number",
                    value=self._reflection.get("rounds", 1),
                ),
                PropertyMetadata(
                    name="thresholds.tool_confidence",
                    label="Tool Confidence Threshold",
                    type="number",
                    value=self._thresholds.get("tool_confidence", 0.6),
                ),
            ],
            statistics=[],
            actions=[],
        )
