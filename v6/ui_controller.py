"""v6/ui_controller.py — UI 与业务唯一桥梁（当前为纯信号桥接 + Demo 状态）。
设计来源：docs/v6/SPEC.md 第 3 节。"""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from v6.runtime.stub_runtime import EchoRuntime
from v6.ui.base import theme


class UIController(QObject):
    """接收 MainWindow 的 UI 事件，转发为 UI 更新信号；维护当前会话/模式/模型状态。"""

    # → MainWindow → LeftPanel
    sign_update_sessions = Signal(list)
    sign_set_active_session = Signal(str)
    sign_theme_changed = Signal(str)

    # → MainWindow → ChatArea
    sign_set_title = Signal(str, str)
    sign_chat_user = Signal(str)
    sign_chat_ai = Signal(str, str)
    sign_stream_chunk = Signal(str)
    sign_stream_end = Signal()
    sign_set_streaming = Signal(bool)
    sign_tool_executed = Signal(str, dict, str, int)
    sign_confirm_required = Signal(str, str)
    sign_show_analyze_button = Signal(bool)

    # → MainWindow → RightPanel
    sign_open_file = Signal(str)
    sign_update_terminal = Signal(str)
    sign_switch_tab = Signal(str)

    DEMO_SESSIONS = [
        ("today", "今天", [
            {"sid": "s1", "title": "V6 架构讨论", "preview": "讨论 UI 分层与信号契约", "time": "10:23"},
            {"sid": "s2", "title": "base.py 实现", "preview": "主题系统与基础工具", "time": "09:15"},
        ]),
        ("yesterday", "昨天", [
            {"sid": "s3", "title": "窗口无边框方案", "preview": "FramelessWindowHelper 与边缘拖拽", "time": "昨天"},
            {"sid": "s4", "title": "AppleMenu 设计", "preview": "圆角阴影弹出菜单", "time": "昨天"},
        ]),
        ("last7", "最近 7 天", [
            {"sid": "s5", "title": "pytest smoke 测试", "preview": "验证所有模块可导入", "time": "周一"},
            {"sid": "s6", "title": "主题切换动画", "preview": "深浅色主题即时切换", "time": "周日"},
        ]),
    ]

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sessions = [list(g) for g in self.DEMO_SESSIONS]
        self._active_sid = "s1"
        self._mode = "Agent"
        self._model = "gpt-4o"
        self._runtime = EchoRuntime()

    def startup(self) -> None:
        self.sign_update_sessions.emit(self._sessions)
        self.sign_set_active_session.emit(self._active_sid)
        self.sign_set_title.emit("项目分析助手", "f:\\Agent\\agent_workbench")
        self.sign_show_analyze_button.emit(True)

    def _find_session(self, sid: str) -> dict | None:
        for _, _, items in self._sessions:
            for s in items:
                if s["sid"] == sid:
                    return s
        return None

    def on_session_selected(self, sid: str) -> None:
        self._active_sid = sid
        self.sign_set_active_session.emit(sid)
        s = self._find_session(sid)
        if s:
            self.sign_set_title.emit(s["title"], "f:\\Agent\\agent_workbench")

    def on_new_session(self) -> None:
        import uuid

        sid = f"s{uuid.uuid4().hex[:6]}"
        self._sessions[0][2].insert(0, {"sid": sid, "title": "新会话", "preview": "", "time": "刚刚"})
        self._active_sid = sid
        self.sign_update_sessions.emit(self._sessions)
        self.sign_set_active_session.emit(sid)
        self.sign_set_title.emit("新会话", "f:\\Agent\\agent_workbench")

    def on_session_action(self, action: str, sid: str) -> None:
        if action == "delete":
            for group in self._sessions:
                group[2][:] = [s for s in group[2] if s["sid"] != sid]
        elif action == "pin":
            s = self._find_session(sid)
            if s:
                s["title"] = "📌 " + s["title"].lstrip("📌 ")
        self.sign_update_sessions.emit(self._sessions)

    def on_search_text_changed(self, text: str) -> None:
        text = text.lower()
        filtered = []
        for gid, title, items in self._sessions:
            kept = [s for s in items if text in s["title"].lower() or text in s["preview"].lower()]
            if kept:
                filtered.append((gid, title, kept))
        self.sign_update_sessions.emit(filtered if text else self._sessions)

    def on_theme_toggled(self, name: str) -> None:
        theme.set_theme(name)
        self.sign_theme_changed.emit(name)

    def on_file_selected(self, path: str) -> None:
        self.sign_open_file.emit(path)

    def on_send_msg(self, text: str) -> None:
        self.sign_chat_user.emit(text)
        self.sign_set_streaming.emit(True)

        def _on_event(event: str, payload: dict) -> None:
            if event == "ai_chunk":
                self.sign_chat_ai.emit(payload["text"], "")
            elif event == "ai_end":
                self.sign_stream_end.emit()

        QTimer.singleShot(50, lambda: self._runtime.send_chat(text, _on_event))

    def on_stop_msg(self) -> None:
        self.sign_set_streaming.emit(False)

    def on_mode_changed(self, mode: str) -> None:
        self._mode = mode

    def on_model_changed(self, model: str) -> None:
        self._model = model

    def on_export_requested(self) -> None:
        pass

    def on_settings_requested(self) -> None:
        pass

    def on_search_toggled(self) -> None:
        pass

    def on_more_clicked(self, pos: object) -> None:
        pass

    def on_open_file(self, path: str) -> None:
        self.sign_open_file.emit(path)

    def on_load_url(self, url: str) -> None:
        self.sign_update_terminal.emit(f"加载 URL: {url}\n")

    def on_terminal_command(self, command: str) -> None:
        self.sign_update_terminal.emit(f"$ {command}\n")

    def on_tab_closed(self, tab_type: str) -> None:
        pass
