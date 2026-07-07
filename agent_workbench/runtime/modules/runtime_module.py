"""agent_workbench/runtime/modules/runtime_module.py — Runtime 模块。

职责：
- Agent 生命周期管理（start / stop / restart）。
- Runtime 运行状态展示。
- 热加载入口。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class RuntimeModule(BaseRuntimeModule):
    """Runtime 运行态模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None

    @property
    def namespace(self) -> str:
        return "runtime"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """Runtime 配置变更：更新 orchestrstrator 决策策略等。"""
        if self._runtime is None:
            return
        policy = store.get("runtime.decision_policy", "rule_based")
        # 通过 AgentRuntime 更新 PlannerLoop 的 policy
        self._runtime.set_decision_policy(policy)

    def to_form(self) -> Dict[str, Any]:
        """返回 Runtime 配置表单。"""
        return {
            "title": "Runtime",
            "description": "Agent 运行时核心参数。",
            "fields": [
                {
                    "name": "use_orchestrator",
                    "type": "boolean",
                    "label": "Use Orchestrator",
                    "value": self._runtime.config.get("runtime.use_orchestrator", True) if self._runtime else True,
                },
                {
                    "name": "decision_policy",
                    "type": "select",
                    "label": "Decision Policy",
                    "options": ["rule_based"],
                    "value": self._runtime.config.get("runtime.decision_policy", "rule_based") if self._runtime else "rule_based",
                },
            ],
        }
