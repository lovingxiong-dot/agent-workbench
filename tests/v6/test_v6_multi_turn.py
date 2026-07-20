"""tests/v6/test_v6_multi_turn.py — 多轮上下文验证。

覆盖：
- SessionModule 消息增删查持久化
- 多轮对话历史正确传递
- Session 跨重启恢复
- Session/Context/History/Memory 边界验证
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest import mock

import pytest

from v6.runtime.types import ChatMessage


# ────────────────────────── SessionModule 单元测试 ──────────────────────────

@pytest.fixture
def session_module():
    """创建独立 SessionModule，使用临时目录。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 重定向数据目录到临时路径
        import agent_workbench.runtime.modules.session_module as sm_mod
        original_dir = sm_mod._SESSION_DATA_DIR
        original_file = sm_mod._LAST_SESSION_FILE
        sm_mod._SESSION_DATA_DIR = Path(tmpdir)
        sm_mod._LAST_SESSION_FILE = Path(tmpdir) / "_last_session.txt"

        sm = sm_mod.SessionModule()
        sm.initialize(mock.MagicMock())
        yield sm

        sm_mod._SESSION_DATA_DIR = original_dir
        sm_mod._LAST_SESSION_FILE = original_file


class TestSessionModulePersistence:
    """SessionModule 持久化单元测试。"""

    def test_append_and_history(self, session_module):
        """追加消息后，history 应返回正确内容。"""
        sid = "test-session-1"
        session_module.start_session(sid)

        session_module.append(sid, [
            ChatMessage(role="user", content="你好"),
            ChatMessage(role="assistant", content="你好！有什么可以帮助你的？"),
        ])

        history = session_module.history(sid)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "你好"
        assert history[1]["role"] == "assistant"

    def test_persist_and_load(self, session_module):
        """持久化后再加载，消息应完整恢复。"""
        sid = "test-session-2"
        session_module.start_session(sid)

        session_module.append(sid, [
            ChatMessage(role="user", content="第一轮"),
            ChatMessage(role="assistant", content="回复第一轮"),
        ])
        session_module.persist()

        # 创建新 SessionModule 模拟重启
        import agent_workbench.runtime.modules.session_module as sm_mod
        sm2 = sm_mod.SessionModule()
        sm2.initialize(mock.MagicMock())

        msgs = sm2.load(sid)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "第一轮"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == "回复第一轮"

    def test_load_last_active(self, session_module):
        """load_last_active 应恢复上次活跃会话。"""
        sid = "test-session-active"
        session_module.start_session(sid)
        session_module.append(sid, [
            ChatMessage(role="user", content="hello"),
        ])
        session_module.save_last_active()

        # 新 SessionModule 模拟重启
        import agent_workbench.runtime.modules.session_module as sm_mod
        sm2 = sm_mod.SessionModule()
        sm2.initialize(mock.MagicMock())

        restored = sm2.load_last_active()
        assert restored == sid
        history = sm2.history(sid)
        assert len(history) == 1
        assert history[0]["content"] == "hello"

    def test_clear_removes_disk_file(self, session_module):
        """清除 Session 应删除磁盘文件。"""
        sid = "test-session-clear"
        session_module.start_session(sid)
        session_module.append(sid, [ChatMessage(role="user", content="data")])
        session_module.persist()

        session_module.clear(sid)

        # 验证文件已被删除
        import agent_workbench.runtime.modules.session_module as sm_mod
        filepath = sm_mod._SESSION_DATA_DIR / f"session_{sid}.json"
        assert not filepath.exists()

    def test_append_deduplication(self, session_module):
        """重复追加相同消息应跳过。"""
        sid = "test-dedup"
        session_module.start_session(sid)

        msg = ChatMessage(role="user", content="test")
        session_module.append(sid, [msg])
        session_module.append(sid, [msg])  # 重复

        history = session_module.history(sid)
        assert len(history) == 1

    def test_multi_turn_history_accumulation(self, session_module):
        """5 轮对话后，history 应包含全部 10 条消息。"""
        sid = "test-multi-turn"
        session_module.start_session(sid)

        for i in range(5):
            session_module.append(sid, [
                ChatMessage(role="user", content=f"问题{i+1}"),
                ChatMessage(role="assistant", content=f"回答{i+1}"),
            ])

        history = session_module.history(sid)
        assert len(history) == 10
        assert history[0]["content"] == "问题1"
        assert history[9]["content"] == "回答5"

    def test_history_limit(self, session_module):
        """history 的 limit 参数应截断结果。"""
        sid = "test-limit"
        session_module.start_session(sid)

        for i in range(10):
            session_module.append(sid, [
                ChatMessage(role="user", content=f"msg{i}"),
            ])

        history = session_module.history(sid, limit=3)
        assert len(history) == 3
        # 应返回最后 3 条
        assert history[0]["content"] == "msg7"
        assert history[2]["content"] == "msg9"


# ────────────────────────── 多轮上下文边界验证 ──────────────────────────

class TestMultiTurnBoundaries:
    """验证 Session/Context/History/Memory 边界正确分离。"""

    def test_session_module_does_not_access_memory(self, session_module):
        """SessionModule 不应访问 MemoryModule — 边界验证。"""
        assert not hasattr(session_module, "_memory")
        assert not hasattr(session_module, "memory")

    def test_session_module_does_not_access_capability(self, session_module):
        """SessionModule 不应直接访问 Capability — 边界验证。"""
        assert not hasattr(session_module, "_capability_registry")
        assert not hasattr(session_module, "capability")

    def test_session_data_is_per_session(self, session_module):
        """不同 Session 的数据应完全隔离。"""
        sid_a = "session-a"
        sid_b = "session-b"

        session_module.start_session(sid_a)
        session_module.append(sid_a, [ChatMessage(role="user", content="A")])

        session_module.start_session(sid_b)
        session_module.append(sid_b, [ChatMessage(role="user", content="B")])

        assert len(session_module.history(sid_a)) == 1
        assert session_module.history(sid_a)[0]["content"] == "A"
        assert len(session_module.history(sid_b)) == 1
        assert session_module.history(sid_b)[0]["content"] == "B"

    def test_json_file_is_valid_and_readable(self, session_module):
        """持久化文件应可被标准 JSON 解析器读取。"""
        sid = "test-json-format"
        session_module.start_session(sid)
        session_module.append(sid, [
            ChatMessage(role="user", content="中文消息"),
            ChatMessage(role="assistant", content="English reply"),
        ])
        session_module.persist()

        import agent_workbench.runtime.modules.session_module as sm_mod
        filepath = sm_mod._SESSION_DATA_DIR / f"session_{sid}.json"
        assert filepath.exists()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "中文消息"
        assert data[1]["role"] == "assistant"
        assert data[1]["content"] == "English reply"


# ────────────────────────── 跨重启恢复验证 ──────────────────────────

class TestSessionRestart:
    """模拟重启场景，验证 Session 完整恢复。"""

    def test_five_rounds_survive_restart(self, session_module):
        """5 轮对话后重启，消息应完整恢复。"""
        sid = "restart-test"
        session_module.start_session(sid)

        rounds = 5
        for i in range(rounds):
            session_module.append(sid, [
                ChatMessage(role="user", content=f"Q{i+1}"),
                ChatMessage(role="assistant", content=f"A{i+1}"),
            ])
        session_module.persist()
        session_module.save_last_active()

        # 模拟重启
        import agent_workbench.runtime.modules.session_module as sm_mod
        sm2 = sm_mod.SessionModule()
        sm2.initialize(mock.MagicMock())

        restored_sid = sm2.load_last_active()
        assert restored_sid == sid

        history = sm2.history(sid)
        assert len(history) == rounds * 2
        assert history[0]["content"] == "Q1"
        assert history[-1]["content"] == f"A{rounds}"

    def test_empty_session_restart(self, session_module):
        """空 Session 重启不应崩溃。"""
        sid = "empty-restart"
        session_module.start_session(sid)
        session_module.save_last_active()

        # 验证文件已写入
        import agent_workbench.runtime.modules.session_module as sm_mod
        assert sm_mod._LAST_SESSION_FILE.exists()
        content = sm_mod._LAST_SESSION_FILE.read_text(encoding="utf-8").strip()
        assert content == sid

    def test_no_previous_session(self, session_module):
        """无历史 Session 时 load_last_active 应返回 None。"""
        import agent_workbench.runtime.modules.session_module as sm_mod
        # 删除 _last_session_file
        if sm_mod._LAST_SESSION_FILE.exists():
            sm_mod._LAST_SESSION_FILE.unlink()

        assert sm_mod._LAST_SESSION_FILE.exists() is False
        assert session_module.load_last_active() is None