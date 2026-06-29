"""
test_ui_renderer.py — UIRenderer 单元测试
"""
import pytest
from PySide6.QtCore import QCoreApplication

from core.event_bus import MessageBus
from core.events import (
    UIAppendUserEvent,
    UIAppendAIEvent,
    UIAppendSystemEvent,
    UIStreamChunkEvent,
    UIFinalizeStreamEvent,
    UISetStreamingEvent,
    UISetPhaseIndicatorEvent,
    UIClearPhaseUIEvent,
    UIShowConfirmationEvent,
    UIHideConfirmationEvent,
    UIShowSkipVerifyEvent,
    UIHideSkipVerifyEvent,
    UIUpdateStatusBarEvent,
    UIUpdateSessionStatusEvent,
)
from ui.managers.ui_renderer import UIRenderer


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


class MockChatView:
    def __init__(self):
        self.calls = []

    def append_user(self, text):
        self.calls.append(("append_user", text))

    def append_ai(self, text):
        self.calls.append(("append_ai", text))

    def append_system(self, text):
        self.calls.append(("append_system", text))

    def append_chunk(self, chunk):
        self.calls.append(("append_chunk", chunk))

    def finalize_stream(self):
        self.calls.append(("finalize_stream",))

    def set_streaming(self, active):
        self.calls.append(("set_streaming", active))

    def set_phase_indicator(self, phase, task_count):
        self.calls.append(("set_phase_indicator", phase, task_count))

    def clear_phase_ui(self):
        self.calls.append(("clear_phase_ui",))

    def show_confirmation(self, task_list):
        self.calls.append(("show_confirmation", task_list))

    def hide_confirmation(self):
        self.calls.append(("hide_confirmation",))

    def show_skip_verify(self):
        self.calls.append(("show_skip_verify",))

    def hide_skip_verify(self):
        self.calls.append(("hide_skip_verify",))


class MockStatusIndicator:
    def __init__(self):
        self.text = ""

    def setText(self, text):
        self.text = text


@pytest.fixture
def chat_view():
    return MockChatView()


@pytest.fixture
def status_indicator():
    return MockStatusIndicator()


def test_append_user_for_current_session(app, bus, chat_view):
    renderer = UIRenderer(bus, chat_view, current_session_provider=lambda: "s1")
    bus.process(UIAppendUserEvent(session_id="s1", text="hello"))
    app.processEvents()

    assert chat_view.calls == [("append_user", "hello")]


def test_append_user_ignored_for_other_session(app, bus, chat_view):
    renderer = UIRenderer(bus, chat_view, current_session_provider=lambda: "s1")
    bus.process(UIAppendUserEvent(session_id="s2", text="hello"))
    app.processEvents()

    assert chat_view.calls == []


def test_stream_chunk_and_finalize(app, bus, chat_view):
    renderer = UIRenderer(bus, chat_view, current_session_provider=lambda: "s1")
    bus.process(UIStreamChunkEvent(session_id="s1", chunk="a"))
    bus.process(UIStreamChunkEvent(session_id="s1", chunk="b"))
    bus.process(UIFinalizeStreamEvent(session_id="s1"))
    app.processEvents()

    assert chat_view.calls == [
        ("append_chunk", "a"),
        ("append_chunk", "b"),
        ("finalize_stream",),
    ]


def test_phase_ui_events(app, bus, chat_view):
    renderer = UIRenderer(bus, chat_view, current_session_provider=lambda: "s1")
    bus.process(UISetPhaseIndicatorEvent(session_id="s1", phase="analyze", task_count=2))
    bus.process(UIShowConfirmationEvent(session_id="s1", task_list=["t1"]))
    bus.process(UIHideConfirmationEvent(session_id="s1"))
    bus.process(UIShowSkipVerifyEvent(session_id="s1"))
    bus.process(UIHideSkipVerifyEvent(session_id="s1"))
    bus.process(UIClearPhaseUIEvent(session_id="s1"))
    app.processEvents()

    assert chat_view.calls == [
        ("set_phase_indicator", "analyze", 2),
        ("show_confirmation", ["t1"]),
        ("hide_confirmation",),
        ("show_skip_verify",),
        ("hide_skip_verify",),
        ("clear_phase_ui",),
    ]


def test_status_bar_update(app, bus, chat_view, status_indicator):
    renderer = UIRenderer(
        bus,
        chat_view,
        status_indicator=status_indicator,
        current_session_provider=lambda: "s1",
    )
    bus.process(UIUpdateStatusBarEvent(session_id="s1", capacity_text="2/3"))
    app.processEvents()

    assert status_indicator.text == "2/3"


def test_unknown_event_name_is_safely_ignored(app, bus, chat_view):
    renderer = UIRenderer(bus, chat_view, current_session_provider=lambda: "s1")
    # 构造一个不在 handler 映射中的 ui 事件
    class UnknownEvent:
        namespace = "ui"
        name = "unknown_event"
        session_id = "s1"

        def event_type(self):
            return "ui.unknown_event"

    bus.process(UnknownEvent())
    app.processEvents()

    assert chat_view.calls == []
