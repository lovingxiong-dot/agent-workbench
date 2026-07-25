"""v6/runtime/orchestrator.py — Runtime Orchestration Foundation。

设计来源：V6.5 Runtime Foundation Layer Step 5.4。
Phase 3.11-D v0.3: Parent-Child Execution + ExecutionRegistry + CancellationPropagationContext。

核心原则：
- Orchestrator 位于 AgentRuntime 与 EngineManager/CapabilityRegistry/EventBus/Trace 之间，
  负责任务生命周期编排，而不是让 Planner 成为 Runtime 大脑。
- 第一版只做 Task Lifecycle State Machine + EventBus 驱动，不接真实 LLM，不做自治循环。
- Planner 只是 Orchestrator 调度的一种决策能力，未来可替换为 Rule Planner / Workflow Planner / Human Approval Planner。
- 所有状态迁移通过 RuntimeStateMachine 校验，非法迁移显式报错。

Phase 3.11-D v0.3 集成：
- ExecutionRegistry 持有 topology（Decision #14）
- CancellationPropagationContext 取代字符串拼接（frozen + invariants）
- Deadline 模型取代 timeout（DEADLINE_EXCEEDED 统一命名）
- Cleanup safe predicate 守卫 lifecycle
- submit_child() 创建子 Execution
- cancel() Top-down DFS 后序传播
- _start_deadline_timer() 基于 deadline_at 触发 DEADLINE_EXCEEDED cancel
"""
from __future__ import annotations

import threading
import time
import traceback
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from v6.runtime.cancellation_propagation import (
    CancellationPropagationContext,
    CancellationPropagationLimitExceeded,
    PropagationType,
)
from v6.runtime.context import RuntimeContext
from v6.runtime.decision import Decision, DecisionAction
from v6.runtime.enums import ActivityState, LifecycleState, RuntimeState
from v6.runtime.execution_control import ExecutionControl, TaskCancelledError
from v6.runtime.execution_metadata import ExecutionMetadata
from v6.runtime.execution_registry import ExecutionRegistry

from agent_workbench.runtime.decision import RuntimeDecision, RuntimeMode
from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType
from v6.runtime.state_machine import RuntimeStateMachine, RuntimeStateTransitionError
from v6.runtime.task import ChatTask, Task
from v6.runtime.types import ChatMessage

from agent_workbench.runtime.capability import CapabilityChain

if TYPE_CHECKING:
    from agent_workbench.runtime.capability_router import CapabilityRouter
    from v6.runtime.engine_manager import EngineManager
    from v6.runtime.event_bus import EventBus
    from v6.runtime.planner_loop import PlannerLoop


class Orchestrator:
    """Runtime 编排器。

    Phase 3.11-D v0.3 职责扩展：
    - 维护 ExecutionRegistry（topology owner）
    - 通过 CancellationPropagationContext 传播取消
    - 基于 deadline_at 触发 DEADLINE_EXCEEDED cancel
    - 终态后通过 schedule_cleanup 注册延迟清理
    """

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        engine_manager: Optional["EngineManager"] = None,
        planner_loop: Optional["PlannerLoop"] = None,
        capability_router: Optional["CapabilityRouter"] = None,
    ) -> None:
        self._event_bus = event_bus
        self._engine_manager = engine_manager
        self._planner_loop = planner_loop
        self._capability_router = capability_router
        self._state_machine = RuntimeStateMachine()
        self._task_states: Dict[str, RuntimeState] = {}
        self._contexts: Dict[str, RuntimeContext] = {}
        # Phase 3.11-D v0.3: ExecutionRegistry topology owner
        self._execution_registry = ExecutionRegistry()
        self._lock = threading.Lock()
        self._subscribed = False
        self._subscribe()

    def _subscribe(self) -> None:
        """订阅任务生命周期事件。"""
        if self._event_bus is None or self._subscribed:
            return
        self._event_bus.subscribe(RuntimeEventType.TASK_STARTED, self._on_task_started)
        self._event_bus.subscribe(RuntimeEventType.ENGINE_COMPLETED, self._on_engine_completed)
        self._event_bus.subscribe(RuntimeEventType.ENGINE_FAILED, self._on_engine_failed)
        self._subscribed = True

    # ── Submit ────────────────────────────────────────────

    def submit(self, task: Task) -> str:
        """提交任务到 Orchestrator；注册 Trace Hook 并发布 task.started 事件。"""
        task_id = task.task_id
        with self._lock:
            self._task_states[task_id] = RuntimeState.CREATED
            ctx = self._ensure_context(task)
            self._contexts[task_id] = ctx

            # Phase 3.11-B: Execution Identity — 创建执行元数据
            # v0.3: 使用统一 attach_execution 入口保证 control ABI 不变量
            ctx.attach_execution(ExecutionMetadata(task_id=task_id))

            # Phase 3.11-B: 双状态模型 — CREATED → QUEUED
            ctx.set_lifecycle(LifecycleState.QUEUED)

        # 提前注册 Trace Hook，使 TASK_START 及后续事件都能写入 RuntimeTrace。
        if self._event_bus is not None and ctx.trace is not None:
            self._event_bus.add_trace_hook(task_id, ctx.trace)

        self._publish(
            RuntimeEventType.TASK_STARTED,
            {"task_type": task.type, "session_id": task.session_id},
            task_id=task_id,
            source="orchestrator",
        )
        return task_id

    def execute(self, task: Task) -> str:
        """兼容入口：保留旧版 execute(task) 调用，等价于 submit。"""
        return self.submit(task)

    def submit_child(
        self,
        parent_execution_id: str,
        task: Task,
        timeout: Optional[float] = None,
    ) -> str:
        """Phase 3.11-D v0.3: 创建子 Execution。

        Args:
            parent_execution_id: 父 Execution 的 execution_id
            task: 子 Task
            timeout: 可选 duration 秒数；转 deadline_at = now + timeout

        Returns:
            子 Task 的 task_id

        Raises:
            ValueError: parent 不存在或形成环路
        """
        with self._lock:
            parent_node = self._execution_registry.get(parent_execution_id)
            if parent_node is None:
                raise ValueError(
                    f"Parent execution not found: {parent_execution_id}"
                )

        # 1. 创建子 Execution（复用 submit）
        task_id = self.submit(task)

        with self._lock:
            ctx = self._contexts[task_id]
            if ctx.execution is None:
                # v0.3: 使用统一入口保证 control ABI 不变量
                ctx.attach_execution(ExecutionMetadata(task_id=task_id))
            ctx.execution.parent_execution_id = parent_execution_id

            # 2. 设置 deadline（若传入 timeout）
            if timeout is not None:
                from datetime import timedelta
                ctx.execution.deadline_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=timeout)
                )

            # 3. 计算 effective deadline = min(parent, child)
            parent_ctx = self._contexts.get(parent_node.task_id)
            effective_dl = self._compute_effective_deadline(parent_ctx, ctx)
            if effective_dl is not None:
                ctx.execution.deadline_at = effective_dl

            # 4. 注册到 ExecutionRegistry
            self._execution_registry.register(
                execution_id=ctx.execution.execution_id,
                task_id=task_id,
                parent_execution_id=parent_execution_id,
            )

        return task_id

    def dispatch(self, decision: RuntimeDecision) -> str | None:
        """Runtime Decision Layer 新入口。

        Commit 5 约束：
        - CHAT 模式不创建 Task，不进入 Runtime 执行层。
        - ACTION 模式生成 Task 并携带 capability_chain。
        - WORKFLOW 模式生成 Task 并携带 execution_plan，由现有 PlannerLoop 处理。
        """
        if decision.mode == RuntimeMode.CHAT:
            return None

        task = self._decision_to_task(decision)
        return self.submit(task)

    def _decision_to_task(self, decision: RuntimeDecision) -> Task:
        """将 RuntimeDecision 转换为 Task，保持与旧 execute(task) 路径兼容。"""
        route = decision.route
        if route.startswith("capability://"):
            capability = route[len("capability://"):]
        else:
            capability = route

        metadata: dict[str, Any] = {"decision": decision.to_dict()}
        if decision.capability_chain is not None:
            metadata["capability_chain"] = decision.capability_chain
        if decision.execution_plan is not None:
            metadata["execution_plan"] = decision.execution_plan

        return Task(
            capability=capability,
            payload={"text": decision.intent.raw_input},
            metadata=metadata,
            session_id=None,
        )

    # ── Query ─────────────────────────────────────────────

    def state(self, task_id: str) -> Optional[RuntimeState]:
        """返回指定 Task 的当前生命周期状态。"""
        with self._lock:
            return self._task_states.get(task_id)

    def context(self, task_id: str) -> Optional[RuntimeContext]:
        """返回指定 Task 的 RuntimeContext。"""
        with self._lock:
            return self._contexts.get(task_id)

    @property
    def execution_registry(self) -> ExecutionRegistry:
        """Phase 3.11-D v0.3: 暴露 ExecutionRegistry 用于查询。"""
        return self._execution_registry

    # ── Cancel (v0.3: CancellationPropagationContext) ─────

    def cancel(self, task_id: str, reason: str = "") -> bool:
        """取消指定任务（兼容旧 API：reason 字符串）。

        Phase 3.11-D v0.3:
        - 通过 CancellationPropagationContext 传播
        - 递归 cancel active descendants（DFS 后序）
        - 触发 Registry mark_terminated + schedule_cleanup
        - 终态守卫（ADR-014）
        """
        ctx = self._contexts.get(task_id)
        execution_id = (
            ctx.execution.execution_id if ctx and ctx.execution else task_id
        )
        propagation = CancellationPropagationContext.user_request(
            execution_id, reason
        )
        return self.cancel_with_propagation(task_id, propagation)

    def cancel_with_propagation(
        self,
        task_id: str,
        propagation: CancellationPropagationContext,
    ) -> bool:
        """Phase 3.11-D v0.3: 使用 CancellationPropagationContext 的取消。

        Args:
            task_id: 目标 Task ID
            propagation: 取消传播上下文

        Returns:
            True 若取消成功
        """
        with self._lock:
            ctx = self._contexts.get(task_id)
            if ctx is None:
                return False

            # ADR-014: 终态守卫
            if ctx.lifecycle in (
                LifecycleState.COMPLETED,
                LifecycleState.FAILED,
                LifecycleState.CANCELLED,
            ):
                return False

            # 触发取消令牌 + 迁移状态
            reason_str = propagation.to_reason_string()
            ctx.control.cancel(reason_str)
            current = self._task_states.get(task_id)
            if current is None:
                return False
            try:
                self._state_machine.transition(current, RuntimeState.CANCELLED)
                self._task_states[task_id] = RuntimeState.CANCELLED
                ctx.set_lifecycle(LifecycleState.CANCELLED, ActivityState.IDLE)
                if ctx.execution is not None:
                    ctx.execution.finished_at = datetime.now(timezone.utc)
            except RuntimeStateTransitionError:
                pass

            # 收集 active descendants（DFS 后序）
            child_task_ids: List[str] = []
            if ctx.execution is not None:
                descendants = self._execution_registry.get_descendants(
                    ctx.execution.execution_id
                )
                child_task_ids = [n.task_id for n in descendants]

            # Registry 生命周期
            if ctx.execution is not None:
                self._execution_registry.mark_terminated(ctx.execution.execution_id)
                self._execution_registry.schedule_cleanup(
                    ctx.execution.execution_id
                )

        # 发布 TASK_CANCELLED 事件
        self._publish(
            RuntimeEventType.TASK_CANCELLED,
            propagation.to_payload(),
            task_id=task_id,
            source="orchestrator",
        )
        if self._event_bus is not None:
            self._event_bus.remove_trace_hook(task_id)

        # 递归 cancel 子任务（chain 延长；extend() 内部 enforce depth）
        for child_task_id in child_task_ids:
            child_ctx = self._contexts.get(child_task_id)
            if child_ctx is None or child_ctx.execution is None:
                continue
            try:
                child_propagation = propagation.extend(
                    child_ctx.execution.execution_id
                )
                self.cancel_with_propagation(child_task_id, child_propagation)
            except CancellationPropagationLimitExceeded:
                # 深度超限，记录错误但不静默吞掉
                self._publish(
                    RuntimeEventType.TASK_FAILED,
                    {"reason": "cancellation_propagation_limit_exceeded"},
                    task_id=child_task_id,
                    source="orchestrator",
                )

        return True

    def _check_cancellation(self, ctx: RuntimeContext) -> None:
        """检查取消状态，若已取消则抛出 TaskCancelledError。"""
        ctx.control.raise_if_cancelled()

    # ── Deadline (v0.3: 替换 timeout) ─────────────────────

    def _start_deadline_timer(self, task_id: str, ctx: RuntimeContext) -> None:
        """Phase 3.11-D v0.3: 启动 deadline 定时器。

        若 ExecutionMetadata 设置了 deadline_at，启动守护线程
        在 deadline 到期后自动触发 cancel()，使用 DEADLINE_EXCEEDED 类型。
        """
        if ctx.execution is None or ctx.execution.deadline_at is None:
            return
        deadline = ctx.execution.deadline_at
        now = datetime.now(timezone.utc)

        if deadline <= now:
            # 已过期，立即 cancel
            self._cancel_with_deadline(task_id, ctx, deadline)
            return

        def _deadline_worker() -> None:
            remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                cancelled = ctx.control.cancellation.wait(timeout=remaining)
                if cancelled:
                    return  # 已被 cancel
            # deadline 到期
            self._cancel_with_deadline(task_id, ctx, deadline)

        threading.Thread(
            target=_deadline_worker,
            daemon=True,
            name=f"orch-deadline-{task_id[:8]}",
        ).start()

    def _cancel_with_deadline(
        self, task_id: str, ctx: RuntimeContext, deadline_at: datetime
    ) -> None:
        """v0.3: 使用 DEADLINE_EXCEEDED 类型的 cancel。"""
        if ctx.execution is None:
            return
        propagation = CancellationPropagationContext(
            propagation_type=PropagationType.DEADLINE_EXCEEDED,
            origin_execution_id=ctx.execution.execution_id,
            chain=(ctx.execution.execution_id,),
            reason=f"deadline exceeded at {deadline_at.isoformat()}",
            initiated_at=datetime.now(timezone.utc),
        )
        self.cancel_with_propagation(task_id, propagation)

    def _compute_effective_deadline(
        self,
        parent_ctx: Optional[RuntimeContext],
        child_ctx: RuntimeContext,
    ) -> Optional[datetime]:
        """v0.3: effective deadline = min(parent, child)。"""
        parent_dl = (
            parent_ctx.execution.deadline_at
            if (parent_ctx and parent_ctx.execution)
            else None
        )
        child_dl = (
            child_ctx.execution.deadline_at if child_ctx.execution else None
        )
        if parent_dl is None and child_dl is None:
            return None
        if parent_dl is None:
            return child_dl
        if child_dl is None:
            return parent_dl
        return min(parent_dl, child_dl)

    # ── Lifecycle Hooks ──────────────────────────────────

    def transition(self, task_id: str, to_state: RuntimeState) -> bool:
        """尝试将任务迁移到目标状态；非法迁移返回 False 并记录。"""
        with self._lock:
            current = self._task_states.get(task_id)
            if current is None:
                return False
            try:
                new_state = self._state_machine.transition(current, to_state)
                self._task_states[task_id] = new_state
                ctx = self._contexts.get(task_id)
                if ctx is not None:
                    ctx.status = new_state
                return True
            except RuntimeStateTransitionError:
                traceback.print_exc()
                return False

    def _on_task_started(self, event: RuntimeEvent) -> None:
        """Task 启动事件：进入 PLANNING 阶段。"""
        task_id = event.task_id
        current = self.state(task_id)
        if current != RuntimeState.CREATED:
            return

        if not self.transition(task_id, RuntimeState.PLANNING):
            return

        ctx = self.context(task_id)
        if ctx is None:
            return

        # Phase 3.11-B: 双状态模型 — QUEUED → PLANNING
        ctx.set_lifecycle(LifecycleState.PLANNING)

        # Phase 3.10: 在独立线程中执行任务，避免阻塞 EventBus Dispatch Loop。
        threading.Thread(
            target=self._execute_task,
            args=(task_id,),
            daemon=True,
            name=f"orch-exec-{task_id[:8]}",
        ).start()

    def _execute_task(self, task_id: str) -> None:
        """将任务从 PLANNING 推进到 EXECUTING。

        Phase 3.11-C/D: 添加取消检查、deadline 定时器和 TaskCancelledError 处理。
        """
        ctx = self.context(task_id)
        if ctx is None:
            return
        try:
            self._check_cancellation(ctx)
        except TaskCancelledError:
            current = self.state(task_id)
            if current not in (
                RuntimeState.CANCELLED,
                RuntimeState.COMPLETED,
                RuntimeState.FAILED,
            ):
                self._fail_task(task_id, {"reason": "cancelled before execution"})
            return

        if not self.transition(task_id, RuntimeState.EXECUTING):
            return

        # Phase 3.11-B: 双状态模型 — PLANNING → EXECUTING, activity → RUNNING
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        if ctx.execution is not None:
            ctx.execution.started_at = datetime.now(timezone.utc)

        # Phase 3.11-D v0.3: 启动 deadline 定时器（基于 deadline_at）
        self._start_deadline_timer(task_id, ctx)

        # Foundation 降级：无 EngineManager 时直接完成任务
        if self._engine_manager is None:
            self._complete_task(task_id, {"reason": "no engine manager in foundation mode"})
            return

        capability = self._resolve_capability(ctx)

        chain_steps = CapabilityChain.from_metadata(ctx.metadata)
        if chain_steps:
            self._execute_chain(task_id, ctx, chain_steps)
            return

        decision = self._make_decision(ctx, capability)

        if decision.action == DecisionAction.FAIL:
            self._fail_task(
                task_id,
                {"reason": decision.reason, "decision": decision.to_dict()},
            )
            return

        if decision.action == DecisionAction.COMPLETE:
            self._complete_task(
                task_id,
                {"reason": decision.reason, "decision": decision.to_dict()},
            )
            return

        if decision.action == DecisionAction.WAIT:
            self._complete_task(
                task_id,
                {
                    "reason": "wait not implemented in foundation",
                    "decision": decision.to_dict(),
                },
            )
            return

        if decision.action != DecisionAction.EXECUTE_ENGINE or not decision.target:
            self._fail_task(
                task_id,
                {"reason": "invalid decision", "decision": decision.to_dict()},
            )
            return

        engine_name = decision.target
        self._publish(
            RuntimeEventType.ENGINE_SELECTED,
            {
                "engine": engine_name,
                "capability": capability,
                "task_id": task_id,
                "decision": decision.to_dict(),
            },
            task_id=task_id,
            source="orchestrator",
        )

        try:
            self._check_cancellation(ctx)
            ctx.request = {
                "prompt": ctx.messages[-1].content if ctx.messages else ""
            }
            self._engine_manager.initialize_all(ctx)
            result = self._engine_manager.execute(engine_name, ctx)
            if result is not None and hasattr(result, "status"):
                ctx.result.status = result.status
        except TaskCancelledError:
            current = self.state(task_id)
            if current not in (
                RuntimeState.CANCELLED,
                RuntimeState.COMPLETED,
                RuntimeState.FAILED,
            ):
                self._fail_task(task_id, {"reason": "cancelled during execution"})
        except Exception as exc:  # pragma: no cover - defensive
            self._fail_task(task_id, {"error": str(exc)})

    def _execute_chain(
        self,
        task_id: str,
        ctx: RuntimeContext,
        chain_steps: list,
    ) -> None:
        """顺序执行 CapabilityChain 中的每个 Step。"""
        if self._engine_manager is None:
            self._fail_task(task_id, {"reason": "no engine manager for chain execution"})
            return

        for index, step in enumerate(chain_steps):
            try:
                self._check_cancellation(ctx)
            except TaskCancelledError:
                self._fail_task(
                    task_id,
                    {
                        "reason": f"cancelled before chain step {index}",
                        "capability_id": step.capability_id,
                    },
                )
                return
            ctx.phase = f"chain_step_{index}"
            self._publish(
                RuntimeEventType.CAPABILITY_CHAIN_STEP_STARTED,
                {
                    "step_index": index,
                    "capability_id": step.capability_id,
                    "engine_capability": step.engine_capability,
                    "total_steps": len(chain_steps),
                },
                task_id=task_id,
                source="orchestrator",
            )

            engine_capability = self._map_capability(step.engine_capability)
            try:
                engine_name = self._engine_manager.select_engine(
                    {"capability": engine_capability}
                )
            except Exception as exc:
                self._fail_task(
                    task_id,
                    {
                        "reason": f"chain step {index} engine selection failed",
                        "error": str(exc),
                        "capability_id": step.capability_id,
                    },
                )
                return

            if not engine_name:
                self._fail_task(
                    task_id,
                    {
                        "reason": f"chain step {index}: no engine for {step.engine_capability}",
                        "capability_id": step.capability_id,
                    },
                )
                return

            self._publish(
                RuntimeEventType.ENGINE_SELECTED,
                {
                    "engine": engine_name,
                    "capability": step.engine_capability,
                    "step_index": index,
                    "task_id": task_id,
                },
                task_id=task_id,
                source="orchestrator",
            )

            try:
                ctx.request = {
                    "step_index": index,
                    "capability_id": step.capability_id,
                    "engine_capability": step.engine_capability,
                }
                self._engine_manager.initialize_all(ctx)
                result = self._engine_manager.execute(engine_name, ctx)
                if result is not None and getattr(result, "status", None) == "failed":
                    self._fail_task(
                        task_id,
                        {
                            "reason": f"chain step {index} failed",
                            "capability_id": step.capability_id,
                        },
                    )
                    return
            except Exception as exc:
                self._fail_task(
                    task_id,
                    {
                        "reason": f"chain step {index} exception",
                        "error": str(exc),
                        "capability_id": step.capability_id,
                    },
                )
                return

        self._complete_task(task_id, {"reason": "capability chain completed"})

    def _resolve_capability(self, ctx: RuntimeContext) -> str:
        """通过 CapabilityRouter 解析能力；未注入时回退到 chat。"""
        if self._capability_router is not None:
            return self._capability_router.resolve(ctx, self._event_bus)
        if self._event_bus is not None:
            self._publish(
                RuntimeEventType.CAPABILITY_RESOLVED,
                {"capability": "chat", "reason": "fallback: no capability router"},
                task_id=ctx.task_id,
                source="orchestrator",
            )
        return "chat"

    def _make_decision(self, ctx: RuntimeContext, capability: str) -> Decision:
        """通过 PlannerLoop 或回退策略生成 Decision。"""
        if self._planner_loop is not None:
            return self._planner_loop.plan(ctx)

        engine_capability = self._map_capability(capability)
        if self._engine_manager is not None:
            try:
                engine_name = self._engine_manager.select_engine(
                    {"capability": engine_capability}
                )
                if engine_name:
                    return Decision.execute(
                        target=engine_name,
                        reason=f"fallback: default {engine_capability} capability",
                    )
            except Exception:  # pragma: no cover - defensive
                traceback.print_exc()
        return Decision.fail(reason="no planner loop and no fallback engine available")

    @staticmethod
    def _map_capability(capability: str) -> str:
        """将用户可见 capability 映射到 Engine capability。"""
        mapping = {
            "chat": "text_generation",
            "text": "text_generation",
            "tool": "tool_execution",
            "code_generation": "text_generation",
        }
        return mapping.get(capability, capability)

    def _on_engine_completed(self, event: RuntimeEvent) -> None:
        """Engine 完成事件：推进任务到 COMPLETED。"""
        task_id = event.task_id
        state = self.state(task_id)
        if state not in {RuntimeState.EXECUTING, RuntimeState.RUNNING}:
            return
        self._complete_task(task_id, event.payload)

    def _on_engine_failed(self, event: RuntimeEvent) -> None:
        """Engine 失败事件：推进任务到 FAILED。"""
        task_id = event.task_id
        state = self.state(task_id)
        if state not in {RuntimeState.EXECUTING, RuntimeState.RUNNING, RuntimeState.PLANNING}:
            return
        self._fail_task(task_id, event.payload)

    def _complete_task(self, task_id: str, payload: Dict[str, Any]) -> None:
        transitioned = self.transition(task_id, RuntimeState.COMPLETED)
        if transitioned:
            ctx = self.context(task_id)
            if ctx is not None:
                ctx.set_lifecycle(LifecycleState.COMPLETED, ActivityState.IDLE)
                if ctx.execution is not None:
                    ctx.execution.finished_at = datetime.now(timezone.utc)
            # Phase 3.11-D v0.3: Registry 生命周期标记
            if ctx is not None and ctx.execution is not None:
                self._execution_registry.mark_terminated(ctx.execution.execution_id)
                self._execution_registry.schedule_cleanup(
                    ctx.execution.execution_id
                )
            self._publish(
                RuntimeEventType.TASK_COMPLETED,
                payload,
                task_id=task_id,
                source="orchestrator",
            )
        if self._event_bus is not None:
            self._event_bus.remove_trace_hook(task_id)

    def _fail_task(self, task_id: str, payload: Dict[str, Any]) -> None:
        transitioned = self.transition(task_id, RuntimeState.FAILED)
        if transitioned:
            ctx = self.context(task_id)
            if ctx is not None:
                ctx.set_lifecycle(LifecycleState.FAILED, ActivityState.IDLE)
                if ctx.execution is not None:
                    ctx.execution.finished_at = datetime.now(timezone.utc)
            # Phase 3.11-D v0.3: Registry 生命周期标记
            if ctx is not None and ctx.execution is not None:
                self._execution_registry.mark_terminated(ctx.execution.execution_id)
                self._execution_registry.schedule_cleanup(
                    ctx.execution.execution_id
                )
            self._publish(
                RuntimeEventType.TASK_FAILED,
                payload,
                task_id=task_id,
                source="orchestrator",
            )
        if self._event_bus is not None:
            self._event_bus.remove_trace_hook(task_id)

    def shutdown(self) -> None:
        """v0.3: Orchestrator 销毁时清理 Registry。"""
        self._execution_registry.cleanup_all()

    def _publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        task_id: str,
        source: str,
    ) -> None:
        """通过 EventBus 发布事件；未注入 EventBus 时静默跳过。"""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            event_type=event_type,
            payload=payload,
            task_id=task_id,
            source=source,
        )

    @staticmethod
    def _ensure_context(task: Task) -> RuntimeContext:
        """从 Task payload 提取或新建 RuntimeContext。"""
        ctx = task.payload.get("ctx")
        if isinstance(ctx, RuntimeContext):
            return ctx

        ctx = RuntimeContext.new(
            task_id=task.task_id,
            session_id=task.session_id,
        )
        ctx.metadata.update(task.metadata or {})
        ctx.metadata["task_type"] = task.type
        text = ""
        if isinstance(task, ChatTask):
            text = task.text
        if not text:
            text = task.payload.get("text", "")
        if text:
            ctx.messages.append(ChatMessage(role="user", content=text))
        return ctx