"""tests/v6/test_v6_services.py — Services 层单元与集成测试。

所有 Service 公共方法统一接收 RuntimeContext。
"""
from __future__ import annotations

import pytest

from v6.runtime.context import RuntimeContext


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    yield app


def test_config_service_apply_and_persist(tmp_path, qapp):
    from v6.config_manager import ConfigManager
    from v6.services.config_service import ConfigService

    svc = ConfigService(data_dir=tmp_path)
    ctx = RuntimeContext.new()

    svc.apply(ctx)
    assert ctx.metadata["config"]["theme"] == "dark"
    assert ctx.metadata["config"]["last_mode"] == "Agent"
    assert ctx.metadata["config"]["last_model"] == "gpt-4o"
    assert ctx.metadata["config"]["window_geometry"] is None

    ctx.metadata["config"]["theme"] = "light"
    ctx.metadata["config"]["last_mode"] = "Coder"
    ctx.metadata["config"]["last_model"] = "claude-3"
    ctx.metadata["config"]["window_geometry"] = {"x": 100, "y": 200}
    svc.persist(ctx)

    cm = ConfigManager(data_dir=tmp_path)
    assert cm.get("theme.name") == "light"
    assert cm.get("app.last_mode") == "Coder"
    assert cm.get("app.last_model") == "claude-3"
    assert cm.get("window.geometry") == {"x": 100, "y": 200}


def test_session_service_load_and_create(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()

    svc.load(ctx)
    assert ctx.metadata["session_groups"] == []

    ctx.metadata["session_title"] = "new session"
    svc.create(ctx)
    sid = ctx.session_id
    assert sid is not None

    ctx.session_id = None
    svc.get_active(ctx)
    assert ctx.session_id == sid

    svc.load(ctx)
    groups = ctx.metadata["session_groups"]
    assert len(groups) == 1
    assert groups[0][0] == "today"
    assert groups[0][2][0]["sid"] == sid
    assert groups[0][2][0]["title"] == "new session"


def test_session_service_delete_clears_active(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "to delete"
    svc.create(ctx)
    sid = ctx.session_id

    ctx.session_id = sid
    svc.get_active(ctx)
    assert ctx.session_id == sid

    ctx.session_id = sid
    svc.delete(ctx)

    ctx.session_id = None
    svc.get_active(ctx)
    assert ctx.session_id is None

    svc.load(ctx)
    assert ctx.metadata["session_groups"] == []


def test_session_service_pin_and_rename(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "pin me"
    svc.create(ctx)
    sid = ctx.session_id

    ctx.session_id = sid
    assert svc.pin(ctx) is True
    assert svc.manager.get(sid)["is_pinned"] is True

    ctx.metadata["session_title"] = "renamed"
    svc.rename(ctx)
    assert svc.manager.get(sid)["title"] == "renamed"


def test_session_service_update_metadata(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "meta"
    ctx.metadata["session_summary"] = "summary"
    ctx.metadata["session_icon"] = "🤖"
    ctx.metadata["session_workspace_id"] = "chat"
    ctx.metadata["session_last_activity"] = "typing"
    svc.create(ctx)
    sid = ctx.session_id

    ctx.session_id = sid
    ctx.metadata["session_summary"] = "updated"
    svc.update_metadata(ctx)
    session = svc.manager.get(sid)
    assert session["summary"] == "updated"
    assert session["icon"] == "🤖"
    assert session["workspace_id"] == "chat"
    assert session["last_activity"] == "typing"


def test_session_service_search(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)

    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "apple pie"
    svc.create(ctx)
    sid_apple = ctx.session_id

    ctx.session_id = None
    ctx.metadata["session_title"] = "banana"
    svc.create(ctx)

    svc.manager.touch(sid_apple, "apple preview")

    ctx.metadata["search_text"] = "apple"
    svc.search(ctx)
    groups = ctx.metadata["session_groups"]
    assert len(groups) == 1
    assert len(groups[0][2]) == 1
    assert groups[0][2][0]["sid"] == sid_apple

    ctx.metadata["search_text"] = "zzzz"
    svc.search(ctx)
    assert ctx.metadata["session_groups"] == []

    ctx.metadata["search_text"] = ""
    svc.search(ctx)
    assert len(ctx.metadata["session_groups"]) == 1


def test_chat_service_store_and_load(tmp_path, qapp):
    from v6.runtime.types import ChatMessage
    from v6.session_manager import SessionManager
    from v6.services.chat_service import ChatService

    sm = SessionManager(data_dir=tmp_path)
    chat = ChatService(session_manager=sm)
    sid = sm.create("chat")

    ctx = RuntimeContext.new(session_id=sid)
    ctx.add_message("user", "hello")
    chat.store(ctx)
    ctx.add_message("ai", "world")
    chat.store(ctx)

    ctx.messages = []
    chat.load(ctx)
    assert len(ctx.messages) == 2
    assert ctx.messages[0] == ChatMessage(role="user", content="hello")
    assert ctx.messages[1] == ChatMessage(role="ai", content="world")

    assert sm.get(sid)["preview"] == "world"


def test_chat_service_clear(tmp_path, qapp):
    from v6.session_manager import SessionManager
    from v6.services.chat_service import ChatService

    sm = SessionManager(data_dir=tmp_path)
    chat = ChatService(session_manager=sm)
    sid = sm.create("chat")

    ctx = RuntimeContext.new(session_id=sid)
    ctx.add_message("user", "msg")
    chat.store(ctx)

    ctx.messages = []
    chat.load(ctx)
    assert len(ctx.messages) == 1

    chat.clear(ctx)
    ctx.messages = []
    chat.load(ctx)
    assert ctx.messages == []


def test_services_integration_with_ui_controller(tmp_path, qapp):
    from v6.services.chat_service import ChatService
    from v6.services.config_service import ConfigService
    from v6.services.session_service import SessionService
    from v6.ui_controller import UIController

    cfg = ConfigService(data_dir=tmp_path)
    sess = SessionService(data_dir=tmp_path)
    chat = ChatService(session_manager=sess.manager)

    # 预先创建并激活一个会话，确保 UIController.startup 能选中它
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "integration"
    sess.create(ctx)
    sid = ctx.session_id
    sess.set_active(ctx)

    ctrl = UIController(
        config_service=cfg,
        session_service=sess,
        chat_service=chat,
    )

    sessions_signal = []
    active_signal = []
    ctrl.sign_update_sessions.connect(lambda g: sessions_signal.append(g))
    ctrl.sign_set_active_session.connect(lambda s: active_signal.append(s))

    ctrl.startup()
    assert sessions_signal
    assert active_signal
    assert ctrl._active_sid == active_signal[-1]

    ctrl.on_send_msg("integration test")

    ctx = RuntimeContext.new(session_id=ctrl._active_sid)
    chat.load(ctx)
    assert ctx.messages[0].content == "integration test"

    ctrl.shutdown()
