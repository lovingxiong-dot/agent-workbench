"""v6/ui_controller.py — UI 与业务唯一桥梁。

职责：
- 接收 MainWindow 的 UI 事件，转发为 UI 更新信号
- 维护当前会话/模式/模型等 UI 状态
- 通过 Service 层读写配置、会话、消息历史
- 不保留任何业务计算逻辑

设计来源：docs/v6/SPEC.md 第 3 节。
"""
from __future__ import annotations

import os

from PySide6.QtCore import QObject, QTimer, Signal

from v6.runtime.stub_runtime import EchoRuntime
from v6.services.chat_service import ChatService
from v6.services.config_service import ConfigService
from v6.services.session_service import SessionService
from v6.ui.base import theme


class UIController(QObject):
    """接收 UI 事件，调用 Service 层，将结果转发为 UI 更新信号。"""

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

    def __init__(
        self,
        parent: QObject | None = None,
        config_service: ConfigService | None = None,
        session_service: SessionService | None = None,
        chat_service: ChatService | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config_service or ConfigService(data_dir=data_dir)
        self._session = session_service or SessionService(data_dir=data_dir)
        self._chat = chat_service or ChatService(
            session_manager=self._session.manager, data_dir=data_dir
        )
        self._active_sid: str | None = None
        self._mode = self._config.last_mode()
        self._model = self._config.last_model()
        self._project_path = os.getcwd()
        self._streaming = False
        self._runtime = EchoRuntime()

    def startup(self) -> None:
        """应用启动：加载主题、会话列表与激活状态。"""
        theme_name = self._config.theme()
        theme.set_theme(theme_name)
        self.sign_theme_changed.emit(theme_name)

        groups = self._session.load_groups()
        self.sign_update_sessions.emit(groups)

        active = self._session.get_active()
        if active is None and groups:
            active = groups[0][2][0]["sid"]
            self._session.set_active(active)
        self._active_sid = active

        if active:
            self.sign_set_active_session.emit(active)
            self._load_session_view(active)
        else:
            self.sign_set_title.emit("项目分析助手", self._project_path)

        self.sign_show_analyze_button.emit(True)

    def _load_session_view(self, sid: str) -> None:
        """加载指定会话的标题与历史消息到 UI。"""
        session = self._session.manager.get(sid)
        title = session["title"] if session else "新会话"
        self.sign_set_title.emit(title, self._project_path)
        for msg in self._chat.load_history(sid):
            if msg["role"] == "user":
                self.sign_chat_user.emit(msg["content"])
            elif msg["role"] == "ai":
                self.sign_chat_ai.emit(msg["content"], "")

    def _reload_sessions(self) -> None:
        """重新加载会话列表并同步激活状态信号。"""
        self.sign_update_sessions.emit(self._session.load_groups())
        active = self._session.get_active()
        if active and active != self._active_sid:
            self._active_sid = active
            self.sign_set_active_session.emit(active)

    def on_session_selected(self, sid: str) -> None:
        self._active_sid = sid
        self._session.set_active(sid)
        self.sign_set_active_session.emit(sid)
        self._load_session_view(sid)

    def on_new_session(self) -> None:
        sid = self._session.create("新会话")
        self._active_sid = sid
        self.sign_update_sessions.emit(self._session.load_groups())
        self.sign_set_active_session.emit(sid)
        self.sign_set_title.emit("新会话", self._project_path)

    def on_session_action(self, action: str, sid: str) -> None:
        if action == "delete":
            self._session.delete(sid)
            if self._active_sid == sid:
                self._active_sid = self._session.get_active()
        elif action == "pin":
            self._session.pin(sid)
        elif action == "rename":
            self._session.rename(sid, "重命名会话")
        self._reload_sessions()
        if self._active_sid:
            self.sign_set_active_session.emit(self._active_sid)

    def on_search_text_changed(self, text: str) -> None:
        groups = self._session.search(text) if text.strip() else self._session.load_groups()
        self.sign_update_sessions.emit(groups)

    def on_theme_toggled(self, name: str) -> None:
        self._config.set_theme(name)
        theme.set_theme(name)
        self.sign_theme_changed.emit(name)

    def on_file_selected(self, path: str) -> None:
        self.sign_open_file.emit(path)

    def on_send_msg(self, text: str) -> None:
        if not self._active_sid:
            self.on_new_session()
        sid = self._active_sid
        if sid is None:
            return
        self._chat.append_message(sid, "user", text)
        self.sign_chat_user.emit(text)
        self.sign_set_streaming.emit(True)
        self._streaming = True
        ai_parts: list[str] = []

        def _on_event(event: str, payload: dict) -> None:
            if not self._streaming:
                return
            if event == "ai_chunk":
                ai_parts.append(payload["text"])
                self.sign_chat_ai.emit(payload["text"], "")
            elif event == "ai_end":
                full = "".join(ai_parts)
                if full:
                    self._chat.append_message(sid, "ai", full)
                self.sign_stream_end.emit()
                self.sign_set_streaming.emit(False)
                self._streaming = False

        QTimer.singleShot(50, lambda: self._runtime.send_chat(text, _on_event))

    def on_stop_msg(self) -> None:
        self._streaming = False
        self.sign_set_streaming.emit(False)

    def on_mode_changed(self, mode: str) -> None:
        self._mode = mode
        self._config.set_last_mode(mode)

    def on_model_changed(self, model: str) -> None:
        self._model = model
        self._config.set_last_model(model)

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
