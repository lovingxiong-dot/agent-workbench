"""v6/session_manager.py — 会话持久化管理器。

职责：
- 使用 SQLite 持久化会话（storage/sessions.db）
- 提供会话 CRUD、active 管理、时间分组
- 数据层不依赖 Qt
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from v6._paths import data_dir as _default_data_dir

_WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _format_time(ts: float) -> str:
    """根据时间戳生成友好的显示文本。"""
    dt = datetime.fromtimestamp(ts)
    today = datetime.now().date()
    if dt.date() == today:
        return dt.strftime("%H:%M")
    if dt.date() == today - timedelta(days=1):
        return "昨天"
    if dt.date() >= today - timedelta(days=6):
        return _WEEKDAY_NAMES[dt.weekday()]
    return dt.strftime("%m-%d")


class SessionManager:
    """基于 SQLite 的会话管理器。"""

    def __init__(self, data_dir: str | os.PathLike | None = None) -> None:
        self._dir = Path(data_dir) if data_dir else _default_data_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db = self._dir / "sessions.db"
        self._init_db()

    @property
    def db_path(self) -> Path:
        """返回 SQLite 数据库路径，供 ChatService 等复用。"""
        return self._db

    def _init_db(self) -> None:
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
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
            conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "sid": row["id"],
            "title": row["title"],
            "preview": row["preview"] or "",
            "updated_at": row["updated_at"],
            "created_at": row["created_at"],
            "is_active": bool(row["is_active"]),
            "is_pinned": bool(row["is_pinned"]),
            "time": _format_time(row["updated_at"]),
        }

    def create(self, title: str) -> str:
        """创建新会话并返回 sid。"""
        sid = uuid.uuid4().hex[:12]
        now = time.time()
        with sqlite3.connect(str(self._db)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "INSERT INTO sessions (id, title, preview, updated_at, created_at, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sid, title, "", now, now, 0),
            )
            conn.commit()
        return sid

    def delete(self, sid: str) -> None:
        """删除指定会话。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
            conn.commit()

    def rename(self, sid: str, title: str) -> None:
        """重命名会话并刷新更新时间。"""
        now = time.time()
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, sid),
            )
            conn.commit()

    def touch(self, sid: str, preview: str = "") -> None:
        """更新会话时间，可选更新 preview。"""
        now = time.time()
        with sqlite3.connect(str(self._db)) as conn:
            if preview:
                conn.execute(
                    "UPDATE sessions SET updated_at = ?, preview = ? WHERE id = ?",
                    (now, preview, sid),
                )
            else:
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, sid)
                )
            conn.commit()

    def list(self) -> list[dict[str, Any]]:
        """返回全部会话列表，按更新时间倒序。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM sessions ORDER BY is_pinned DESC, updated_at DESC"
            )
            return [self._row_to_dict(row) for row in cur.fetchall()]

    def get(self, sid: str) -> dict[str, Any] | None:
        """获取单个会话。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None

    def set_active(self, sid: str | None) -> None:
        """设置当前激活会话；sid 为 None 时清除激活。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute("UPDATE sessions SET is_active = 0")
            if sid is not None:
                conn.execute(
                    "UPDATE sessions SET is_active = 1 WHERE id = ?", (sid,)
                )
            conn.commit()

    def get_active(self) -> str | None:
        """返回当前激活会话 ID。"""
        with sqlite3.connect(str(self._db)) as conn:
            cur = conn.execute(
                "SELECT id FROM sessions WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            return row[0] if row else None

    def pin(self, sid: str) -> bool:
        """切换会话置顶状态，返回操作后的置顶状态。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT is_pinned FROM sessions WHERE id = ?", (sid,)
            )
            row = cur.fetchone()
            if row is None:
                return False
            new_state = 0 if row["is_pinned"] else 1
            conn.execute(
                "UPDATE sessions SET is_pinned = ? WHERE id = ?", (new_state, sid)
            )
            conn.commit()
            return bool(new_state)

    def groups(self) -> list[tuple[str, str, list[dict[str, Any]]]]:
        """按时间分组返回会话，用于左栏渲染。

        返回 [(group_id, display, items), ...]，顺序为 今天/昨天/最近7天/更早。
        """
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=6)

        buckets = {
            "today": [],
            "yesterday": [],
            "last7": [],
            "earlier": [],
        }
        for s in self.list():
            dt = datetime.fromtimestamp(s["updated_at"]).date()
            if dt == today:
                buckets["today"].append(s)
            elif dt == yesterday:
                buckets["yesterday"].append(s)
            elif dt >= week_start:
                buckets["last7"].append(s)
            else:
                buckets["earlier"].append(s)

        result: list[tuple[str, str, list[dict[str, Any]]]] = []
        for gid, title in (
            ("today", "今天"),
            ("yesterday", "昨天"),
            ("last7", "最近 7 天"),
            ("earlier", "更早"),
        ):
            if buckets[gid]:
                result.append((gid, title, buckets[gid]))
        return result
