"""agent_workbench/runtime/manager/decision_manager.py — Decision Layer 默认 Manager。

设计约束：
- 实现 v6.runtime.manager.Manager 协议，可直接替换 ManagerRuntime 作为 WorkbenchController 默认 Manager。
- 内部流程：UserRequest → ManagerAI → Intent → CapabilityResolver → Policy → RuntimeDecision → Task。
- CHAT 模式仍生成 Task，但 capability 为 "chat" 且不携带 capability_chain；Orchestrator.dispatch 会跳过，
  此处保留 Task 生成以保证 Manager 协议兼容性。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from v6.runtime.manager import Manager
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

from agent_workbench.runtime.capability import CapabilityRegistry, CapabilityStep
from agent_workbench.runtime.decision import (
    CapabilityResolver,
    Interpreter,
    ManagerAI,
    Policy,
    RuntimeDecision,
    RuntimeMode,
)

if TYPE_CHECKING:
    from v6.runtime.event_bus import EventBus


class DecisionManager(Manager):
    """基于 Runtime Decision Layer 的 Manager 实现。"""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        event_bus: EventBus | None = None,
        interpreter: Interpreter | None = None,
        manager_ai: ManagerAI | None = None,
        resolver: CapabilityResolver | None = None,
        policy: Policy | None = None,
    ) -> None:
        self._registry = capability_registry
        self._event_bus = event_bus
        self._interpreter = interpreter or Interpreter()
        self._manager_ai = manager_ai or ManagerAI(interpreter=self._interpreter)
        self._resolver = resolver or CapabilityResolver(capability_registry)
        self._policy = policy or Policy()

    def decide(self, request: UserRequest) -> RuntimeDecision:
        """将 UserRequest 解析为 RuntimeDecision（供控制平面直接调度）。"""
        intent = self._manager_ai.understand(request)
        route, chain = self._resolver.resolve(intent)

        return RuntimeDecision(
            mode=intent.mode,
            intent=intent,
            route=route,
            capability_chain=[step.to_dict() for step in chain] if chain else None,
            payload={"text": request.text or ""},
        )

    def resolve(self, request: UserRequest) -> Task:
        """将 UserRequest 解析为 Task。

        流程：
        1. ManagerAI 生成 Intent。
        2. CapabilityResolver 将 Intent 解析为 (route, capability_chain)。
        3. Policy 检查通过。
        4. 构造 RuntimeDecision 并转换为 Task。
        """
        decision = self.decide(request)
        policy_result = self._policy.check(decision)
        if not policy_result.allowed:
            return self._build_blocked_task(request, decision, policy_result.reason)

        chain_data = decision.capability_chain
        chain = None
        if chain_data is not None:
            chain = [CapabilityStep.from_dict(item) for item in chain_data]

        return self._build_task(request, decision, chain)

    def _build_task(
        self,
        request: UserRequest,
        decision: RuntimeDecision,
        chain: list[CapabilityStep] | None,
    ) -> Task:
        """将 RuntimeDecision 转换为可提交的 Task。"""
        route = decision.route
        if route.startswith("capability://"):
            capability = route[len("capability://") :]
        else:
            capability = route

        metadata: dict[str, Any] = {"decision": decision.to_dict()}
        if chain is not None:
            from agent_workbench.runtime.capability import CapabilityChain

            metadata.update(CapabilityChain.to_metadata(chain))

        return Task(
            id=request.task_id,
            session_id=request.session_id,
            capability=capability,
            payload={"text": request.text or ""},
            metadata=metadata,
        )

    def _build_blocked_task(
        self,
        request: UserRequest,
        decision: RuntimeDecision,
        reason: str | None,
    ) -> Task:
        """Policy 拒绝时返回一个标记为 blocked 的 Task（保持 Manager 协议兼容）。"""
        return Task(
            id=request.task_id,
            session_id=request.session_id,
            capability="chat",
            payload={"text": request.text or "", "blocked": True, "reason": reason},
            metadata={"decision": decision.to_dict(), "blocked": True, "reason": reason},
        )
