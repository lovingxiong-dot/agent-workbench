"""tests/v6/test_v6_planner_loop.py — Planner Decision Loop Foundation 测试。"""
from __future__ import annotations

import time

from v6.runtime.capability_registry import CapabilityRegistry
from v6.runtime.context import RuntimeContext
from v6.runtime.decision import Decision, DecisionAction
from v6.runtime.decision_policy import RuleBasedDecisionPolicy
from v6.runtime.engine_manager import EngineManager
from v6.runtime.engines import LLMEngine, VisionEngine
from v6.runtime.enums import RuntimeState
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.planner_loop import PlannerLoop
from v6.runtime.task import ChatTask
from v6.runtime.types import ChatMessage


def build_planner_loop(
    event_bus: EventBus | None = None,
) -> tuple[PlannerLoop, EngineManager]:
    registry = CapabilityRegistry()
    manager = EngineManager(capability_registry=registry, event_bus=event_bus)
    manager.register(LLMEngine())
    manager.register(VisionEngine())
    policy = RuleBasedDecisionPolicy()
    loop = PlannerLoop(policy=policy, registry=registry, event_bus=event_bus)
    return loop, manager


def test_planner_loop_decides_execute_for_text() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "chat"
    ctx.messages.append(ChatMessage(role="user", content="hello"))

    decision = loop.plan(ctx)

    assert decision.action == DecisionAction.EXECUTE_ENGINE
    assert decision.target == "llm"
    assert "text_generation" in decision.reason


def test_planner_loop_decides_execute_for_image() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "chat"
    ctx.messages.append(ChatMessage(role="user", content="analyze this image"))

    decision = loop.plan(ctx)

    assert decision.action == DecisionAction.EXECUTE_ENGINE
    assert decision.target == "vision"


def test_planner_loop_decides_fail_when_no_capability() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "unknown"

    decision = loop.plan(ctx)

    assert decision.action == DecisionAction.FAIL


def test_planner_loop_decides_fail_when_no_engine_for_capability() -> None:
    registry = CapabilityRegistry()
    policy = RuleBasedDecisionPolicy()
    loop = PlannerLoop(policy=policy, registry=registry)
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "chat"
    ctx.messages.append(ChatMessage(role="user", content="hello"))

    decision = loop.plan(ctx)

    assert decision.action == DecisionAction.FAIL


def test_planner_loop_observation_includes_state() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "chat"
    ctx.status = RuntimeState.PLANNING

    observation = loop.observe(ctx)

    assert observation.task_id == ctx.task_id
    assert observation.task_type == "chat"
    assert observation.status == "planning"
    assert "text_generation" in observation.available_capabilities


def test_planner_loop_evaluate_returns_complete() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()

    decision = loop.evaluate(ctx, None)

    assert decision.action == DecisionAction.COMPLETE


def test_planner_loop_publishes_decision_event() -> None:
    bus = EventBus()
    bus.start()
    try:
        events = []

        def listener(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_STARTED, listener)

        loop, manager = build_planner_loop(event_bus=bus)
        ctx = RuntimeContext.new()
        ctx.metadata["task_type"] = "chat"
        ctx.messages.append(ChatMessage(role="user", content="hello"))

        loop.plan(ctx)
        time.sleep(0.1)

        decision_events = [e for e in events if e.source == "planner_loop"]
        assert len(decision_events) == 1
        assert decision_events[0].payload["phase"] == "decision"
        assert decision_events[0].payload["decision"]["target"] == "llm"
    finally:
        bus.stop()


def test_planner_loop_does_not_directly_write_trace() -> None:
    loop, manager = build_planner_loop()
    ctx = RuntimeContext.new()
    ctx.metadata["task_type"] = "chat"

    steps_before = len(ctx.trace.steps())
    loop.plan(ctx)
    steps_after = len(ctx.trace.steps())

    # PlannerLoop 本身不应调用 ctx.trace.add；如果 trace 增加，应来自 EventBus（本测试未连接 EventBus）
    assert steps_after == steps_before


def test_orchestrator_uses_planner_loop_to_select_vision_engine() -> None:
    bus = EventBus()
    bus.start()
    try:
        loop, manager = build_planner_loop(event_bus=bus)
        orchestrator = Orchestrator(
            event_bus=bus,
            engine_manager=manager,
            planner_loop=loop,
        )

        task = ChatTask(text="analyze this image")
        orchestrator.submit(task)
        time.sleep(0.2)

        assert orchestrator.state(task.task_id) == RuntimeState.COMPLETED
        ctx = orchestrator.context(task.task_id)
        assert ctx is not None
        # 验证 VisionEngine 被执行过
        vision_steps = ctx.trace.filter(node="engine:vision")
        assert len(vision_steps) == 1
    finally:
        bus.stop()
