"""V6 UI 层契约测试：信号存在性、公共接口与简单交互。"""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from v6.runtime.context import RuntimeContext


@pytest.fixture(autouse=True)
def reset_theme():
    from v6.ui.base import theme

    theme.set_theme("dark")
    yield
    theme.set_theme("dark")


# ── 基础组件 ──
def test_theme_manager():
    from v6.ui.base import theme, C, V6_THEMES

    assert theme.name == "dark"
    assert C["bg_primary"] == V6_THEMES["dark"]["bg_primary"]
    theme.set_theme("light")
    assert theme.name == "light"


def test_header_bar_signals(qapp):
    from v6.ui.header_bar import HeaderBar

    bar = HeaderBar()
    for name in (
        "left_expand_toggled",
        "expand_toggled",
        "search_clicked",
        "more_clicked",
        "double_clicked",
    ):
        assert hasattr(bar, name)


def test_input_area_signals(qapp):
    from v6.ui.input_area import InputArea

    area = InputArea()
    for name in (
        "send_clicked",
        "stop_clicked",
        "mode_tag_clicked",
        "model_tag_clicked",
        "skill_btn_clicked",
    ):
        assert hasattr(area, name)
    area.set_mode("Coder")
    assert area.text() == ""


# ── 左栏 ──
def test_left_panel_signals_and_update(qapp):
    from v6.ui.left_panel import LeftPanel

    panel = LeftPanel()
    for name in (
        "session_selected",
        "new_session_requested",
        "session_action",
        "search_text_changed",
        "theme_toggled",
        "file_selected",
        "tool_toggled",
        "mcp_toggled",
        "skill_clicked",
        "automation_toggled",
    ):
        assert hasattr(panel, name)
    sessions = [
        ("g1", "组1", [{"sid": "x1", "title": "t1", "preview": "p1", "time": "now"}]),
    ]
    panel.update_sessions(sessions)
    panel.set_active_session("x1")


# ── 中区 ──
def test_chat_area_signals(qapp):
    from v6.ui.chat_area import ChatArea

    chat = ChatArea()
    for name in (
        "send_msg",
        "stop_msg",
        "mode_changed",
        "model_changed",
        "export_requested",
        "settings_requested",
        "search_toggled",
        "more_clicked",
        "toggle_right_panel",
    ):
        assert hasattr(chat, name)
    chat.set_title("T", "S")
    chat.append_user("hello")
    chat.append_ai("ok")
    chat.tool_executed("list_dir", {"files": []}, "ok", 12)
    chat.set_analyze_button_visible(False)
    chat.set_analyze_button_visible(True)


def test_echo_runtime_stub():
    from v6.runtime.stub_runtime import EchoRuntime

    rt = EchoRuntime()
    events = []
    rt.send_chat("hello", lambda e, p: events.append((e, p)))
    assert [e[0] for e in events] == ["user_echo", "ai_start", "ai_chunk", "ai_end"]
    assert events[2][1]["text"].startswith("收到：")


# ── 右栏 ──
def test_right_panel_signals(qapp):
    from v6.ui.right_panel import RightPanel

    panel = RightPanel()
    for name in ("open_file", "load_url", "terminal_command", "tab_closed"):
        assert hasattr(panel, name)
    panel.show_file("demo.txt")
    panel.append_terminal("line\n")
    panel.switch_tab("terminal")


# ── UIController ──
def test_uicontroller_signals(qapp, tmp_path):
    from v6.services.session_service import SessionService
    from v6.ui_controller import UIController

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "contract"
    svc.create(ctx)
    sid = ctx.session_id
    svc.set_active(ctx)
    ctrl = UIController(session_service=svc)
    received = []
    ctrl.sign_update_sessions.connect(lambda s: received.append(("sessions", len(s))))
    ctrl.sign_set_active_session.connect(lambda s: received.append(("active", s)))
    ctrl.sign_set_title.connect(lambda t, s: received.append(("title", t)))
    ctrl.startup()
    assert any(item[0] == "sessions" for item in received)
    assert any(item == ("active", sid) for item in received)


def test_uicontroller_session_flow(qapp, tmp_path):
    from v6.services.session_service import SessionService
    from v6.ui_controller import UIController

    svc = SessionService(data_dir=tmp_path)
    ctx = RuntimeContext.new()
    ctx.metadata["session_title"] = "flow"
    svc.create(ctx)
    sid = ctx.session_id
    svc.set_active(ctx)
    ctrl = UIController(session_service=svc)
    active = []
    ctrl.sign_set_active_session.connect(lambda s: active.append(s))
    ctrl.on_session_selected(sid)
    assert active == [sid]


def test_uicontroller_send_msg(qapp, tmp_path):
    from v6.ui_controller import UIController

    ctrl = UIController(data_dir=str(tmp_path))
    user_msgs = []
    ctrl.sign_chat_user.connect(user_msgs.append)
    ctrl.on_send_msg("hi")
    assert user_msgs == ["hi"]


# ── MainWindow 装配 ──
def test_main_window_assembly(qapp):
    from v6.main_window import MainWindow

    win = MainWindow()
    assert win.centralWidget() is not None
    assert win.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    win.close()


# ── 窗口控制按钮 ──
def test_right_panel_window_buttons(qapp):
    from v6.ui.right_panel import RightPanel

    panel = RightPanel()
    called = []
    panel.set_window_buttons(
        lambda: called.append("min"),
        lambda: called.append("max"),
        lambda: called.append("close"),
    )
    assert len(called) == 0
