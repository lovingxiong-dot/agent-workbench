"""tests/v6/test_v6_event_bus.py — Runtime Event Bus 单元测试。"""
from __future__ import annotations

import asyncio
import threading
import time

import pytest

from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import EventBus, RuntimeEvent, RuntimeEventType
from v6.runtime.trace import RuntimeTrace


@pytest.fixture
def bus():
    event_bus = EventBus()
    event_bus.start()
    yield event_bus
    event_bus.stop()


def wait_for(event: threading.Event, timeout: float = 2.0) -> bool:
    return event.wait(timeout=timeout)


def test_subscribe_and_emit(bus):
    received = []
    done = threading.Event()

    def callback(event: RuntimeEvent) -> None:
        received.append(event)
        if len(received) >= 1:
            done.set()

    bus.subscribe("test", callback)
    bus.emit("test", {"hello": "world"}, task_id="t1")

    assert wait_for(done)
    assert len(received) == 1
    assert received[0].type == "test"
    assert received[0].payload == {"hello": "world"}
    assert received[0].task_id == "t1"
    assert isinstance(received[0].timestamp, float)


def test_multiple_subscribers(bus):
    done1 = threading.Event()
    done2 = threading.Event()

    def cb1(event: RuntimeEvent) -> None:
        done1.set()

    def cb2(event: RuntimeEvent) -> None:
        done2.set()

    bus.subscribe("multi", cb1)
    bus.subscribe("multi", cb2)
    bus.emit("multi", {}, task_id="t2")

    assert wait_for(done1)
    assert wait_for(done2)


def test_unsubscribe(bus):
    received = []
    done = threading.Event()

    def callback(event: RuntimeEvent) -> None:
        received.append(event)
        done.set()

    bus.subscribe("unsub", callback)
    bus.unsubscribe("unsub", callback)
    bus.emit("unsub", {}, task_id="t3")

    time.sleep(0.1)
    assert not received


def test_event_type_isolation(bus):
    received = []
    done = threading.Event()

    def callback(event: RuntimeEvent) -> None:
        received.append(event)
        done.set()

    bus.subscribe("type_a", callback)
    bus.emit("type_b", {}, task_id="t4")

    time.sleep(0.1)
    assert not received
    bus.emit("type_a", {}, task_id="t5")
    assert wait_for(done)
    assert received[0].task_id == "t5"


def test_emit_before_start_is_dropped():
    bus = EventBus()
    received = []

    def callback(event: RuntimeEvent) -> None:
        received.append(event)

    bus.subscribe("early", callback)
    bus.emit("early", {}, task_id="t6")

    time.sleep(0.1)
    assert not received


def test_runtime_event_schema(bus):
    """RuntimeEvent 应携带 source / trace_id / phase / task_id。"""
    received = []
    done = threading.Event()

    def callback(event: RuntimeEvent) -> None:
        received.append(event)
        done.set()

    bus.subscribe(RuntimeEventType.ENGINE_STARTED, callback)
    bus.publish(
        RuntimeEventType.ENGINE_STARTED,
        {},
        task_id="t-schema",
        source="engine:llm",
        trace_id="trace-1",
        phase="inference",
    )

    assert wait_for(done)
    event = received[0]
    assert event.type == RuntimeEventType.ENGINE_STARTED
    assert event.task_id == "t-schema"
    assert event.source == "engine:llm"
    assert event.trace_id == "trace-1"
    assert event.phase == "inference"
    assert isinstance(event.timestamp, float)


def test_async_dispatch():
    """dispatch(RuntimeEvent) 应可被 await，并在当前事件循环同步分发。"""

    async def run() -> None:
        loop = asyncio.get_running_loop()
        bus = EventBus()
        bus._loop = loop
        bus._queue = asyncio.Queue()
        bus._running = True

        received = []

        async def callback(event: RuntimeEvent) -> None:
            received.append(event)

        bus.subscribe("async.test", callback)
        event = RuntimeEvent(type="async.test", payload={"k": "v"}, task_id="t-async")
        await bus.dispatch(event)

        assert len(received) == 1
        assert received[0].type == "async.test"
        assert received[0].payload == {"k": "v"}

    asyncio.run(run())


def test_trace_hook_routes_by_task_id(bus):
    """Trace Hook 按 task_id 路由，事件自动写入对应 RuntimeTrace。"""
    trace_a = RuntimeTrace()
    trace_b = RuntimeTrace()
    bus.add_trace_hook("task-a", trace_a)
    bus.add_trace_hook("task-b", trace_b)

    bus.publish(
        RuntimeEventType.ENGINE_STARTED,
        {"engine": "llm"},
        task_id="task-a",
        source="engine:llm",
        phase="inference",
    )
    bus.publish(
        RuntimeEventType.ENGINE_STARTED,
        {"engine": "tool"},
        task_id="task-b",
        source="engine:tool",
        phase="tool",
    )

    time.sleep(0.1)

    steps_a = trace_a.filter(node="engine:llm")
    steps_b = trace_b.filter(node="engine:tool")
    assert len(steps_a) == 1
    assert len(steps_b) == 1
    assert steps_a[0].action == TraceEvent.ENGINE_START.value
    assert steps_b[0].action == TraceEvent.ENGINE_START.value

    bus.remove_trace_hook("task-a")
    bus.publish(
        RuntimeEventType.ENGINE_COMPLETED,
        {},
        task_id="task-a",
        source="engine:llm",
    )
    time.sleep(0.1)
    assert len(trace_a.steps()) == 1  # hook 移除后不再写入


def test_trace_hook_does_not_write_without_task_id(bus):
    """没有 task_id 的事件不应被 Trace Hook 记录。"""
    trace = RuntimeTrace()
    bus.add_trace_hook("task-x", trace)
    bus.publish(RuntimeEventType.ENGINE_STARTED, {}, task_id="")
    time.sleep(0.1)
    assert len(trace.steps()) == 0


def test_manager_event_types_exist():
    """v6.9.3-alpha 新增 Manager 级事件类型应存在。"""
    assert RuntimeEventType.MANAGER_INTENT_CLASSIFIED == "manager.intent.classified"
    assert RuntimeEventType.MANAGER_CAPABILITY_SELECTED == "manager.capability.selected"
    assert RuntimeEventType.MANAGER_CHAIN_STEP_STARTED == "manager.chain.step.started"
    assert RuntimeEventType.CAPABILITY_CHAIN_STEP_STARTED == "capability.chain.step.started"
