"""V5 端到端集成测试。

覆盖 Controller + ChatService + SessionService + Adapter 的完整链路：
创建会话 → 切换会话 → 发送消息 → 接收流式 chunk → 停止生成。
Adapter 使用 Mock，避免真实 LLM 调用。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from v5.controller.work_controller import WorkController
from v5.service.chat_service import ChatService
from v5.service.config_service import ConfigService
from v5.service.session_service import SessionService


class MockAdapter(QObject):
    """模拟 V5Adapter，记录调用并支持手动触发回调。"""

    chunk_ready = Signal(str)
    result_ready = Signal(str, str)
    error_occurred = Signal(str, str)

    def __init__(self, session_service=None, parent=None):
        super().__init__(parent)
        self.calls = []
        self._callbacks = {}
        self._last_session_id = ""
        self._session_service = session_service

    def set_callbacks(self, **callbacks):
        self._callbacks = callbacks

    def emit_session_create(self, **kwargs):
        self.calls.append(("create", kwargs))

    def emit_session_switch(self, session_id: str):
        self._last_session_id = session_id
        self.calls.append(("switch", session_id))

    def emit_user_send(self, **kwargs):
        self._last_session_id = kwargs.get("session_id", "")
        self.calls.append(("send", kwargs))
        if self._session_service is not None:
            self._session_service.add_message(
                kwargs.get("session_id", ""), "user", kwargs.get("text", "")
            )
            on_user = self._callbacks.get("on_user")
            if on_user:
                on_user(kwargs.get("text", ""))

    def emit_user_stop(self, session_id: str):
        self.calls.append(("stop", session_id))

    def emit_session_delete(self, session_id: str):
        self.calls.append(("delete", session_id))

    def emit_session_rename(self, session_id: str, new_title: str):
        self.calls.append(("rename", session_id, new_title))

    def emit_session_pin(self, session_id: str, pinned: bool):
        self.calls.append(("pin", session_id, pinned))

    def run_terminal_command(self, command: str, cwd: str = ""):
        self.calls.append(("terminal", command, cwd))

    def simulate_chunk(self, text: str):
        cb = self._callbacks.get("on_chunk")
        if cb:
            cb(text)

    def simulate_ai(self, text: str, phase: str = ""):
        cb = self._callbacks.get("on_ai")
        if cb:
            cb(text, phase)
        end = self._callbacks.get("on_stream_end")
        if end:
            end()


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def tmp_config(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
app:
  version: v5.0.19-alpha
  theme: dark
  last_mode: ask
  last_model: tool-agent
manual_modes:
  ask:
    system_prompt: ask prompt
  plan:
    system_prompt: plan prompt
  craft:
    system_prompt: craft prompt
llm_providers:
  tool-agent:
    type: dummy
""",
        encoding="utf-8",
    )
    return ConfigService(str(cfg_path))


class TestV5Integration:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app, tmp_config):
        self.app = qt_app
        self.config = tmp_config
        db_path = os.path.join(os.path.dirname(self.config._svc.config_path), "test.db")
        self.session_service = SessionService(db_path)
        self.adapter = MockAdapter(session_service=self.session_service)
        self.chat_service = ChatService(self.adapter)
        self.controller = WorkController(self.config, self.session_service, self.chat_service)

        self.signals = {
            "user": [],
            "ai": [],
            "chunk": [],
            "stream_end": [],
            "streaming": [],
            "sessions": [],
            "active": [],
            "title": [],
        }
        self.controller.sign_chat_user.connect(self.signals["user"].append)
        self.controller.sign_chat_ai.connect(lambda t, p: self.signals["ai"].append((t, p)))
        self.controller.sign_stream_chunk.connect(self.signals["chunk"].append)
        self.controller.sign_stream_end.connect(lambda: self.signals["stream_end"].append(True))
        self.controller.sign_set_streaming.connect(self.signals["streaming"].append)
        self.controller.sign_update_sessions.connect(self.signals["sessions"].append)
        self.controller.sign_set_active_session.connect(self.signals["active"].append)
        self.controller.sign_set_title.connect(lambda t, p: self.signals["title"].append((t, p)))

    def test_create_chat_session(self):
        self.controller.handle_create_chat("chat")
        self.app.processEvents()
        assert self.controller._active_session_id
        assert self.signals["active"]
        assert self.signals["title"]
        assert self.signals["sessions"]

    def test_switch_session_loads_title(self):
        self.controller.handle_create_chat("chat")
        self.app.processEvents()
        sid = self.controller._active_session_id
        # 创建第二个会话后切换回第一个
        self.controller.handle_create_chat("chat")
        self.controller.handle_switch_session(sid)
        self.app.processEvents()
        assert self.controller._active_session_id == sid

    def test_send_message_persists_and_emits_user_signal(self):
        self.controller.handle_create_chat("chat")
        self.app.processEvents()
        sid = self.controller._active_session_id

        self.controller.handle_send_message("hello integration")
        self.app.processEvents()

        assert "hello integration" in self.signals["user"]
        assert True in self.signals["streaming"]
        messages = self.session_service.list_messages(sid)
        assert any(m["role"] == "user" and m["content"] == "hello integration" for m in messages)

    def test_stream_chunk_and_finalize(self):
        self.controller.handle_create_chat("chat")
        self.app.processEvents()

        self.controller.handle_send_message("hello")
        self.app.processEvents()

        self.adapter.simulate_chunk("chunk1")
        self.adapter.simulate_chunk("chunk2")
        self.adapter.simulate_ai("final answer", "")
        self.app.processEvents()

        assert self.signals["chunk"] == ["chunk1", "chunk2"]
        assert self.signals["ai"] == [("final answer", "")]
        assert self.signals["stream_end"]

    def test_stop_message_clears_streaming(self):
        self.controller.handle_create_chat("chat")
        self.app.processEvents()
        self.controller.handle_send_message("hello")
        self.app.processEvents()

        assert self.controller._streaming is True
        self.controller.handle_stop_message()
        self.app.processEvents()
        assert self.controller._streaming is False
        assert self.signals["streaming"] == [True, False]
        assert any(c[0] == "stop" for c in self.adapter.calls)

    def test_mode_change_persists(self):
        self.controller.handle_mode_changed("plan")
        assert self.controller._current_mode == "plan"
        assert self.config.get("app.last_mode") == "plan"

    def test_model_change_persists(self):
        self.controller.handle_model_changed("flash")
        assert self.controller._current_model == "flash"
        assert self.config.get("app.last_model") == "flash"
