"""tests/v6/test_v6_integration.py — Runtime 最小 happy path 集成测试。

覆盖：提交 ChatTask → 收到 user_message/ai_start/ai_chunk/ai_end 完整事件序列。
"""
from __future__ import annotations

import threading
import time

import pytest

from v6.runtime.event_bus import EventBus
from v6.runtime.runtime import AgentRuntime
from v6.runtime.scheduler import Scheduler
from v6.runtime.task import ChatTask


def wait_for(event: threading.Event, timeout: float = 3.0) -> bool:
    return event.wait(timeout=timeout)


@pytest.fixture
def runtime():
    rt = AgentRuntime()
    rt.start()
    yield rt
    rt.stop()


def test_runtime_chat_task_happy_path(runtime):
    """最小 happy path：ChatTask 产生完整事件序列。"""
    events = []
    done = threading.Event()

    def on_event(event) -> None:
        events.append(event)
        if event.type == "ai_end":
            done.set()

    runtime.subscribe("user_message", on_event)
    runtime.subscribe("ai_start", on_event)
    runtime.subscribe("ai_chunk", on_event)
    runtime.subscribe("ai_end", on_event)

    task = ChatTask(session_id="sid-happy", text="集成测试")
    task_id = runtime.submit_task(task)

    assert wait_for(done)
    time.sleep(0.05)

    types = [e.type for e in events]
    assert types == ["user_message", "ai_start", "ai_chunk", "ai_end"]
    assert events[0].payload["text"] == "集成测试"
    assert events[2].payload["text"] == "收到：集成测试"
    assert all(e.task_id == task_id for e in events)


def test_scheduler_running_count_and_wait_all():
    """Scheduler 并发计数与 wait_all 行为。"""
    started = threading.Event()
    can_finish = threading.Event()

    def executor(task: ChatTask) -> None:
        started.set()
        can_finish.wait()

    scheduler = Scheduler(concurrency=3, executor=executor)
    scheduler.start()
    try:
        task_id = scheduler.submit(ChatTask(text="block"))
        assert wait_for(started)
        assert scheduler.running_count() == 1
        can_finish.set()
        assert scheduler.wait_all(timeout=2.0) is True
        assert scheduler.running_count() == 0
        assert task_id
    finally:
        scheduler.stop()


def test_event_bus_publish_interface():
    """EventBus.publish 接口可用。"""
    bus = EventBus()
    received = []
    done = threading.Event()

    def callback(event) -> None:
        received.append(event)
        done.set()

    bus.subscribe("publish", callback)
    bus.start()
    try:
        bus.publish("publish", {"key": "value"}, task_id="t-pub")
        assert wait_for(done)
        assert received[0].payload == {"key": "value"}
        assert received[0].task_id == "t-pub"
    finally:
        bus.stop()
