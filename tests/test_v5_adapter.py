"""V5 适配器单元测试。

覆盖 V5Adapter 回调注册、会话操作转发、终端命令、消息总线事件。
Worker 创建涉及真实 LLM 初始化，测试中通过 monkeypatch 隔离。
"""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtWidgets import QApplication

from v5.service.adapter import V5Adapter
from v5.service.config_service import ConfigService


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
user_rules:
  - rule1
agent:
  ask:
    max_tool_rounds: 4
    task_timeout: 60.0
    llm_timeout: 30.0
    tool_timeout: 10.0
llm_providers:
  tool-agent:
    type: dummy
""",
        encoding="utf-8",
    )
    return ConfigService(str(cfg_path))


class MockSessionService:
    def __init__(self):
        self.messages = []
        self.created = []
        self.renamed = []
        self.pinned = []

    def add_message(self, session_id: str, role: str, content: str):
        self.messages.append((session_id, role, content))

    def list_messages(self, session_id: str):
        return [{"role": "user", "content": "hello", "session_id": session_id}]

    def create_session(self, **kwargs):
        self.created.append(kwargs)
        return "sid-" + kwargs.get("session_type", "chat")

    def rename_session(self, session_id: str, new_title: str):
        self.renamed.append((session_id, new_title))

    def pin_session(self, session_id: str, pinned: bool):
        self.pinned.append((session_id, pinned))


class TestV5Adapter:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app, tmp_config):
        self.app = qt_app
        self.config = tmp_config
        self.sessions = MockSessionService()
        self.adapter = V5Adapter(self.config, self.sessions)

    def test_adapter_init_creates_engines(self):
        assert isinstance(self.adapter._engines, dict)

    def test_adapter_set_callbacks(self):
        called = {}
        self.adapter.set_callbacks(
            on_user=lambda t: called.update({"user": t}),
            on_ai=lambda t, p: called.update({"ai": (t, p)}),
            on_chunk=lambda t: called.update({"chunk": t}),
            on_stream_end=lambda: called.update({"end": True}),
            on_terminal=lambda t: called.update({"terminal": t}),
        )
        self.adapter._on_user("u")
        self.adapter._on_chunk("c")
        self.adapter._on_stream_end()
        assert called["user"] == "u"
        assert called["chunk"] == "c"
        assert called["end"] is True

    def test_adapter_emit_user_send_adds_message(self):
        self.adapter._get_llm = MagicMock(return_value=MagicMock())
        self.adapter.emit_user_send("sid-1", "hello", "tool-agent", "ask", "chat", "")
        assert ("sid-1", "user", "hello") in self.sessions.messages

    def test_adapter_emit_user_send_triggers_user_callback(self):
        received = []
        self.adapter.set_callbacks(on_user=received.append)
        self.adapter._get_llm = MagicMock(return_value=MagicMock())
        self.adapter.emit_user_send("sid-1", "hello", "tool-agent", "ask", "chat", "")
        assert received == ["hello"]

    def test_adapter_emit_user_send_ignores_empty(self):
        self.adapter._get_llm = MagicMock()
        self.adapter.emit_user_send("sid-1", "   ", "tool-agent", "ask", "chat", "")
        self.adapter._get_llm.assert_not_called()

    def test_adapter_emit_session_create(self):
        self.adapter.emit_session_create("chat", "tool-agent", "ask", "/tmp")
        assert len(self.sessions.created) == 1
        assert self.sessions.created[0]["mode"] == "ask"

    def test_adapter_emit_session_delete_without_worker(self):
        # 无 worker 时不抛异常
        self.adapter.emit_session_delete("sid-none")
        assert "sid-none" not in self.adapter._workers

    def test_adapter_get_system_prompt(self):
        assert self.adapter._get_system_prompt("ask") == "ask prompt"
        assert self.adapter._get_system_prompt("plan") == "plan prompt"
        assert self.adapter._get_system_prompt("unknown") == ""

    def test_adapter_build_workspace_context(self):
        ctx = self.adapter._build_workspace_context("sid-12345678", "/project")
        assert "/project" in ctx
        assert "sid-12345678"[:8] in ctx

    def test_adapter_build_context(self):
        ctx = self.adapter._build_context("/project")
        assert "当前项目路径" in ctx

    def test_adapter_emit_session_rename(self):
        self.adapter.emit_session_rename("sid-1", "新标题")
        assert self.sessions.renamed == [("sid-1", "新标题")]

    def test_adapter_emit_session_pin(self):
        self.adapter.emit_session_pin("sid-1", True)
        assert self.sessions.pinned == [("sid-1", True)]

    def test_adapter_bus_open_file_callback(self):
        received = []
        self.adapter.set_callbacks(on_open_file=received.append)
        event = MagicMock()
        event.name = "open_file"
        event.path = "/tmp/file.txt"
        self.adapter._on_ui_event(event)
        assert received == ["/tmp/file.txt"]

    def test_adapter_bus_load_url_callback(self):
        received = []
        self.adapter.set_callbacks(on_load_url=received.append)
        event = MagicMock()
        event.name = "load_url"
        event.url = "https://example.com"
        self.adapter._on_ui_event(event)
        assert received == ["https://example.com"]

    def test_adapter_bus_switch_tab_callback(self):
        received = []
        self.adapter.set_callbacks(on_switch_tab=received.append)
        event = MagicMock()
        event.name = "right_panel_tab"
        event.tab_name = "terminal"
        self.adapter._on_ui_event(event)
        assert received == ["terminal"]

    def test_adapter_manual_modes_from_config(self):
        modes = self.config.raw_config.get("manual_modes", {})
        assert set(modes.keys()) == {"ask", "plan", "craft"}
