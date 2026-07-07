"""v6/runtime/decision_policy.py — Runtime 决策策略。

设计来源：V6.5 Runtime Foundation Layer Step 5.5。

核心原则：
- DecisionPolicy 封装"如何根据当前上下文做决策"，与 PlannerLoop 的执行循环分离。
- 第一版使用规则策略，不引入 LLM / ReAct / LangChain / MCP / Prompt Chain。
- 策略只读 RuntimeContext 和 CapabilityRegistry，不写 Trace、不调用 Engine。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from v6.runtime.capability_registry import CapabilityQuery
from v6.runtime.decision import Decision, DecisionAction

if TYPE_CHECKING:
    from v6.runtime.capability_registry import CapabilityRegistry
    from v6.runtime.context import RuntimeContext


class DecisionPolicy:
    """决策策略基类。"""

    def decide(
        self,
        ctx: "RuntimeContext",
        registry: "CapabilityRegistry",
    ) -> Decision:
        """根据上下文和注册表做出决策。"""
        raise NotImplementedError


class RuleBasedDecisionPolicy(DecisionPolicy):
    """基于规则的决策策略（Foundation 阶段）。

    规则示例：
    - task.type 包含 image/vision → 选择 image_understanding。
    - task.type 为 chat/code/analyze → 选择 text_generation。
    - 无匹配 capability → FAIL。
    """

    def decide(
        self,
        ctx: "RuntimeContext",
        registry: "CapabilityRegistry",
    ) -> Decision:
        capability = self._infer_capability(ctx)
        if capability is None:
            return Decision.fail(reason=f"no capability matched for task type: {ctx.metadata.get('task_type', '')}")

        candidates = registry.find(CapabilityQuery(capability=capability))
        if not candidates:
            return Decision.fail(reason=f"no engine registered for capability: {capability}")

        best = candidates[0]
        return Decision.execute(
            target=best.name,
            reason=f"capability '{capability}' matched engine '{best.name}' via rule policy",
            metadata={"capability": capability, "score": best.score},
        )

    def _infer_capability(self, ctx: "RuntimeContext") -> Optional[str]:
        """根据上下文推断所需能力。"""
        task_type = ctx.metadata.get("task_type", "")
        text = ""
        if ctx.messages:
            text = ctx.messages[-1].content.lower()
        elif ctx.request is not None and isinstance(ctx.request, dict):
            text = str(ctx.request.get("prompt", "")).lower()

        combined = f"{task_type} {text}".lower()

        if any(k in combined for k in {"image", "vision", "picture", "photo"}):
            return "image_understanding"
        if any(k in combined for k in {"code", "program", "function"}):
            return "code_generation"
        if any(k in combined for k in {"tool", "search", "query"}):
            return "tool_execution"
        if any(k in combined for k in {"chat", "analyze", "text", "hello"}):
            return "text_generation"

        return None
