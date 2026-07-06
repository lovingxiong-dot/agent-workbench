"""tests/v6/test_v6_event_bus.py — EventBus 单元测试。"""
from __future__ import annotations

import threading
import time

import pytest

from v6.runtime.event_bus import EventBus, RuntimeEvent


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
