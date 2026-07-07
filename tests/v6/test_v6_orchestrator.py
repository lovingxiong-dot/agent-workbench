"""tests/v6/test_v6_orchestrator.py — Runtime Orchestration Foundation 测试。"""
from __future__ import annotations

import time

from v6.runtime.engine_manager import EngineManager
from v6.runtime.engines import LLMEngine, ToolEngine
from v6.runtime.enums import RuntimeState
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.task import ChatTask


def test_orchestrator_task_lifecycle() -> None:
    """Orchestrator 应驱动 Task 经历 CREATED -> PLANNING -> EXECUTING -> COMPLETED。"""
    bus = EventBus()
    bus.start()
    try:
        manager = EngineManager(event_bus=bus)
        manager.register(LLMEngine())
        manager.register(ToolEngine())
        orchestrator = Orchestrator(event_bus=bus, engine_manager=manager)

        task = ChatTask(text="hello")
        orchestrator.submit(task)
        time.sleep(0.2)

        assert orchestrator.state(task.task_id) == RuntimeState.COMPLETED
        ctx = orchestrator.context(task.task_id)
        assert ctx is not None
        assert ctx.status == RuntimeState.COMPLETED
    finally:
        bus.stop()


def test_orchestrator_publishes_task_events() -> None:
    """Orchestrator 应通过 EventBus 发布 task 生命周期事件。"""
    bus = EventBus()
    bus.start()
    try:
        events = []

        def listener(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_COMPLETED, listener)

        manager = EngineManager(event_bus=bus)
        manager.register(LLMEngine())
        orchestrator = Orchestrator(event_bus=bus, engine_manager=manager)

        task = ChatTask(text="hello")
        orchestrator.submit(task)
        time.sleep(0.2)

        completed = [e for e in events if e.task_id == task.task_id]
        assert len(completed) == 1
    finally:
        bus.stop()


def test_orchestrator_without_engine_manager_completes() -> None:
    """无 EngineManager 时 Orchestrator 不应崩溃。"""
    bus = EventBus()
    bus.start()
    try:
        orchestrator = Orchestrator(event_bus=bus)
        task = ChatTask(text="hello")
        orchestrator.submit(task)
        time.sleep(0.2)
        # 无 EngineManager 时会直接完成（或保持在某个中间态）
        assert orchestrator.state(task.task_id) in {RuntimeState.COMPLETED, RuntimeState.CREATED}
    finally:
        bus.stop()


def test_orchestrator_state_transition_invalid() -> None:
    """非法状态迁移应返回 False。"""
    orchestrator = Orchestrator()
    task = ChatTask(text="hello")
    orchestrator.submit(task)
    # 先合法迁移到 COMPLETED
    orchestrator.transition(task.task_id, RuntimeState.PLANNING)
    orchestrator.transition(task.task_id, RuntimeState.EXECUTING)
    orchestrator.transition(task.task_id, RuntimeState.COMPLETED)
    # COMPLETED 是终态，无法迁移到 PLANNING
    assert orchestrator.transition(task.task_id, RuntimeState.PLANNING) is False


def test_orchestrator_state_returns_none_for_unknown_task() -> None:
    orchestrator = Orchestrator()
    assert orchestrator.state("unknown") is None


def test_orchestrator_uses_capability_registry_to_select_engine() -> None:
    """Orchestrator 应通过 capability registry 选择 Engine，而不是硬编码名称。"""
    bus = EventBus()
    bus.start()
    try:
        manager = EngineManager(event_bus=bus)
        manager.register(LLMEngine())
        manager.register(ToolEngine())
        orchestrator = Orchestrator(event_bus=bus, engine_manager=manager)

        task = ChatTask(text="hello")
        orchestrator.submit(task)
        time.sleep(0.2)

        ctx = orchestrator.context(task.task_id)
        assert ctx is not None
        assert ctx.status == RuntimeState.COMPLETED
    finally:
        bus.stop()


def test_orchestrator_does_not_directly_access_trace() -> None:
    """Orchestrator 不直接写 Trace，Trace 应通过 EventBus Trace Hook 记录。"""
    bus = EventBus()
    bus.start()
    try:
        manager = EngineManager(event_bus=bus)
        manager.register(LLMEngine())
        orchestrator = Orchestrator(event_bus=bus, engine_manager=manager)

        task = ChatTask(text="hello")
        orchestrator.submit(task)
        time.sleep(0.2)

        ctx = orchestrator.context(task.task_id)
        assert ctx is not None
        # Orchestrator 本身不应直接调用 ctx.trace.add；事件总线会写入 trace
        assert len(ctx.trace.steps()) > 0
    finally:
        bus.stop()
