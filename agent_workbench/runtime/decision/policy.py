"""agent_workbench/runtime/decision/policy.py — 执行前策略检查。

设计约束：
- 第一版只提供策略接口，不实现权限 / 计费 / 负载 / 用户体系。
- Policy 位于 Decision 之后、Orchestrator 之前，用于未来扩展。
"""
from __future__ import annotations

from dataclasses import dataclass

from agent_workbench.runtime.decision.schema import RuntimeDecision


@dataclass
class PolicyResult:
    """策略检查结果。"""

    allowed: bool
    reason: str | None = None


class Policy:
    """执行前策略检查器。"""

    def check(self, decision: RuntimeDecision) -> PolicyResult:
        """检查 Decision 是否允许执行。

        第一版默认放行；未来可在此接入权限 / 配额 / 安全策略。
        """
        return PolicyResult(allowed=True, reason="default allow in foundation")
