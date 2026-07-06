"""v6/services/chat_service.py — 聊天消息历史服务。

职责：
- 在 SQLite 中读写消息历史
- 追加消息时同步更新对应会话的 preview 与 updated_at

默认复用 sessions.db，与 SessionManager 共享同一数据库文件。
"""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from v6._paths import data_dir as _default_data_dir
from v6.session_manager import SessionManager


class ChatService:
    """消息历史服务。"""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        if session_manager is not None:
            self._db = session_manager.db_path
        else:
            d = Path(data_dir) if data_dir else _default_data_dir()
            d.mkdir(parents=True, exist_ok=True)
            self._db = d / "sessions.db"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sid TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_sid ON messages(sid)"
            )
            conn.commit()

    def append_message(self, sid: str, role: str, content: str) -> None:
        """追加一条消息，并同步刷新会话 preview。"""
        now = time.time()
        preview = content.strip().replace("\n", " ")[:60]
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute(
                "INSERT INTO messages (sid, role, content, created_at) VALUES (?, ?, ?, ?)",
                (sid, role, content, now),
            )
            conn.execute(
                "UPDATE sessions SET preview = ?, updated_at = ? WHERE id = ?",
                (preview, now, sid),
            )
            conn.commit()

    def load_history(self, sid: str) -> list[dict[str, Any]]:
        """加载指定会话的完整消息历史。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE sid = ? ORDER BY created_at ASC",
                (sid,),
            )
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "created_at": row["created_at"],
                }
                for row in cur.fetchall()
            ]

    def delete_history(self, sid: str) -> None:
        """删除指定会话的全部消息（业务扩展接口）。"""
        with sqlite3.connect(str(self._db)) as conn:
            conn.execute("DELETE FROM messages WHERE sid = ?", (sid,))
            conn.commit()
