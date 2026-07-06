"""tests/v6/test_v6_runtime_kernel.py — Runtime Kernel 集成测试。

设计来源：V6.5 Runtime Foundation Layer Step 4。

目标：验证八大 Engine 空壳可被 EngineManager 统一发现、调度、追踪，
形成完整的 Task Execution Timeline。
"""
from __future__ import annotations

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
from v6.runtime.result import RuntimeResult
from v6.runtime.trace import RuntimeTrace


ALL_ENGINE_NAMES = ["llm", "tool", "memory", "planner", "workflow", "code", "vision", "knowledge"]


def build_manager(trace: RuntimeTrace | None = None) -> EngineManager:
    """构建已注册八大 Engine 的 EngineManager。"""
    manager = EngineManager(trace=trace)
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
