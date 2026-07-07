"""agent_workbench/runtime/modules/runtime_module.py — Runtime 模块。

职责：
- Agent 生命周期管理（start / stop / restart）。
- Runtime 运行状态展示。
- 热加载入口。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
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
        """Runtime 配置变更：更新 orchestrator 决策策略等。"""
        if self._runtime is None:
            return
        policy = store.get("runtime.decision_policy", "rule_based")
        # 通过 AgentRuntime 更新 PlannerLoop 的 policy
        self._runtime.set_decision_policy(policy)

    def metadata(self) -> ModuleMetadata:
        """返回 Runtime Capability Metadata。"""
        running = False
        if self._runtime is not None:
            running = getattr(self._runtime, "running", False)
        policy = self._runtime.config.get("runtime.decision_policy", "rule_based") if self._runtime else "rule_based"
        use_orch = self._runtime.config.get("runtime.use_orchestrator", True) if self._runtime else True
        return ModuleMetadata(
            id="runtime",
            type="runtime",
            name="Runtime",
            description="Agent 运行时核心参数与状态。",
            icon="play-circle",
            properties=[
                PropertyMetadata(
                    name="use_orchestrator",
                    label="Use Orchestrator",
                    type="boolean",
                    value=use_orch,
                ),
                PropertyMetadata(
                    name="decision_policy",
                    label="Decision Policy",
                    type="select",
                    value=policy,
                    options=["rule_based"],
                ),
            ],
            statistics=[
                StatisticMetadata(
                    name="status",
                    label="Status",
                    value="running" if running else "stopped",
                ),
            ],
            actions=[
                ActionMetadata(name="start", label="Start", icon="play"),
                ActionMetadata(name="stop", label="Stop", icon="square"),
                ActionMetadata(name="reload", label="Reload Config", icon="refresh"),
            ],
        )
