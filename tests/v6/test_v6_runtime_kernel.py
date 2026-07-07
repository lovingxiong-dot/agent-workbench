"""tests/v6/test_v6_runtime_kernel.py — Runtime Kernel 集成测试。

设计来源：V6.5 Runtime Foundation Layer Step 4 / Step 5.1。

目标：验证八大 Engine 空壳可被 EngineManager 统一发现、调度、追踪，
形成完整的 Task Execution Timeline；验证 EventBus 作为 Runtime 神经系统，
Engine 事件通过 Trace Hook 写入 RuntimeTrace。
"""
from __future__ import annotations

import time

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_manager import EngineManager
from v6.runtime.engine_state import EngineState
from v6.runtime.engines import (
    CodeEngine,
    KnowledgeEngine,
    LLMEngine,
    MemoryEngine,
    PlannerEngine,
    ToolEngine,
    VisionEngine,
    WorkflowEngine,
)
from v6.runtime.engines.planner import PlannerEngine
from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.result import RuntimeResult
from v6.runtime.trace import RuntimeTrace


ALL_ENGINE_NAMES = ["llm", "tool", "memory", "planner", "workflow", "code", "vision", "knowledge"]


def build_manager(
    trace: RuntimeTrace | None = None,
    event_bus: EventBus | None = None,
) -> EngineManager:
    """构建已注册八大 Engine 的 EngineManager。"""
    manager = EngineManager(trace=trace, event_bus=event_bus)
    manager.register(LLMEngine())
    manager.register(ToolEngine())
    manager.register(MemoryEngine())
    manager.register(WorkflowEngine())
    manager.register(CodeEngine())
    manager.register(VisionEngine())
    manager.register(KnowledgeEngine())
    # Planner 需要 EngineManager 注入以编排 LLM/Tool
    manager.register(PlannerEngine(manager=manager))
    return manager


def test_manager_lists_all_engines() -> None:
    manager = build_manager()
    names = manager.names()
    for name in ALL_ENGINE_NAMES:
        assert name in names
    assert len(names) == len(ALL_ENGINE_NAMES)


def test_all_engines_have_descriptors() -> None:
    manager = build_manager()
    for name in ALL_ENGINE_NAMES:
        desc = manager.descriptor(name)
        assert desc is not None
        assert desc.name == name
        assert desc.instance is manager.get(name)


def test_all_engines_lifecycle_consistency() -> None:
    """验证所有 Engine 生命周期统一：CREATED -> LOADED -> READY -> STOPPED。"""
    manager = build_manager()
    ctx = RuntimeContext.new()

    manager.initialize_all(ctx)

    for name in ALL_ENGINE_NAMES:
        assert manager.state(name) == EngineState.READY, f"{name} should be READY"

    manager.shutdown_all()

    for name in ALL_ENGINE_NAMES:
        assert manager.state(name) == EngineState.STOPPED, f"{name} should be STOPPED"


def test_all_engines_execute_return_runtime_result() -> None:
    trace = RuntimeTrace()
    manager = build_manager(trace=trace)
    ctx = RuntimeContext.new()
    manager.initialize_all(ctx)

    for name in ALL_ENGINE_NAMES:
        ctx.request = {"test": name}
        result = manager.execute(name, ctx)
        assert isinstance(result, RuntimeResult), f"{name} should return RuntimeResult"
        assert result.status == "placeholder"
        assert result.extra["engine"] == name


def test_engine_trace_records_execution_timeline() -> None:
    trace = RuntimeTrace()
    manager = build_manager(trace=trace)
    ctx = RuntimeContext.new()
    manager.initialize_all(ctx)

    ctx.request = {"prompt": "hello"}
    manager.execute("llm", ctx)

    steps = trace.filter(node="engine:llm")
    assert len(steps) == 1
    step = steps[0]
    assert step.action == "engine_start"
    assert step.payload["request_type"] == "dict"
    assert step.duration_ms >= 0.0


def test_planner_orchestrates_llm_and_tool() -> None:
    trace = RuntimeTrace()
    manager = build_manager(trace=trace)
    ctx = RuntimeContext.new()
    manager.initialize_all(ctx)

    ctx.request = {"goal": "say hello"}
    result = manager.execute("planner", ctx)

    assert isinstance(result, RuntimeResult)
    assert result.extra["engine"] == "planner"
    assert "llm" in result.extra
    assert "tool" in result.extra

    # Planner 编排应产生 engine:llm 与 engine:tool 两个 TraceStep
    llm_steps = trace.filter(node="engine:llm")
    tool_steps = trace.filter(node="engine:tool")
    assert len(llm_steps) == 1
    assert len(tool_steps) == 1


def test_planner_without_manager_returns_placeholder() -> None:
    manager = EngineManager()
    manager.register(PlannerEngine())  # 无 manager 注入
    ctx = RuntimeContext.new()
    manager.load("planner")
    manager.initialize("planner", ctx)

    ctx.request = {"goal": "test"}
    result = manager.execute("planner", ctx)

    assert isinstance(result, RuntimeResult)
    assert result.extra["engine"] == "planner"
    assert "llm" not in result.extra


def test_engine_manager_wires_event_bus_to_engines() -> None:
    """EngineManager 注册 Engine 时应自动注入 EventBus。"""
    bus = EventBus()
    manager = build_manager(event_bus=bus)

    llm = manager.get("llm")
    assert llm is not None
    assert llm._event_bus is bus


def test_engine_publishes_lifecycle_events_to_trace() -> None:
    """Engine 执行时通过 EventBus 发布 started / completed 事件，并写入 Trace。"""
    bus = EventBus()
    bus.start()
    try:
        trace = RuntimeTrace()
        manager = build_manager(event_bus=bus)
        ctx = RuntimeContext.new()
        bus.add_trace_hook(ctx.task_id, trace)
        manager.initialize_all(ctx)

        ctx.request = {"prompt": "hello"}
        manager.execute("llm", ctx)

        # 等待后台事件分发线程处理 engine.completed
        time.sleep(0.1)

        started = trace.filter(action=TraceEvent.ENGINE_START.value)
        completed = trace.filter(action=TraceEvent.ENGINE_END.value)
        assert len(started) == 1
        assert len(completed) == 1
        assert started[0].node == "engine:llm"
        assert completed[0].node == "engine:llm"
    finally:
        bus.stop()


def test_event_bus_prevents_engine_direct_trace_calls() -> None:
    """Engine 不直接调用 ctx.trace.add；事件通过 EventBus 路由。"""
    bus = EventBus()
    bus.start()
    try:
        trace = RuntimeTrace()
        manager = build_manager(event_bus=bus)
        ctx = RuntimeContext.new()
        bus.add_trace_hook(ctx.task_id, trace)
        manager.initialize_all(ctx)

        # 清空 trace，确保只有事件总线写入
        trace.clear()
        ctx.request = {"prompt": "hello"}
        manager.execute("llm", ctx)

        # 等待后台事件分发线程处理
        time.sleep(0.1)

        # 至少应有 engine.started / engine.completed 两个事件来自 EventBus
        assert len(trace.steps()) >= 2
        assert all(step.node.startswith("engine:") for step in trace.steps())
    finally:
        bus.stop()
