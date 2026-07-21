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

    def test_callback_tool_executed(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)

        called = {}
        chat.set_callbacks(on_tool_executed=lambda name, args, result, elapsed: called.update({"name": name, "args": args, "result": result, "elapsed": elapsed}))
        adapter._on_tool_executed("read_file", {"path": "/tmp/a"}, "content", 42)

        assert called["name"] == "read_file"
        assert called["args"] == {"path": "/tmp/a"}
        assert called["result"] == "content"
        assert called["elapsed"] == 42

    def test_callback_confirm(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)

        called = {}
        chat.set_callbacks(on_confirm=lambda tool_name, command: called.update({"tool": tool_name, "cmd": command}))
        adapter._on_confirm_required("bash", "rm -rf /tmp")

        assert called["tool"] == "bash"
        assert called["cmd"] == "rm -rf /tmp"

    def test_confirm_result_forwards_to_adapter(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\nmanual_modes:\n  ask:\n    system_prompt: ''\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)

        # 没有 worker 时不应抛异常
        chat.confirm_result("nonexistent", True)

    def test_create_session_forwards(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)
        chat = ChatService(adapter=adapter)

        chat.create_session(session_type="work", model="flash", mode="plan", project_path="/tmp")
        sessions = session_svc.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_type == "work"


class TestV5ConfigServiceMore:
    def test_get_default_fallback(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")
        cfg = ConfigService(config_path=str(cfg_path))
        assert cfg.get("app.missing", "default") == "default"

    def test_raw_config_returns_dict(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\nmanual_modes:\n  ask:\n    system_prompt: hi\n", encoding="utf-8")
        cfg = ConfigService(config_path=str(cfg_path))
        raw = cfg.raw_config
        assert isinstance(raw, dict)
        assert raw.get("app", {}).get("version") == "v5-test"
        assert "ask" in raw.get("manual_modes", {})

    def test_save_persists_nested_value(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")
        cfg = ConfigService(config_path=str(cfg_path))
        cfg.set("app.last_mode", "craft")
        cfg.save()

        cfg2 = ConfigService(config_path=str(cfg_path))
        assert cfg2.get("app.last_mode") == "craft"


class TestV5SessionServiceMore:
    def test_rename_session_updates_title(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))
        sid = svc.create_session(session_type="chat", model="tool-agent", mode="ask")
        assert svc.rename_session(sid, "新标题")
        session = svc.get_session(sid)
        assert session.title == "新标题"

    def test_pin_session(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))
        sid = svc.create_session(session_type="chat", model="tool-agent", mode="ask")
        assert svc.pin_session(sid, True)
        session = svc.get_session(sid)
        assert session.pinned is True

    def test_add_and_list_messages(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))
        sid = svc.create_session(session_type="chat", model="tool-agent", mode="ask")
        assert svc.add_message(sid, "user", "hello")
        assert svc.add_message(sid, "ai", "world")
        messages = svc.list_messages(sid)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "ai"

    def test_delete_session_cascades_meta(self, tmp_path):
        db_path = tmp_path / "test.db"
        svc = SessionService(db_path=str(db_path))
        sid = svc.create_session(session_type="work", model="flash", mode="plan")
        svc.pin_session(sid, True)
        assert svc.delete_session(sid)
        assert svc.get_session(sid) is None
        assert svc.list_sessions() == []


class TestV5AdapterMore:
    def test_emit_session_rename(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)

        sid = session_svc.create_session(session_type="chat", model="tool-agent", mode="ask")
        adapter.emit_session_rename(sid, "改名后")
        session = session_svc.get_session(sid)
        assert session.title == "改名后"

    def test_set_callbacks_defaults(self, tmp_path):
        db_path = tmp_path / "test.db"
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("app:\n  version: v5-test\n", encoding="utf-8")

        cfg = ConfigService(config_path=str(cfg_path))
        session_svc = SessionService(db_path=str(db_path))
        adapter = V5Adapter(config=cfg, session_service=session_svc)

        # 默认回调不应抛异常
        adapter._on_user("x")
        adapter._on_ai("y", "z")
        adapter._on_chunk("c")
        adapter._on_stream_end()
        adapter._on_terminal("t")
        adapter._on_tool_executed("n", {}, "r", 1)
        adapter._on_confirm_required("bash", "cmd")
        adapter._on_open_file("p")
        adapter._on_load_url("u")
        adapter._on_switch_tab("browser")
