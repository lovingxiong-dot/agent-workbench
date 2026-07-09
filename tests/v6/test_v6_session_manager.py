"""tests/v6/test_v6_session_manager.py — SessionManager 单元测试。"""
from __future__ import annotations

import sqlite3
import time

import pytest


@pytest.fixture
def sm(tmp_path):
    from v6.session_manager import SessionManager

    yield SessionManager(data_dir=tmp_path)


def test_create_and_get(sm):
    sid = sm.create("hello")
    assert sid and isinstance(sid, str)
    session = sm.get(sid)
    assert session["title"] == "hello"
    assert session["summary"] == ""
    assert session["icon"] == ""
    assert session["workspace_id"] == ""
    assert session["last_activity"] == ""
    assert session["preview"] == ""
    assert session["is_active"] is False
    assert session["is_pinned"] is False
    assert session["pinned"] is False


def test_list_order(sm):
    sid_a = sm.create("a")
    time.sleep(0.01)
    sid_b = sm.create("b")
    sids = [s["sid"] for s in sm.list()]
    assert sids == [sid_b, sid_a]


def test_active_unique(sm):
    sid_a = sm.create("a")
    sid_b = sm.create("b")
    sm.set_active(sid_a)
    sm.set_active(sid_b)
    active_rows = [s for s in sm.list() if s["is_active"]]
    assert len(active_rows) == 1
    assert active_rows[0]["sid"] == sid_b
    assert sm.get_active() == sid_b


def test_set_active_none_clears(sm):
    sid = sm.create("x")
    sm.set_active(sid)
    assert sm.get_active() == sid
    sm.set_active(None)
    assert sm.get_active() is None
    assert all(not s["is_active"] for s in sm.list())


def test_delete(sm):
    sid = sm.create("x")
    sm.set_active(sid)
    sm.delete(sid)
    assert sm.get(sid) is None
    assert sm.get_active() is None


def test_create_with_metadata(sm):
    sid = sm.create("meta", summary="s", icon="🤖", workspace_id="chat")
    session = sm.get(sid)
    assert session["title"] == "meta"
    assert session["summary"] == "s"
    assert session["icon"] == "🤖"
    assert session["workspace_id"] == "chat"


def test_rename(sm):
    sid = sm.create("old")
    sm.rename(sid, "new")
    assert sm.get(sid)["title"] == "new"


def test_update_metadata(sm):
    sid = sm.create("x")
    sm.update_metadata(
        sid,
        title="new title",
        summary="new summary",
        icon="📊",
        workspace_id="trace",
        last_activity="typing",
    )
    session = sm.get(sid)
    assert session["title"] == "new title"
    assert session["summary"] == "new summary"
    assert session["icon"] == "📊"
    assert session["workspace_id"] == "trace"
    assert session["last_activity"] == "typing"


def test_update_metadata_partial(sm):
    sid = sm.create("x")
    sm.update_metadata(sid, summary="only summary")
    session = sm.get(sid)
    assert session["summary"] == "only summary"
    assert session["title"] == "x"


def test_migrate_old_database(tmp_path):
    """旧数据库应自动追加 Conversation 完整化所需字段。"""
    from v6.session_manager import SessionManager

    db_path = tmp_path / "sessions.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                preview TEXT DEFAULT '',
                updated_at REAL NOT NULL,
                created_at REAL NOT NULL,
                is_active INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            "INSERT INTO sessions (id, title, preview, updated_at, created_at) VALUES (?, ?, ?, ?, ?)",
            ("old", "legacy", "", time.time(), time.time()),
        )
        conn.commit()

    sm = SessionManager(data_dir=tmp_path)
    session = sm.get("old")
    assert session is not None
    assert session["summary"] == ""
    assert session["icon"] == ""
    assert session["workspace_id"] == ""
    assert session["last_activity"] == ""


def test_touch_and_preview(sm):
    sid = sm.create("x")
    sm.touch(sid, "preview text")
    session = sm.get(sid)
    assert session["preview"] == "preview text"


def test_pin_toggle(sm):
    sid = sm.create("p")
    assert sm.pin(sid) is True
    assert sm.get(sid)["is_pinned"] is True
    assert sm.pin(sid) is False
    assert sm.get(sid)["is_pinned"] is False


def test_pin_affects_list_order(sm):
    sid_old = sm.create("old")
    time.sleep(0.01)
    sid_new = sm.create("new")
    sm.pin(sid_old)
    sids = [s["sid"] for s in sm.list()]
    assert sids == [sid_old, sid_new]


def test_groups_by_time(sm):
    sid_today = sm.create("today")
    sid_yesterday = sm.create("yesterday")
    sid_old = sm.create("old")

    now = time.time()
    with sqlite3.connect(str(sm._db)) as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now - 86400, sid_yesterday),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now - 10 * 86400, sid_old),
        )
        conn.commit()

    groups = sm.groups()
    gids = [g[0] for g in groups]
    assert gids == ["today", "yesterday", "earlier"]
    assert groups[0][2][0]["sid"] == sid_today
    assert groups[1][2][0]["sid"] == sid_yesterday
    assert groups[2][2][0]["sid"] == sid_old


def test_time_format(sm):
    sid = sm.create("now")
    session = sm.get(sid)
    # 今天创建的会话应显示 HH:MM
    assert ":" in session["time"]


def test_database_isolation(tmp_path):
    from v6.session_manager import SessionManager

    sm_a = SessionManager(data_dir=tmp_path / "a")
    sm_b = SessionManager(data_dir=tmp_path / "b")
    sid_a = sm_a.create("a")
    sm_b.create("b")
    assert sm_a.get(sid_a) is not None
    assert sm_a.get("b") is None
    assert sm_b.get(sid_a) is None
