"""agent_workbench/runtime/decision — Runtime Decision Layer。

设计约束：
- Decision Layer 是 Runtime Kernel Control Plane 的一部分，不是 Capability Module。
- 本包负责：Intent 解释 → 策略检查 → 路由决策 → Orchestrator 分发。
- 禁止反向依赖 capability / planner / service 实现；schema 中只保存协议对象。
"""
from __future__ import annotations

from agent_workbench.runtime.decision.interpreter import Interpreter
from agent_workbench.runtime.decision.manager_ai import ManagerAI
from agent_workbench.runtime.decision.policy import Policy, PolicyResult
from agent_workbench.runtime.decision.resolver import CapabilityResolver
from agent_workbench.runtime.decision.schema import (
    Intent,
    IntentError,
    IntentType,
    RuntimeDecision,
    RuntimeMode,
)

__all__ = [
    "CapabilityResolver",
    "Intent",
    "IntentError",
    "IntentType",
    "Interpreter",
    "ManagerAI",
    "Policy",
    "PolicyResult",
    "RuntimeDecision",
    "RuntimeMode",
]
