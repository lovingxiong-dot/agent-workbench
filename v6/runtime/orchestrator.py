"""v6/runtime/orchestrator.py — Runtime Orchestration Foundation。

设计来源：V6.5 Runtime Foundation Layer Step 5.4。

核心原则：
- Orchestrator 位于 AgentRuntime 与 EngineManager/CapabilityRegistry/EventBus/Trace 之间，
  负责任务生命周期编排，而不是让 Planner 成为 Runtime 大脑。
- 第一版只做 Task Lifecycle State Machine + EventBus 驱动，不接真实 LLM，不做自治循环。
- Planner 只是 Orchestrator 调度的一种决策能力，未来可替换为 Rule Planner / Workflow Planner / Human Approval Planner。
- 所有状态迁移通过 RuntimeStateMachine 校验，非法迁移显式报错。
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.decision import Decision, DecisionAction
from v6.runtime.enums import RuntimeState
from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType
from v6.runtime.state_machine import RuntimeStateMachine, RuntimeStateTransitionError
from v6.runtime.task import ChatTask, Task
from v6.runtime.types import ChatMessage

if TYPE_CHECKING:
    from v6.runtime.engine_manager import EngineManager
    from v6.runtime.event_bus import EventBus
    from v6.runtime.planner_loop import PlannerLoop


class Orchestrator:
    """Runtime 编排器。

    职责：
    - 维护每个 Task 的生命周期状态。
    - 通过 EventBus 订阅和发布任务事件，驱动执行流程。
    - 使用 CapabilityRegistry + EngineManager 选择并执行 Engine。
    - 不直接调用 Trace；Trace 由 EventBus Trace Hook 自动记录。

    当前阶段（Foundation）不支持自治循环；只支持单阶段线性推进：
    CREATED -> PLANNING -> EXECUTING -> COMPLETED/FAILED。
    """

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        engine_manager: Optional["EngineManager"] = None,
        planner_loop: Optional["PlannerLoop"] = None,
    ) -> None:
        self._event_bus = event_bus
        self._engine_manager = engine_manager
        self._planner_loop = planner_loop
        self._state_machine = RuntimeStateMachine()
        self._task_states: Dict[str, RuntimeState] = {}
        self._contexts: Dict[str, RuntimeContext] = {}
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

    def submit(self, task: Task) -> str:
        """提交任务到 Orchestrator；发布 task.created 事件并开始编排。"""
        task_id = task.task_id
        with self._lock:
            self._task_states[task_id] = RuntimeState.CREATED
            ctx = self._ensure_context(task)
            self._contexts[task_id] = ctx

        self._publish(
            RuntimeEventType.TASK_STARTED,
            {"task_type": task.type, "session_id": task.session_id},
            task_id=task_id,
            source="orchestrator",
        )
        return task_id

    def state(self, task_id: str) -> Optional[RuntimeState]:
        """返回指定 Task 的当前生命周期状态。"""
        with self._lock:
            return self._task_states.get(task_id)

    def context(self, task_id: str) -> Optional[RuntimeContext]:
        """返回指定 Task 的 RuntimeContext。"""
        with self._lock:
            return self._contexts.get(task_id)

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

        # Foundation 阶段：直接发布 planning 事件，由订阅者处理；未订阅则进入 EXECUTING。
        self._publish(
            RuntimeEventType.TASK_STARTED,
            {"phase": "planning", "task_id": task_id},
            task_id=task_id,
            source="orchestrator",
        )

        # Foundation 简化：planning 完成后立即进入 EXECUTING。
        self._execute_task(task_id)

    def _execute_task(self, task_id: str) -> None:
        """将任务从 PLANNING 推进到 EXECUTING，并根据 PlannerLoop 的 Decision 执行。"""
        if not self.transition(task_id, RuntimeState.EXECUTING):
            return

        ctx = self.context(task_id)
        if ctx is None:
            return

        # Foundation 降级：无 EngineManager 时直接完成任务，避免决策失败。
        if self._engine_manager is None:
            self._complete_task(task_id, {"reason": "no engine manager in foundation mode"})
            return

        # Foundation 阶段：通过 PlannerLoop 做决策，而非硬编码能力选择。
        decision = self._make_decision(ctx)

        if decision.action == DecisionAction.FAIL:
            self._fail_task(task_id, {"reason": decision.reason, "decision": decision.to_dict()})
            return

        if decision.action == DecisionAction.COMPLETE:
            self._complete_task(task_id, {"reason": decision.reason, "decision": decision.to_dict()})
            return

        if decision.action == DecisionAction.WAIT:
            # Foundation 阶段不实现 WAIT 后续处理，直接完成。
            self._complete_task(task_id, {"reason": "wait not implemented in foundation", "decision": decision.to_dict()})
            return

        if decision.action != DecisionAction.EXECUTE_ENGINE or not decision.target:
            self._fail_task(task_id, {"reason": "invalid decision", "decision": decision.to_dict()})
            return

        engine_name = decision.target
        self._publish(
            RuntimeEventType.ENGINE_STARTED,
            {"engine": engine_name, "task_id": task_id, "decision": decision.to_dict()},
            task_id=task_id,
            source="orchestrator",
        )

        try:
            ctx.request = {"prompt": ctx.messages[-1].content if ctx.messages else ""}
            self._engine_manager.initialize_all(ctx)
            result = self._engine_manager.execute(engine_name, ctx)
            # execute 成功后会由 Engine 发布 engine.completed，Orchestrator 在该事件里推进状态。
            if result is not None and hasattr(result, "status"):
                ctx.result.status = result.status
        except Exception as exc:  # pragma: no cover - defensive
            self._fail_task(task_id, {"error": str(exc)})

    def _make_decision(self, ctx: RuntimeContext) -> Decision:
        """通过 PlannerLoop 或回退策略生成 Decision。"""
        if self._planner_loop is not None:
            return self._planner_loop.plan(ctx)

        # 无 PlannerLoop 时的最小回退：默认选 text_generation。
        if self._engine_manager is not None:
            try:
                engine_name = self._engine_manager.select_engine({"capability": "text_generation"})
                if engine_name:
                    return Decision.execute(
                        target=engine_name,
                        reason="fallback: default text_generation capability",
                    )
            except Exception:  # pragma: no cover - defensive
                traceback.print_exc()
        return Decision.fail(reason="no planner loop and no fallback engine available")

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
        if not self.transition(task_id, RuntimeState.COMPLETED):
            return
        self._publish(
            RuntimeEventType.TASK_COMPLETED,
            payload,
            task_id=task_id,
            source="orchestrator",
        )

    def _fail_task(self, task_id: str, payload: Dict[str, Any]) -> None:
        if not self.transition(task_id, RuntimeState.FAILED):
            return
        self._publish(
            RuntimeEventType.TASK_FAILED,
            payload,
            task_id=task_id,
            source="orchestrator",
        )

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
        """从 Task payload 提取或新建 RuntimeContext。

        若 Task 包含文本输入（如 ChatTask），自动加入 ctx.messages 并设置 task_type，
        供 PlannerLoop 基于内容进行能力匹配。
        """
        ctx = task.payload.get("ctx")
        if isinstance(ctx, RuntimeContext):
            return ctx

        ctx = RuntimeContext.new(
            task_id=task.task_id,
            session_id=task.session_id,
        )
        ctx.metadata["task_type"] = task.type
        text = ""
        if isinstance(task, ChatTask):
            text = task.text
        if not text:
            text = task.payload.get("text", "")
        if text:
            ctx.messages.append(ChatMessage(role="user", content=text))
        return ctx
