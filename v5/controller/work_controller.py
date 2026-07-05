"""v5 唯一业务中枢。"""
from PySide6.QtCore import QObject, Signal

from v5.service.config_service import ConfigService
from v5.service.session_service import SessionService
from v5.service.chat_service import ChatService
from v5.widgets.base import theme


class WorkController(QObject):
    # Controller -> UI
    sign_update_sessions = Signal(list)
    sign_set_active_session = Signal(str)
    sign_set_title = Signal(str, str)
    sign_chat_user = Signal(str)
    sign_chat_ai = Signal(str, str)
    sign_stream_chunk = Signal(str)
    sign_stream_end = Signal()
    sign_set_streaming = Signal(bool)
    sign_open_file_right = Signal(str)
    sign_update_terminal = Signal(str)
    sign_switch_tab = Signal(str)

    def __init__(
        self,
        config: ConfigService,
        session_service: SessionService,
        chat_service: ChatService,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._session_service = session_service
        self._chat_service = chat_service

        self._active_session_id: str = ""
        self._current_mode: str = config.get("app.last_mode", "ask")
        self._current_model: str = config.get("app.last_model", "tool-agent")
        self._draft_session_type: str = "chat"
        self._draft_project_path: str = ""
        self._streaming: bool = False

        self._chat_service.set_callbacks(
            on_user=lambda text: self.sign_chat_user.emit(text),
            on_ai=lambda text, phase="": self.sign_chat_ai.emit(text, phase),
            on_chunk=lambda text: self.sign_stream_chunk.emit(text),
            on_stream_end=lambda: self.sign_stream_end.emit(),
            on_terminal=lambda text: self.sign_update_terminal.emit(text),
        )

    # ---------- UI -> Controller 处理 ----------

    def handle_create_chat(self, session_type: str):
        self._draft_session_type = session_type
        sid = self._session_service.create_session(
            session_type=session_type,
            model=self._current_model,
            mode=self._current_mode,
            project_path=self._draft_project_path,
        )
        self._refresh_sessions()
        self.handle_switch_session(sid)

    def handle_switch_session(self, sid: str):
        self._active_session_id = sid
        self._config.set("app.last_session_id", sid)
        self._config.save()
        self.sign_set_active_session.emit(sid)
        session = self._session_service.get_session(sid)
        if session:
            self._draft_session_type = session.session_type or "chat"
            self._draft_project_path = session.project_path or ""
            self.sign_set_title.emit(session.title or "新会话", self._draft_project_path)
        else:
            self.sign_set_title.emit("新会话", "")

    def handle_session_action(self, action: str, sid: str):
        if action == "delete":
            self._session_service.delete_session(sid)
            if self._active_session_id == sid:
                self._active_session_id = ""
                self.sign_set_active_session.emit("")
                self.sign_set_title.emit("新会话", "")
        elif action == "rename":
            # rename is handled via UI prompt -> controller callback
            return
        elif action == "pin":
            self._session_service.pin_session(sid)
        self._refresh_sessions()

    def handle_search_input(self, text: str):
        sessions = self._session_service.list_sessions()
        text = text.strip().lower()
        if text:
            filtered = [
                s for s in sessions
                if text in (s.title or "").lower() or text in (s.preview or "").lower()
            ]
        else:
            filtered = sessions
        self.sign_update_sessions.emit(filtered)

    def handle_switch_theme(self, theme_name: str):
        theme.set_theme(theme_name)
        self._config.set("app.theme", theme_name)
        self._config.save()

    def handle_send_message(self, text: str):
        if not text.strip():
            return
        if not self._active_session_id:
            self.handle_create_chat(self._draft_session_type)
        self.sign_chat_user.emit(text)
        self._streaming = True
        self.sign_set_streaming.emit(True)
        self._chat_service.send_message(
            session_id=self._active_session_id,
            text=text,
            model=self._current_model,
            mode=self._current_mode,
            session_type=self._draft_session_type,
            project_path=self._draft_project_path,
        )

    def handle_stop_message(self):
        if self._streaming:
            self._chat_service.stop_message()
            self._streaming = False
            self.sign_set_streaming.emit(False)

    def handle_mode_changed(self, mode: str):
        self._current_mode = mode
        self._config.set("app.last_mode", mode)
        self._config.save()

    def handle_model_changed(self, model: str):
        self._current_model = model
        self._config.set("app.last_model", model)
        self._config.save()

    def handle_export_requested(self):
        # TODO: export current session to file
        pass

    def handle_settings_requested(self):
        # TODO: open settings dialog
        pass

    def handle_open_file(self, path: str):
        self.sign_open_file_right.emit(path)
        self.sign_switch_tab.emit("file")

    def handle_load_url(self, url: str):
        self._right_url = url
        self.sign_switch_tab.emit("browser")

    def handle_terminal_command(self, cmd: str):
        self._chat_service.run_terminal_command(cmd, self._draft_project_path)

    # ---------- 内部辅助 ----------

    def _refresh_sessions(self):
        sessions = self._session_service.list_sessions()
        self.sign_update_sessions.emit(sessions)

    def bootstrap(self):
        """启动时恢复状态。"""
        theme_name = self._config.get("app.theme", "dark")
        theme.set_theme(theme_name)
        self._refresh_sessions()
        last_sid = self._config.get("app.last_session_id", "")
        if last_sid and self._session_service.get_session(last_sid):
            self.handle_switch_session(last_sid)
