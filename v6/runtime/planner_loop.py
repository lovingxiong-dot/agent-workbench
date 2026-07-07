"""v6/runtime/planner_loop.py — Planner Decision Loop Foundation。

设计来源：V6.5 Runtime Foundation Layer Step 5.5。

核心原则：
- PlannerLoop 是 Runtime 决策机制，不是 Engine；它不替代 PlannerEngine（计划生成能力）。
- PlannerLoop 读取 RuntimeContext、Task State、Events、Capability Registry、Previous Trace，输出 Decision。
- 第一版使用规则策略，不引入 LLM / ReAct / LangChain / MCP / Prompt Chain。
- PlannerLoop 不直接写 Trace；决策事件通过 EventBus 发布，由 Trace Hook 记录。
- 未来可替换 DecisionPolicy 为 LLM-based / Rule-based / Human-approval 等。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from v6.runtime.decision import Decision, DecisionAction

if TYPE_CHECKING:
    from v6.runtime.capability_registry import CapabilityRegistry
    from v6.runtime.context import RuntimeContext
    from v6.runtime.decision_policy import DecisionPolicy
    from v6.runtime.event_bus import EventBus, RuntimeEvent


class Observation:
    """对当前 Runtime 状态的观察摘要。"""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        status: str,
        available_capabilities: List[str],
        trace_step_count: int,
        last_action: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.task_id = task_id
        self.task_type = task_type
        self.status = status
        self.available_capabilities = available_capabilities
        self.trace_step_count = trace_step_count
        self.last_action = last_action
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "available_capabilities": self.available_capabilities,
            "trace_step_count": self.trace_step_count,
            "last_action": self.last_action,
            "metadata": dict(self.metadata),
        }


class PlannerLoop:
    """Runtime 决策循环（Foundation）。

    当前为单次决策循环：observe -> decide -> emit decision event。
    未来可扩展为多轮循环：observe -> decide -> act -> evaluate -> next。
    """

    def __init__(
        self,
        policy: "DecisionPolicy",
        registry: "CapabilityRegistry",
        event_bus: Optional["EventBus"] = None,
    ) -> None:
        self._policy = policy
        self._registry = registry
        self._event_bus = event_bus

    def set_policy(self, policy: "DecisionPolicy") -> None:
        """运行时切换决策策略。"""
        self._policy = policy

    def observe(self, ctx: "RuntimeContext") -> Observation:
        """观察当前 Runtime 状态。"""
        last_action = ""
        last = ctx.trace.last()
        if last is not None:
            last_action = str(last.action)

        return Observation(
            task_id=ctx.task_id,
            task_type=ctx.metadata.get("task_type", ""),
            status=ctx.status.value if hasattr(ctx.status, "value") else str(ctx.status),
            available_capabilities=self._registry.capabilities(),
            trace_step_count=len(ctx.trace.steps()),
            last_action=last_action,
            metadata={"messages_count": len(ctx.messages)},
        )

    def decide(self, ctx: "RuntimeContext") -> Decision:
        """基于观察做出决策。"""
        return self._policy.decide(ctx, self._registry)

    def evaluate(
        self,
        ctx: "RuntimeContext",
        result: Any,
    ) -> Decision:
        """根据执行结果评估下一步（Foundation 阶段：直接 complete）。"""
        return Decision.complete(reason="foundation evaluate: execution finished")

    def plan(self, ctx: "RuntimeContext") -> Decision:
        """完整的单次规划：observe -> decide -> publish decision event。"""
        observation = self.observe(ctx)
        decision = self.decide(ctx)
        self._publish_decision(ctx.task_id, observation, decision)
        return decision

    def on_event(self, event: "RuntimeEvent") -> Optional["Decision"]:
        """EventBus 事件回调：根据事件类型触发规划。"""
        from v6.runtime.event_bus import RuntimeEventType

        if event.type == RuntimeEventType.TASK_STARTED:
            # 由 Orchestrator 在合适的时机调用 plan；这里仅做事件响应示例。
            return None
        return None

    def _publish_decision(
        self,
        task_id: str,
        observation: Observation,
        decision: Decision,
    ) -> None:
        """发布决策事件。"""
        if self._event_bus is None:
            return
        from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType

        self._event_bus.publish(
            RuntimeEventType.DECISION_PLANNED,
            {
                "phase": "decision",
                "observation": observation.to_dict(),
                "decision": decision.to_dict(),
            },
            task_id=task_id,
            source="planner_loop",
        )
