"""V5 Service 层单元测试。"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.service.config_service import ConfigService
from v5.service.session_service import SessionService
from v5.service.chat_service import ChatService
from v5.service.adapter import V5Adapter


class TestV5ConfigService:
    def test_get_set_save(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n  theme: dark\n", encoding="utf-8")
        cfg = ConfigService(config_path=str(cfg_path))

        assert cfg.get("app.version") == "v5-test"
        cfg.set("app.theme", "light")
        cfg.save()

        cfg2 = ConfigService(config_path=str(cfg_path))
        assert cfg2.get("app.theme") == "light"


class TestV5SessionService:
    def test_create_list_delete(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))

        sessions = svc.list_sessions()
        assert sessions == []

        sid = svc.create_session(session_type="chat", model="tool-agent", mode="ask")
        assert sid
        sessions = svc.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == sid

        svc.delete_session(sid)
        assert svc.list_sessions() == []

    def test_get_session_returns_none_for_unknown(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))
        assert svc.get_session("nonexistent") is None


class TestV5ChatService:
    def test_callbacks_registration(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)

        called = {}

        def on_user(text):
            called["user"] = text

        def on_ai(text, phase=""):
            called["ai"] = (text, phase)

        chat.set_callbacks(on_user=on_user, on_ai=on_ai)
        adapter._on_user("hello")
        adapter._on_ai("world", "think")

        assert called["user"] == "hello"
        assert called["ai"] == ("world", "think")
