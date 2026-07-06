"""tests/v6/test_v6_runtime.py — AgentRuntime 单元与集成测试。"""
from __future__ import annotations

import threading
import time

import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import EventBus, RuntimeEvent
from v6.runtime.runtime import AgentRuntime
from v6.runtime.scheduler import Scheduler
from v6.runtime.task import AnalyzeTask, ChatTask, Task


def wait_for(event: threading.Event, timeout: float = 3.0) -> bool:
    return event.wait(timeout=timeout)


@pytest.fixture
def runtime():
    rt = AgentRuntime()
    rt.start()
    yield rt
    rt.stop()


def collect_events(bus: EventBus, events: list[RuntimeEvent], done: threading.Event) -> None:
    def callback(event: RuntimeEvent) -> None:
        events.append(event)
        if event.type == "ai_end":
            done.set()

    bus.subscribe("user_message", callback)
    bus.subscribe("ai_start", callback)
    bus.subscribe("ai_chunk", callback)
    bus.subscribe("ai_end", callback)


def test_runtime_submit_chat_emits_event_sequence(runtime):
    events = []
    done = threading.Event()
    collect_events(runtime.event_bus, events, done)

    task = ChatTask(session_id="sid-1", text="hello")
    task_id = runtime.submit(task)
    assert task_id == task.task_id

    assert wait_for(done)
    time.sleep(0.05)

    types = [e.type for e in events]
    assert types == ["user_message", "ai_start", "ai_chunk", "ai_end"]
    assert events[0].payload["text"] == "hello"
    assert events[2].payload["text"] == "收到：hello"
    assert all(e.task_id == task_id for e in events)


def test_runtime_context_tracks_messages(runtime):
    events = []
    done = threading.Event()

    def callback(event: RuntimeEvent) -> None:
        events.append(event)
        if event.type == "ai_end":
            done.set()

    runtime.event_bus.subscribe("ai_end", callback)

    task = ChatTask(session_id="sid-2", text="context")
    runtime.submit(task)

    assert wait_for(done)
    runtime.scheduler.wait_all(timeout=2.0)
    ctx = runtime._contexts.get(task.task_id)
    assert ctx is None  # 执行完成后已清理


def test_runtime_register_handler_overrides_echo(runtime):
    custom_called = threading.Event()

    def custom_handler(task: Task, ctx: RuntimeContext, bus: EventBus) -> None:
        bus.emit("ai_chunk", {"text": "custom", "phase": "p1"}, task.task_id)
        bus.emit("ai_end", {}, task.task_id)
        custom_called.set()

    runtime.register_handler("chat", custom_handler)

    end = threading.Event()
    runtime.event_bus.subscribe("ai_end", lambda e: end.set())

    task = ChatTask(text="hello")
    runtime.submit(task)

    assert wait_for(custom_called)
    assert wait_for(end)


def test_runtime_unhandled_task_emits_error(runtime):
    error = threading.Event()
    received = []

    def callback(event: RuntimeEvent) -> None:
        received.append(event)
        if event.type == "error":
            error.set()

    runtime.event_bus.subscribe("error", callback)

    task = AnalyzeTask(target_path="/tmp")
    runtime.submit(task)

    assert wait_for(error)
    assert received[0].payload["message"].startswith("No handler")


def test_runtime_cancel_task(runtime):
    started = threading.Event()
    end = threading.Event()

    def slow_handler(task: Task, ctx: RuntimeContext, bus: EventBus) -> None:
        started.set()
        time.sleep(0.5)
        bus.emit("ai_end", {}, task.task_id)
        end.set()

    runtime.register_handler("chat", slow_handler)

    task = ChatTask(text="slow")
    task_id = runtime.submit(task)
    assert wait_for(started)
    assert runtime.cancel(task_id) is True
    # 取消对已执行中的任务不中断执行体，但调度器会接受取消请求
    assert task_id in runtime.scheduler._cancelled
    runtime.scheduler.wait_all(timeout=2.0)
    # 取消的任务不再处于 pending/running
    assert task_id not in runtime.scheduler._pending
    assert task_id not in runtime.scheduler._running_tasks


def test_runtime_lifecycle_start_stop():
    rt = AgentRuntime()
    assert not rt.running
    rt.start()
    assert rt.running
    rt.stop()
    assert not rt.running


def test_runtime_injected_components():
    bus = EventBus()
    scheduler = Scheduler()
    rt = AgentRuntime(event_bus=bus, scheduler=scheduler)
    assert rt.event_bus is bus
    assert rt.scheduler is scheduler


# ── UIController + AgentRuntime 端到端集成 ──

def test_uicontroller_runtime_end_to_end(qapp, tmp_path):
    from PySide6.QtCore import Qt
    from v6.services.chat_service import ChatService
    from v6.services.config_service import ConfigService
    from v6.services.session_service import SessionService
    from v6.ui_controller import UIController

    cfg = ConfigService(data_dir=tmp_path)
    sess = SessionService(data_dir=tmp_path)
    chat = ChatService(session_manager=sess.manager)
    ctrl = UIController(
        config_service=cfg,
        session_service=sess,
        chat_service=chat,
    )

    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "runtime-e2e"
    sess.create(ctx)
    sid = ctx.session_id
    sess.set_active(ctx)

    ai_chunks = []
    stream_ended = []

    ctrl.sign_chat_ai.connect(
        lambda text, phase: ai_chunks.append((text, phase)),
        type=Qt.ConnectionType.DirectConnection,
    )
    ctrl.sign_stream_end.connect(
        lambda: stream_ended.append(True),
        type=Qt.ConnectionType.DirectConnection,
    )

    ctrl.startup()
    ctrl.on_send_msg("端到端测试")

    # 等待事件总线处理完成
    deadline = time.time() + 3.0
    while time.time() < deadline and not stream_ended:
        time.sleep(0.05)

    ctrl.shutdown()

    assert any(text.startswith("收到：") for text, _ in ai_chunks)
    assert stream_ended
    verify = RuntimeContext.new(session_id=sid)
    chat.load(verify)
    assert verify.messages[0].role == "user"
    assert verify.messages[0].content == "端到端测试"
    assert verify.messages[1].role == "ai"
    assert verify.messages[1].content.startswith("收到：")
