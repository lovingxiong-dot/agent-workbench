"""
test_v3_flow.py — v3 事件流集成测试

验证从 UserSendEvent 到 PhaseAnalyzeRequiredEvent / WorkerCreatedEvent 的完整链路，
无需真实 LLM 调用。
"""
import pytest
from PySide6.QtCore import QCoreApplication
from unittest.mock import MagicMock

from core.event_bus import MessageBus
from core.events import (
    UserSendEvent,
    QueueStateChangedEvent,
    QueueTaskReadyEvent,
    PhaseAnalyzeRequiredEvent,
    WorkerCreatedEvent,
    UIAppendUserEvent,
)
from services.session_orchestrator import SessionOrchestrator
from services.task_service import TaskService
from workers.task_capacity import TaskCapacity


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def bus(app):
    b = MessageBus()
    b.connect_dispatch()
    return b


@pytest.fixture
def mock_app_context(app):
    ctx = MagicMock()
    ctx.context_service = MagicMock()
    ctx.context_service.build_prompt_context.return_value = "ctx"
    ctx.session_service = MagicMock()
    ctx.worker_manager = MagicMock()
    return ctx


@pytest.fixture
def task_service(app, bus):
    return TaskService(
        capacity=TaskCapacity(max_concurrent_tasks=1, max_queued_tasks=1),
        message_bus=bus,
    )


@pytest.fixture
def orchestrator(app, mock_app_context, bus, task_service):
    return SessionOrchestrator(mock_app_context, bus, task_service)


class EventSpy:
    def __init__(self, bus: MessageBus):
        self.events = []
        bus.subscribe(self.on_event)

    def on_event(self, event):
        self.events.append(event)


def test_user_send_event_enqueues_and_emits_queue_state(app, bus, orchestrator):
    spy = EventSpy(bus)
    orch = orchestrator

    orch.create_runtime("s1", "/tmp", "test", "ask", "deepseek")
    bus.process(UserSendEvent(session_id="s1", user_text="hello", mode="ask"))
    app.processEvents()

    # 用户消息 UI 事件
    append_user = [e for e in spy.events if isinstance(e, UIAppendUserEvent)]
    assert len(append_user) == 1
    assert append_user[0].text == "hello"

    # 队列状态变化事件
    queue_states = [e for e in spy.events if isinstance(e, QueueStateChangedEvent)]
    assert len(queue_states) >= 1
    assert queue_states[-1].session_id == "s1"


def _pump_events(app, times=5):
    for _ in range(times):
        app.processEvents()


def test_queue_task_ready_starts_phase_flow(app, bus, orchestrator):
    spy = EventSpy(bus)
    orch = orchestrator

    rt = orch.create_runtime("s1", "/tmp", "test", "ask", "deepseek")
    # 直接入队并触发 ready
    rt.queue_manager.enqueue("hello", "ask", "ctx")
    _pump_events(app)

    # PhaseAnalyzeRequiredEvent 应该被发射
    analyze = [e for e in spy.events if isinstance(e, PhaseAnalyzeRequiredEvent)]
    assert len(analyze) == 1
    assert analyze[0].session_id == "s1"
    assert analyze[0].user_text == "hello"

    # WorkerCreatedEvent 应该被发射
    created = [e for e in spy.events if isinstance(e, WorkerCreatedEvent)]
    assert len(created) == 1
    assert created[0].session_id == "s1"
    assert created[0].mode == "ask"


def test_user_send_v3_full_chain(app, bus, orchestrator):
    spy = EventSpy(bus)
    orch = orchestrator

    orch.create_runtime("s1", "/tmp", "test", "ask", "deepseek")
    bus.process(UserSendEvent(session_id="s1", user_text="hello", mode="ask"))
    _pump_events(app)

    # 完整链路：用户消息 -> 队列状态 -> PhaseAnalyze -> WorkerCreated
    assert any(isinstance(e, UIAppendUserEvent) for e in spy.events)
    assert any(isinstance(e, QueueStateChangedEvent) for e in spy.events)
    assert any(isinstance(e, PhaseAnalyzeRequiredEvent) for e in spy.events)
    assert any(isinstance(e, WorkerCreatedEvent) for e in spy.events)
