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
    assert session["preview"] == ""
    assert session["is_active"] is False
    assert session["is_pinned"] is False


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


def test_rename(sm):
    sid = sm.create("old")
    sm.rename(sid, "new")
    assert sm.get(sid)["title"] == "new"


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
