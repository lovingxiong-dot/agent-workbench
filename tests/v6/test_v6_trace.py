"""tests/v6/test_v6_trace.py — RuntimeTrace 与 Replay 测试。"""
from __future__ import annotations

import threading
import time

from v6.runtime.adapter import LocalRuntimeAdapter
from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import EventBus
from v6.runtime.runtime import AgentRuntime
from v6.runtime.trace import ReplayPlayer, RuntimeTrace


def test_trace_records_steps():
    trace = RuntimeTrace()
    trace.add(node="adapter", action="submit", phase="inference", payload={"x": 1})
    trace.add(node="engine", action="echo_start", phase="inference")

    steps = trace.steps()
    assert len(steps) == 2
    assert steps[0].node == "adapter"
    assert steps[0].action == "submit"
    assert steps[0].payload == {"x": 1}
    assert steps[1].node == "engine"


def test_trace_filter():
    trace = RuntimeTrace()
    trace.add(node="runtime", action="task_start")
    trace.add(node="engine", action="echo_start")
    trace.add(node="runtime", action="task_finish")

    runtime_steps = trace.filter(node="runtime")
    assert len(runtime_steps) == 2
    assert all(s.node == "runtime" for s in runtime_steps)

    start_steps = trace.filter(action="task_start")
    assert len(start_steps) == 1


def test_trace_snapshot_and_restore():
    trace = RuntimeTrace()
    trace.add(node="engine", action="emit_chunk", payload={"text": "hi"})
    snap = trace.snapshot()
    assert len(snap["steps"]) == 1
    assert snap["steps"][0]["payload"]["text"] == "hi"


def test_context_carries_trace():
    ctx = RuntimeContext.new()
    assert isinstance(ctx.trace, RuntimeTrace)
    ctx.trace.add(node="test", action="verify")
    snapshot = ctx.snapshot()
    assert "trace" in snapshot
    assert len(snapshot["trace"]["steps"]) == 1


def test_context_clone_copies_trace():
    ctx = RuntimeContext.new()
    ctx.trace.add(node="a", action="b")
    cloned = ctx.clone()
    assert cloned.trace is not ctx.trace
    assert len(cloned.trace.steps()) == 1
    cloned.trace.add(node="c", action="d")
    assert len(ctx.trace.steps()) == 1
    assert len(cloned.trace.steps()) == 2


def test_context_restore_rebuilds_trace():
    ctx = RuntimeContext.new()
    ctx.trace.add(node="a", action="b", payload={"k": "v"})
    snap = ctx.snapshot()

    restored = RuntimeContext.new()
    restored.restore(snap)
    steps = restored.trace.steps()
    assert len(steps) == 1
    assert steps[0].node == "a"
    assert steps[0].payload == {"k": "v"}


def test_runtime_records_trace():
    runtime = AgentRuntime()
    runtime.start()
    try:
        ctx = RuntimeContext.new(session_id="s-trace")
        ctx.add_message("user", "hello")
        adapter = LocalRuntimeAdapter(runtime)

        done = threading.Event()
        runtime.subscribe("ai_end", lambda _evt: done.set())

        adapter.submit(ctx)
        assert done.wait(timeout=2.0)
        runtime.scheduler.wait_all(timeout=2.0)

        steps = ctx.trace.steps()
        nodes = [s.node for s in steps]
        assert "adapter" in nodes
        assert "runtime" in nodes
        assert "engine" in nodes
        assert any(s.node == "runtime" and s.action == "task_start" for s in steps)
        assert any(s.node == "runtime" and s.action == "task_finish" for s in steps)
        assert any(s.node == "engine" and s.action == "echo_start" for s in steps)
        assert any(s.node == "engine" and s.action == "echo_end" for s in steps)
        assert ctx.status == "completed"
    finally:
        runtime.stop()


def test_replay_player_emits_events():
    trace = RuntimeTrace()
    trace.add(
        node="engine",
        action="emit_start",
        phase="inference",
        payload={"data": {"phase": ""}},
    )
    trace.add(
        node="engine",
        action="emit_chunk",
        phase="inference",
        payload={"data": {"text": "chunk1"}},
    )
    trace.add(
        node="engine",
        action="emit_end",
        phase="inference",
        payload={"data": {}},
    )

    bus = EventBus()
    bus.start()
    try:
        received = []
        bus.subscribe("ai_start", lambda e: received.append((e.type, e.payload)))
        bus.subscribe("ai_chunk", lambda e: received.append((e.type, e.payload)))
        bus.subscribe("ai_end", lambda e: received.append((e.type, e.payload)))

        player = ReplayPlayer(trace, bus)
        player.play(task_id="replay-1")
        # 等待事件总线异步分发
        time.sleep(0.15)

        types = [t for t, _ in received]
        assert types == ["ai_start", "ai_chunk", "ai_end"]
        assert received[1][1]["text"] == "chunk1"
    finally:
        bus.stop()
