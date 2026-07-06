"""tests/v6/test_v6_services.py — Services 层单元与集成测试。"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["test"])
    yield app


def test_config_service_reads_and_writes(tmp_path, qapp):
    from v6.config_manager import ConfigManager
    from v6.services.config_service import ConfigService

    svc = ConfigService(data_dir=tmp_path)
    assert svc.theme() == "dark"
    assert svc.last_mode() == "Agent"
    assert svc.last_model() == "gpt-4o"
    assert svc.window_geometry() is None

    svc.set_theme("light")
    svc.set_last_mode("Coder")
    svc.set_last_model("claude-3")
    svc.set_window_geometry({"x": 100, "y": 200})

    cm = ConfigManager(data_dir=tmp_path)
    assert cm.get("theme.name") == "light"
    assert cm.get("app.last_mode") == "Coder"
    assert cm.get("app.last_model") == "claude-3"
    assert cm.get("window.geometry") == {"x": 100, "y": 200}


def test_session_service_create_and_groups(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    assert svc.load_groups() == []

    sid = svc.create("new session")
    assert svc.get_active() == sid

    groups = svc.load_groups()
    assert len(groups) == 1
    assert groups[0][0] == "today"
    assert groups[0][2][0]["sid"] == sid
    assert groups[0][2][0]["title"] == "new session"


def test_session_service_delete_clears_active(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    sid = svc.create("to delete")
    assert svc.get_active() == sid
    svc.delete(sid)
    assert svc.get_active() is None
    assert svc.load_groups() == []


def test_session_service_pin_and_rename(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    sid = svc.create("pin me")
    assert svc.pin(sid) is True
    assert svc.manager.get(sid)["is_pinned"] is True
    svc.rename(sid, "renamed")
    assert svc.manager.get(sid)["title"] == "renamed"


def test_session_service_search(tmp_path, qapp):
    from v6.services.session_service import SessionService

    svc = SessionService(data_dir=tmp_path)
    sid_apple = svc.create("apple pie")
    svc.create("banana")

    # 更新 preview 以测试预览搜索
    svc.manager.touch(sid_apple, "apple preview")

    groups = svc.search("apple")
    assert len(groups) == 1
    assert len(groups[0][2]) == 1
    assert groups[0][2][0]["sid"] == sid_apple

    assert svc.search("zzzz") == []
    # 空搜索返回全部分组
    assert len(svc.search("")) == 1


def test_chat_service_append_and_load(tmp_path, qapp):
    from v6.session_manager import SessionManager
    from v6.services.chat_service import ChatService

    sm = SessionManager(data_dir=tmp_path)
    chat = ChatService(session_manager=sm)
    sid = sm.create("chat")

    chat.append_message(sid, "user", "hello")
    chat.append_message(sid, "ai", "world")

    history = chat.load_history(sid)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "ai"
    assert history[1]["content"] == "world"

    # 同步更新会话 preview
    assert sm.get(sid)["preview"] == "world"


def test_chat_service_delete_history(tmp_path, qapp):
    from v6.session_manager import SessionManager
    from v6.services.chat_service import ChatService

    sm = SessionManager(data_dir=tmp_path)
    chat = ChatService(session_manager=sm)
    sid = sm.create("chat")
    chat.append_message(sid, "user", "msg")
    assert len(chat.load_history(sid)) == 1
    chat.delete_history(sid)
    assert chat.load_history(sid) == []


def test_services_integration_with_ui_controller(tmp_path, qapp):
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

    sid = sess.create("integration")
    sess.set_active(sid)

    sessions_signal = []
    active_signal = []
    ctrl.sign_update_sessions.connect(lambda g: sessions_signal.append(g))
    ctrl.sign_set_active_session.connect(lambda s: active_signal.append(s))

    ctrl.startup()
    assert sessions_signal
    assert active_signal
    assert ctrl._active_sid == active_signal[-1]

    ctrl.on_send_msg("integration test")
    assert chat.load_history(ctrl._active_sid)[0]["content"] == "integration test"
