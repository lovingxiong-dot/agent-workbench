"""
test_event_bus.py — MessageBus 单元测试
"""
import pytest
from PySide6.QtCore import QObject, Signal, QCoreApplication

from core.event_bus import MessageBus
from core.events import (
    UserSendEvent,
    QueueStateChangedEvent,
    UIAppendUserEvent,
)


class SignalSpy(QObject):
    received = Signal(object)

    def __init__(self):
        super().__init__()
        self.events = []

    def on_event(self, event):
        self.events.append(event)
        self.received.emit(event)


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_emit_and_dispatch_sync(app):
    bus = MessageBus()
    spy = SignalSpy()
    bus.subscribe(spy.on_event)
    bus.connect_dispatch()

    event = UserSendEvent(session_id="s1", user_text="hello", mode="ask")
    bus.emit(event)

    # QueuedConnection 需要事件循环处理，这里用 process 直接同步处理
    bus.process(event)

    assert len(spy.events) == 1
    assert spy.events[0].session_id == "s1"


def test_namespace_filter(app):
    bus = MessageBus()
    spy = SignalSpy()
    bus.subscribe_namespace("ui", spy.on_event)
    bus.connect_dispatch()

    ui_event = UIAppendUserEvent(session_id="s1", text="hi")
    user_event = UserSendEvent(session_id="s1", user_text="hello", mode="ask")

    bus.process(ui_event)
    bus.process(user_event)

    assert len(spy.events) == 1
    assert spy.events[0].event_type() == "ui.append_user"


def test_event_filter(app):
    bus = MessageBus()
    spy = SignalSpy()
    bus.subscribe(spy.on_event, event_filter=lambda e: e.session_id == "s2")
    bus.connect_dispatch()

    bus.process(UserSendEvent(session_id="s1", user_text="a", mode="ask"))
    bus.process(UserSendEvent(session_id="s2", user_text="b", mode="ask"))

    assert len(spy.events) == 1
    assert spy.events[0].user_text == "b"


def test_multiple_handlers(app):
    bus = MessageBus()
    spy1 = SignalSpy()
    spy2 = SignalSpy()
    bus.subscribe(spy1.on_event, namespace="queue")
    bus.subscribe(spy2.on_event, namespace="queue")
    bus.connect_dispatch()

    event = QueueStateChangedEvent(
        session_id="s1",
        state_name="STREAMING",
        is_full=False,
        send_enabled=True,
        bar_text="",
    )
    bus.process(event)

    assert len(spy1.events) == 1
    assert len(spy2.events) == 1


def test_event_type_string():
    event = UserSendEvent(session_id="s1", user_text="x", mode="ask")
    assert event.event_type() == "user.send"
