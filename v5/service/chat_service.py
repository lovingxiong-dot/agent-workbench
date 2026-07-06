"""v5 聊天服务包装层：对外纯 Python 接口。"""
from typing import Callable

from v5.service.adapter import V5Adapter


class ChatService:
    """封装 V5Adapter，将底层 Qt 信号隔离为普通 Python 回调。"""

    def __init__(self, adapter: V5Adapter):
        self._adapter = adapter
        self._on_user: Callable[[str], None] = lambda text: None
        self._on_ai: Callable[[str, str], None] = lambda text, phase: None
        self._on_chunk: Callable[[str], None] = lambda text: None
        self._on_stream_end: Callable[[], None] = lambda: None
        self._on_terminal: Callable[[str], None] = lambda text: None
        self._last_session_id: str = ""

    def set_callbacks(
        self,
        on_user: Callable[[str], None] = None,
        on_ai: Callable[[str, str], None] = None,
        on_chunk: Callable[[str], None] = None,
        on_stream_end: Callable[[], None] = None,
        on_terminal: Callable[[str], None] = None,
    ):
        if on_user:
            self._on_user = on_user
        if on_ai:
            self._on_ai = on_ai
        if on_chunk:
            self._on_chunk = on_chunk
        if on_stream_end:
            self._on_stream_end = on_stream_end
        if on_terminal:
            self._on_terminal = on_terminal

        self._adapter.set_callbacks(
            on_user=self._on_user,
            on_ai=self._on_ai,
            on_chunk=self._on_chunk,
            on_stream_end=self._on_stream_end,
            on_terminal=self._on_terminal,
            on_open_file=lambda path: None,
            on_load_url=lambda url: None,
            on_switch_tab=lambda tab: None,
        )

    def create_session(
        self,
        session_type: str,
        model: str,
        mode: str,
        project_path: str,
    ):
        self._adapter.emit_session_create(
            session_type=session_type,
            model=model,
            mode=mode,
            project_path=project_path,
        )

    def switch_session(self, session_id: str):
        self._last_session_id = session_id
        self._adapter.emit_session_switch(session_id)

    def delete_session(self, session_id: str):
        self._adapter.emit_session_delete(session_id)
        if self._last_session_id == session_id:
            self._last_session_id = ""

    def send_message(
        self,
        session_id: str,
        text: str,
        model: str,
        mode: str,
        session_type: str,
        project_path: str,
    ):
        self._last_session_id = session_id
        self._adapter.emit_user_send(
            session_id=session_id,
            text=text,
            model=model,
            mode=mode,
            session_type=session_type,
            project_path=project_path,
        )

    def stop_message(self):
        if self._last_session_id:
            self._adapter.emit_user_stop(self._last_session_id)

    def run_terminal_command(self, command: str, cwd: str = ""):
        self._adapter.run_terminal_command(command, cwd)
