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

    def to_form(self) -> Dict[str, Any]:
        """返回 Strategy 配置表单。"""
        return {
            "title": "Strategy",
            "description": "管理 Agent 行为策略、Planner 参数与阈值。",
            "fields": [
                {
                    "name": "planner_policy",
                    "type": "select",
                    "label": "Planner Policy",
                    "options": ["rule_based"],
                    "value": self._planner.get("policy", "rule_based"),
                },
                {
                    "name": "planner_threshold",
                    "type": "float",
                    "label": "Planner Threshold",
                    "min": 0.0,
                    "max": 1.0,
                    "value": self._planner.get("threshold", 0.5),
                },
                {
                    "name": "reflection_enabled",
                    "type": "boolean",
                    "label": "Reflection Enabled",
                    "value": self._reflection.get("enabled", False),
                },
                {
                    "name": "reflection_rounds",
                    "type": "integer",
                    "label": "Reflection Rounds",
                    "min": 0,
                    "max": 10,
                    "value": self._reflection.get("rounds", 1),
                },
                {
                    "name": "tool_confidence",
                    "type": "float",
                    "label": "Tool Confidence Threshold",
                    "min": 0.0,
                    "max": 1.0,
                    "value": self._thresholds.get("tool_confidence", 0.6),
                },
            ],
        }
