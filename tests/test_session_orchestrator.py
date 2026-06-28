"""
test_session_orchestrator.py — SessionOrchestrator 单元测试
"""
import pytest
from PySide6.QtCore import QCoreApplication
from unittest.mock import MagicMock

from core.event_bus import MessageBus
from core.events import (
    UserSendEvent,
    SessionCreateEvent,
    SessionSwitchEvent,
    PhaseFlowCompletedEvent,
    UIAppendUserEvent,
    UIClearPhaseUIEvent,
)
from services.session_orchestrator import SessionOrchestrator
from services.task_service import TaskService
from workers.session_task import SessionTask, TaskStatus


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def mock_app_context():
    ctx = MagicMock()
    ctx.context_service = MagicMock()
    ctx.context_service.build_prompt_context.return_value = "ctx"
    return ctx


@pytest.fixture
def bus(app):
    b = MessageBus()
    b.connect_dispatch()
    return b


@pytest.fixture
def task_service(app):
    return TaskService()


@pytest.fixture
def orchestrator(app, mock_app_context, bus, task_service):
    return SessionOrchestrator(mock_app_context, bus, task_service)


class EventSpy:
    def __init__(self, bus: MessageBus):
        self.events = []
        bus.subscribe(self.on_event)

    def on_event(self, event):
        self.events.append(event)


def test_create_runtime(orchestrator):
    rt = orchestrator.create_runtime("s1", "/tmp", "test", "ask", "deepseek")
    assert rt.session_id == "s1"
    assert orchestrator.current_session_id == "s1"


def test_switch_session_does_not_overwrite_completed(app, mock_app_context, bus, task_service):
    orch = SessionOrchestrator(mock_app_context, bus, task_service)

    rt1 = orch.create_runtime("s1", "/tmp", "a", "ask", "m1")
    rt2 = orch.create_runtime("s2", "/tmp", "b", "ask", "m2")

    # 模拟 s1 任务已完成
    task = SessionTask(session_id="s1", mode="ask", user_input="hello")
    task.status = TaskStatus.COMPLETED
    task_service._tasks["s1"] = task

    orch.switch_session("s2")
    assert orch.current_session_id == "s2"

    # 切换回 s1，completed 不应被覆盖
    orch.switch_session("s1")
    assert task.status == TaskStatus.COMPLETED
    assert not rt1.is_active


def test_user_send_emits_ui_append_user(app, mock_app_context, bus, task_service):
    orch = SessionOrchestrator(mock_app_context, bus, task_service)
    spy = EventSpy(bus)

    orch.create_runtime("s1", "/tmp", "test", "ask", "deepseek")
    bus.process(UserSendEvent(session_id="s1", user_text="hello", mode="ask"))
    app.processEvents()

    append_events = [e for e in spy.events if isinstance(e, UIAppendUserEvent)]
    assert len(append_events) == 1
    assert append_events[0].text == "hello"


def test_phase_flow_completed_clears_state(app, mock_app_context, bus, task_service):
    orch = SessionOrchestrator(mock_app_context, bus, task_service)
    spy = EventSpy(bus)

    orch.create_runtime("s1", "/tmp", "test", "ask", "deepseek")

    # 模拟任务
    task = SessionTask(session_id="s1", mode="ask", user_input="hello")
    task_service._tasks["s1"] = task
    orch.get_runtime("s1").bind_task(task)

    bus.process(PhaseFlowCompletedEvent(session_id="s1", success=True))
    app.processEvents()

    assert task.status == TaskStatus.COMPLETED
    clear_events = [e for e in spy.events if isinstance(e, UIClearPhaseUIEvent)]
    assert len(clear_events) == 1
