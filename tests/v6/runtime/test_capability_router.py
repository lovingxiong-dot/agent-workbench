"""tests/v6/runtime/test_capability_router.py — CapabilityRouter Commit 3 测试。"""
from __future__ import annotations

import threading

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import EventBus, RuntimeEventType

from agent_workbench.runtime.capability.graph import CapabilityRegistry
from agent_workbench.runtime.capability_router import CapabilityRouter


def _make_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.load_defaults()
    return registry


def test_router_resolves_capability_id_to_engine_capability():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    ctx = RuntimeContext.new(task_id="t1")
    ctx.metadata["capability_id"] = "coding.python.debugging"

    capability = router.resolve(ctx)

    assert capability == "code_generation"


def test_router_falls_back_to_task_type_tool():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    ctx = RuntimeContext.new(task_id="t2")
    ctx.metadata["task_type"] = "tool"

    capability = router.resolve(ctx)

    assert capability == "tool_execution"


def test_router_falls_back_to_default_when_no_capability_id():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    ctx = RuntimeContext.new(task_id="t3")

    capability = router.resolve(ctx)

    assert capability == "chat"


def test_router_registry_priority_over_task_type():
    """capability_id 存在时，即使 task_type 为 tool，也应按 registry 解析。"""
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    ctx = RuntimeContext.new(task_id="t4")
    ctx.metadata["capability_id"] = "coding.python.debugging"
    ctx.metadata["task_type"] = "tool"

    capability = router.resolve(ctx)

    assert capability == "code_generation"


def test_router_returns_default_for_unknown_capability_id():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    ctx = RuntimeContext.new(task_id="t5")
    ctx.metadata["capability_id"] = "unknown.nonexistent"

    capability = router.resolve(ctx)

    assert capability == "chat"


def test_router_publishes_event_with_capability_context():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    event_bus = EventBus()
    event_bus.start()

    received = []
    done = threading.Event()

    def callback(event) -> None:
        if event.type == RuntimeEventType.CAPABILITY_RESOLVED:
            received.append(event.payload)
            done.set()

    event_bus.subscribe(RuntimeEventType.CAPABILITY_RESOLVED, callback)

    try:
        ctx = RuntimeContext.new(task_id="t6")
        ctx.metadata["capability_id"] = "coding.python.debugging"
        router.resolve(ctx, event_bus=event_bus)

        done.wait(timeout=2.0)
        assert len(received) == 1
        payload = received[0]
        assert payload["capability"] == "code_generation"
        assert payload["capability_id"] == "coding.python.debugging"
        assert payload["resolved_by"] == "registry"
        assert payload["capability_path"] == [
            "assistant",
            "coding",
            "coding.python",
            "coding.python.debugging",
        ]
    finally:
        event_bus.stop()


def test_router_publishes_fallback_event():
    registry = _make_registry()
    router = CapabilityRouter(capability_registry=registry)
    event_bus = EventBus()
    event_bus.start()

    received = []
    done = threading.Event()

    def callback(event) -> None:
        if event.type == RuntimeEventType.CAPABILITY_RESOLVED:
            received.append(event.payload)
            done.set()

    event_bus.subscribe(RuntimeEventType.CAPABILITY_RESOLVED, callback)

    try:
        ctx = RuntimeContext.new(task_id="t7")
        ctx.metadata["task_type"] = "tool"
        router.resolve(ctx, event_bus=event_bus)

        done.wait(timeout=2.0)
        assert len(received) == 1
        payload = received[0]
        assert payload["capability"] == "tool_execution"
        assert payload["resolved_by"] == "fallback"
        assert "capability_id" not in payload
    finally:
        event_bus.stop()
