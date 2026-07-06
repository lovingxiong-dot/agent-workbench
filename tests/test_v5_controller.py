"""V5 Controller 层单元测试。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from v5.service.config_service import ConfigService
from v5.service.session_service import SessionService
from v5.service.chat_service import ChatService
from v5.service.adapter import V5Adapter
from v5.controller.work_controller import WorkController


class TestV5Controller:
    @classmethod
    def setup_class(cls):
        app = QApplication.instance() or QApplication(sys.argv)
        cls.app = app

    def _make_controller(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(
            "app:\n  version: v5-test\n  theme: dark\n  last_mode: ask\n  last_model: tool-agent\n",
            encoding="utf-8",
        )
        db_path = tmp_path / "test.db"
        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)
        return WorkController(
            config=cfg,
            session_service=session_svc,
            chat_service=chat,
        )

    def test_bootstrap_refreshes_sessions(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        received = []
        ctrl.sign_update_sessions.connect(received.append)
        ctrl.bootstrap()
        self.app.processEvents()
        assert len(received) == 1
        assert received[0] == []

    def test_create_chat_updates_sessions_and_title(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        sessions = []
        titles = []
        ctrl.sign_update_sessions.connect(sessions.append)
        ctrl.sign_set_title.connect(lambda t, p: titles.append((t, p)))

        ctrl.handle_create_chat("chat")
        self.app.processEvents()

        assert len(sessions) == 1
        assert len(sessions[0]) == 1
        assert len(titles) == 1
        assert titles[0][0] == "新会话"

    def test_switch_session_sets_active_and_title(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        sid = ctrl._session_service.create_session(session_type="work", model="flash", mode="plan")
        ctrl._session_service.rename_session(sid, "项目A")

        active = []
        titles = []
        ctrl.sign_set_active_session.connect(active.append)
        ctrl.sign_set_title.connect(lambda t, p: titles.append((t, p)))

        ctrl.handle_switch_session(sid)
        self.app.processEvents()

        assert active == [sid]
        assert titles == [("项目A", "")]

    def test_mode_changed_persists(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        ctrl.handle_mode_changed("plan")
        assert ctrl._current_mode == "plan"
        assert ctrl._config.get("app.last_mode") == "plan"

    def test_model_changed_persists(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        ctrl.handle_model_changed("deepseek-pro")
        assert ctrl._current_model == "deepseek-pro"
        assert ctrl._config.get("app.last_model") == "deepseek-pro"

    def test_theme_switch(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        from v5.widgets.base import theme
        original = theme.name
        try:
            target = "light" if original == "dark" else "dark"
            ctrl.handle_switch_theme(target)
            self.app.processEvents()
            assert theme.name == target
            assert ctrl._config.get("app.theme") == target
        finally:
            ctrl.handle_switch_theme(original)

    def test_manual_modes_match_engine(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        modes = ctrl.manual_modes
        assert isinstance(modes, list)
        assert "craft" in modes
        assert "build" not in modes
        assert "review" not in modes
        assert set(modes) == {"ask", "plan", "craft"}

    def test_tool_executed_signal_forwarded(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        received = []
        ctrl.sign_tool_executed.connect(
            lambda name, args, result, elapsed: received.append(
                {"name": name, "args": args, "result": result, "elapsed": elapsed}
            )
        )
        # 通过底层 adapter 回调触发
        ctrl._chat_service._adapter._on_tool_executed(
            "read_file", {"path": "/tmp/a"}, "content", 42
        )
        self.app.processEvents()
        assert len(received) == 1
        assert received[0]["name"] == "read_file"
        assert received[0]["args"] == {"path": "/tmp/a"}
        assert received[0]["result"] == "content"
        assert received[0]["elapsed"] == 42

    def test_confirm_required_signal_forwarded(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        received = []
        ctrl.sign_confirm_required.connect(
            lambda tool_name, command: received.append((tool_name, command))
        )
        ctrl._chat_service._adapter._on_confirm_required("bash", "rm -rf /tmp")
        self.app.processEvents()
        assert received == [("bash", "rm -rf /tmp")]

    def test_handle_confirmation_result_forwards_to_adapter(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        ctrl.handle_create_chat("chat")
        self.app.processEvents()
        sid = ctrl._active_session_id
        # 替换 adapter.set_confirm_result 为 mock，验证被调用
        called = []
        ctrl._chat_service._adapter.set_confirm_result = lambda session_id, confirmed: called.append(
            (session_id, confirmed)
        )
        ctrl.handle_confirmation_result(True)
        assert called == [(sid, True)]

    def test_handle_analyze_project_creates_work_session(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        ctrl.handle_analyze_project()
        self.app.processEvents()
        assert ctrl._draft_session_type == "work"
        assert ctrl._active_session_id
        messages = ctrl._session_service.list_messages(ctrl._active_session_id)
        assert any("分析当前项目" in m["content"] for m in messages)

    def test_handle_session_rename_updates_title(self, tmp_path):
        ctrl = self._make_controller(tmp_path)
        sid = ctrl._session_service.create_session(session_type="chat", model="tool-agent", mode="ask")
        ctrl.handle_session_rename(sid, "新标题")
        session = ctrl._session_service.get_session(sid)
        assert session.title == "新标题"
