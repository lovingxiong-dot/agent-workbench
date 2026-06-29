"""
test_phase_coordinator.py — PhaseCoordinator 单元测试
"""
import pytest
from PySide6.QtCore import QCoreApplication

from core.event_bus import MessageBus
from core.events import (
    PhaseChangedEvent,
    PhaseAnalyzeRequiredEvent,
    PhaseConfirmRequiredEvent,
    PhaseExecuteRequiredEvent,
    PhaseVerifyRequiredEvent,
    PhaseArchiveRequiredEvent,
    PhaseFlowCompletedEvent,
    PhaseErrorEvent,
    UIAppendSystemEvent,
    UIClearPhaseUIEvent,
    UISetPhaseIndicatorEvent,
    UIShowConfirmationEvent,
    UIHideConfirmationEvent,
    UIShowSkipVerifyEvent,
    UIHideSkipVerifyEvent,
)
from agent_engine.phase_manager import PhaseManager, TaskItem
from ui.managers.phase_coordinator import PhaseCoordinator


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
def phase_manager(app):
    return PhaseManager()


@pytest.fixture
def coordinator(bus, phase_manager):
    return PhaseCoordinator(
        session_id="s1",
        phase_manager=phase_manager,
        message_bus=bus,
    )


class EventSpy:
    def __init__(self, bus: MessageBus):
        self.events = []
        bus.subscribe(self.on_event)

    def on_event(self, event):
        self.events.append(event)


def test_start_flow_emits_analyze_required(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("hello", "ask", "ctx")
    app.processEvents()

    analyze = [e for e in spy.events if isinstance(e, PhaseAnalyzeRequiredEvent)]
    assert len(analyze) == 1
    assert analyze[0].session_id == "s1"
    assert analyze[0].user_text == "hello"
    assert analyze[0].mode == "ask"


def test_phase_changed_emits_indicator_event(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("hello", "ask", "ctx")
    app.processEvents()

    changed = [e for e in spy.events if isinstance(e, PhaseChangedEvent)]
    assert len(changed) >= 1
    assert changed[0].session_id == "s1"
    assert changed[0].phase == "analyze"

    indicators = [e for e in spy.events if isinstance(e, UISetPhaseIndicatorEvent)]
    assert len(indicators) >= 1
    assert indicators[0].session_id == "s1"


def test_confirm_required_emits_ui_show_confirmation(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("plan task", "plan", "ctx")
    app.processEvents()

    # 模拟 analyze 返回任务清单
    phase_manager.on_analyze_complete([TaskItem(id="t1", description="task")])
    app.processEvents()

    confirm = [e for e in spy.events if isinstance(e, PhaseConfirmRequiredEvent)]
    show = [e for e in spy.events if isinstance(e, UIShowConfirmationEvent)]
    assert len(confirm) == 1
    assert confirm[0].session_id == "s1"
    assert len(show) == 1
    assert show[0].session_id == "s1"


def test_flow_finished_emits_completed_and_clear(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("hello", "ask", "ctx")
    app.processEvents()

    phase_manager.on_analyze_complete([])
    app.processEvents()

    completed = [e for e in spy.events if isinstance(e, PhaseFlowCompletedEvent)]
    clear = [e for e in spy.events if isinstance(e, UIClearPhaseUIEvent)]
    assert len(completed) == 1
    assert completed[0].session_id == "s1"
    assert completed[0].success is True
    assert len(clear) == 1
    assert clear[0].session_id == "s1"
    assert not coordinator.is_flow_active


def test_error_emits_system_and_finishes(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("hello", "invalid_mode", "ctx")
    app.processEvents()

    system = [e for e in spy.events if isinstance(e, UIAppendSystemEvent)]
    completed = [e for e in spy.events if isinstance(e, PhaseFlowCompletedEvent)]
    assert len(system) == 1
    assert system[0].session_id == "s1"
    assert len(completed) == 1
    assert completed[0].success is False
    assert not coordinator.is_flow_active


def test_double_start_is_ignored(app, bus, phase_manager, coordinator):
    spy = EventSpy(bus)
    coordinator.start_flow("first", "ask", "ctx")
    coordinator.start_flow("second", "ask", "ctx")
    app.processEvents()

    analyze = [e for e in spy.events if isinstance(e, PhaseAnalyzeRequiredEvent)]
    assert len(analyze) == 1
    assert analyze[0].user_text == "first"


def test_user_actions_guarded_by_flow_active(app, bus, phase_manager, coordinator):
    # 未启动时调用不应报错
    coordinator.on_user_confirm(True)
    coordinator.on_user_reanalyze()
    coordinator.on_user_skip_verify()
    app.processEvents()
    assert not coordinator.is_flow_active
