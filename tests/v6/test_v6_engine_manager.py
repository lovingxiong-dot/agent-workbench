"""tests/v6/test_v6_engine_manager.py — EngineManager 生命周期与调度测试。"""
from __future__ import annotations

from typing import Any

import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_manager import EngineManager
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.protocol import EngineDescriptor, EngineNotReadyError
from v6.runtime.trace import RuntimeTrace


class FakeEngine:
    """符合 Engine Protocol 的最小 Engine 实现。"""

    name = "fake"

    def __init__(self) -> None:
        self.loaded = False
        self.initialized = False
        self.executed = False
        self.shut_down = False
        self.last_ctx: Any = None
        self.healthy = True

    def load(self) -> None:
        self.loaded = True

    def initialize(self, ctx: RuntimeContext) -> None:
        self.initialized = True
        self.last_ctx = ctx

    def health_check(self) -> EngineState:
        return EngineState.READY if self.healthy else EngineState.DEGRADED

    def execute(self, ctx: RuntimeContext) -> Any:
        self.executed = True
        self.last_ctx = ctx
        return {"engine": self.name, "request": ctx.request}

    def shutdown(self) -> None:
        self.shut_down = True


def test_register_creates_descriptor_and_state() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    manager.register(engine)

    assert manager.has("fake")
    desc = manager.descriptor("fake")
    assert isinstance(desc, EngineDescriptor)
    assert desc.name == "fake"
    assert desc.instance is engine
    assert desc.state == EngineState.CREATED
    assert manager.state("fake") == EngineState.CREATED


def test_get_missing_engine_returns_none() -> None:
    manager = EngineManager()
    assert manager.get("missing") is None
    assert not manager.has("missing")
    assert manager.descriptor("missing") is None
    assert manager.state("missing") is None


def test_names_lists_registered_engines() -> None:
    class EngineA:
        name = "A"

    class EngineB:
        name = "B"

    manager = EngineManager()
    manager.register(EngineA())  # type: ignore[arg-type]
    manager.register(EngineB())  # type: ignore[arg-type]

    names = manager.names()
    assert "A" in names
    assert "B" in names
    assert len(names) == 2


def test_unregister_removes_engine() -> None:
    manager = EngineManager()
    manager.register(FakeEngine())

    assert manager.unregister("fake") is True
    assert not manager.has("fake")
    assert manager.unregister("fake") is False


def test_clear_removes_all_engines() -> None:
    class EngineA:
        name = "A"

    class EngineB:
        name = "B"

    manager = EngineManager()
    manager.register(EngineA())  # type: ignore[arg-type]
    manager.register(EngineB())  # type: ignore[arg-type]

    manager.clear()
    assert manager.names() == []


# ─────────────────────────────────────────────────────────
# 生命周期测试
# ─────────────────────────────────────────────────────────


def test_load_transitions_state() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    manager.register(engine)

    manager.load("fake")
    assert engine.loaded
    assert manager.state("fake") == EngineState.LOADED
    assert manager.descriptor("fake").state == EngineState.LOADED


def test_initialize_requires_loaded_state() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    manager.register(engine)

    ctx = RuntimeContext.new()
    with pytest.raises(EngineNotReadyError):
        manager.initialize("fake", ctx)

    manager.load("fake")
    manager.initialize("fake", ctx)
    assert engine.initialized
    assert engine.last_ctx is ctx
    assert manager.state("fake") == EngineState.READY


def test_initialize_allows_reinitialize_from_stopped() -> None:
    manager = EngineManager()
    ctx = RuntimeContext.new()
    manager.register(FakeEngine())
    manager.load("fake")
    manager.initialize("fake", ctx)
    manager.shutdown("fake")

    manager.load("fake")
    manager.initialize("fake", ctx)
    assert manager.state("fake") == EngineState.READY


def test_initialize_all_loads_and_initializes_engines() -> None:
    class EngineA(FakeEngine):
        name = "A"

    class EngineB(FakeEngine):
        name = "B"

    manager = EngineManager()
    ctx = RuntimeContext.new()
    manager.register(EngineA())
    manager.register(EngineB())

    manager.initialize_all(ctx)

    assert manager.state("A") == EngineState.READY
    assert manager.state("B") == EngineState.READY


def test_health_check_updates_state() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    ctx = RuntimeContext.new()
    manager.register(engine)
    manager.load("fake")
    manager.initialize("fake", ctx)

    state = manager.health_check("fake")
    assert state == EngineState.READY
    assert manager.state("fake") == EngineState.READY

    engine.healthy = False
    state = manager.health_check("fake")
    assert state == EngineState.DEGRADED
    assert manager.state("fake") == EngineState.DEGRADED


def test_health_check_all_returns_all_states() -> None:
    class EngineA(FakeEngine):
        name = "A"

    class EngineB(FakeEngine):
        name = "B"

    manager = EngineManager()
    ctx = RuntimeContext.new()
    manager.register(EngineA())
    manager.register(EngineB())
    manager.load("A")
    manager.initialize("A", ctx)
    manager.load("B")
    manager.initialize("B", ctx)

    states = manager.health_check_all()
    assert states == {"A": EngineState.READY, "B": EngineState.READY}


def test_execute_requires_ready_state() -> None:
    manager = EngineManager()
    ctx = RuntimeContext.new()
    ctx.request = "hello"
    manager.register(FakeEngine())

    with pytest.raises(EngineNotReadyError):
        manager.execute("fake", ctx)

    manager.load("fake")
    manager.initialize("fake", ctx)

    result = manager.execute("fake", ctx)
    assert result == {"engine": "fake", "request": "hello"}


def test_execute_passes_context_to_engine() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    ctx = RuntimeContext.new()
    ctx.request = "ping"
    manager.register(engine)
    manager.load("fake")
    manager.initialize("fake", ctx)

    manager.execute("fake", ctx)
    assert engine.last_ctx is ctx
    assert engine.last_ctx.request == "ping"


def test_execute_restores_ready_state_after_run() -> None:
    manager = EngineManager()
    ctx = RuntimeContext.new()
    manager.register(FakeEngine())
    manager.load("fake")
    manager.initialize("fake", ctx)

    manager.execute("fake", ctx)
    assert manager.state("fake") == EngineState.READY


def test_execute_records_trace_step() -> None:
    trace = RuntimeTrace()
    manager = EngineManager(trace=trace)
    ctx = RuntimeContext.new()
    ctx.request = {"prompt": "ping"}
    manager.register(FakeEngine())
    manager.load("fake")
    manager.initialize("fake", ctx)

    manager.execute("fake", ctx)

    steps = trace.filter(node="engine:fake")
    assert len(steps) == 1
    assert steps[0].action == "engine_start"
    assert steps[0].payload["request_type"] == "dict"
    assert steps[0].duration_ms >= 0.0


def test_shutdown_transitions_state() -> None:
    manager = EngineManager()
    engine = FakeEngine()
    ctx = RuntimeContext.new()
    manager.register(engine)
    manager.load("fake")
    manager.initialize("fake", ctx)

    manager.shutdown("fake")
    assert engine.shut_down
    assert manager.state("fake") == EngineState.STOPPED


def test_shutdown_all_closes_all_engines() -> None:
    class EngineA(FakeEngine):
        name = "A"

    class EngineB(FakeEngine):
        name = "B"

    manager = EngineManager()
    ctx = RuntimeContext.new()
    a = EngineA()
    b = EngineB()
    manager.register(a)
    manager.register(b)
    manager.load("A")
    manager.initialize("A", ctx)
    manager.load("B")
    manager.initialize("B", ctx)

    manager.shutdown_all()
    assert a.shut_down
    assert b.shut_down
    assert manager.state("A") == EngineState.STOPPED
    assert manager.state("B") == EngineState.STOPPED


def test_states_returns_snapshot() -> None:
    manager = EngineManager()
    manager.register(FakeEngine())
    snapshot = manager.states()
    assert snapshot == {"fake": EngineState.CREATED}


def test_lifecycle_failure_transitions_to_error() -> None:
    class BrokenEngine(FakeEngine):
        name = "broken"

        def load(self) -> None:
            raise RuntimeError("load failed")

    manager = EngineManager()
    manager.register(BrokenEngine())

    with pytest.raises(RuntimeError):
        manager.load("broken")

    assert manager.state("broken") == EngineState.ERROR


def test_execute_failure_transitions_to_error() -> None:
    class BrokenEngine(FakeEngine):
        name = "broken"

        def execute(self, ctx: RuntimeContext) -> Any:
            raise RuntimeError("execute failed")

    manager = EngineManager()
    ctx = RuntimeContext.new()
    manager.register(BrokenEngine())
    manager.load("broken")
    manager.initialize("broken", ctx)

    with pytest.raises(RuntimeError):
        manager.execute("broken", ctx)

    assert manager.state("broken") == EngineState.ERROR
