import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "storage/conversations.db"


class SessionService:
    """对话持久化服务"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            mode TEXT,
            model TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT CHECK(role IN ('user','ai','system','tool')),
            content TEXT,
            tool_calls TEXT,
            token_count INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )''')
        # Token usage tracking table
        conn.execute('''CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            timestamp TEXT
        )''')
        conn.commit()
        conn.close()

    def list_conversations(self) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id, title, mode, model, created_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "mode": r[2], "model": r[3], "created_at": r[4]} for r in rows]

    def create_conversation(self, conv_id, title, mode="ask", model="tool-agent"):
        conn = sqlite3.connect(self.db_path)
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO conversations VALUES (?,?,?,?,?,?)",
            (conv_id, title, mode, model, now, now),
        )
        conn.commit()
        conn.close()

    def get_messages(self, conversation_id) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT role, content, tool_calls FROM messages WHERE conversation_id=? ORDER BY id",
            (conversation_id,),
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1], "tool_calls": r[2]} for r in rows]

    def add_message(self, conversation_id, role, content, tool_calls=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, tool_calls, created_at) VALUES (?,?,?,?,?)",
            (
                conversation_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                datetime.now().isoformat(),
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at=? WHERE id=?",
            (datetime.now().isoformat(), conversation_id),
        )
        conn.commit()
        conn.close()

    def delete_conversation(self, conversation_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
        conn.commit()
        conn.close()

    def log_token_usage(self, provider, model, input_tokens, output_tokens):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO token_usage (provider, model, input_tokens, output_tokens, timestamp) VALUES (?,?,?,?,?)",
            (provider, model, input_tokens, output_tokens, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_token_stats(self, days=7) -> dict:
        conn = sqlite3.connect(self.db_path)
        stats = conn.execute(
            f"""
            SELECT provider, model, SUM(input_tokens), SUM(output_tokens), COUNT(*)
            FROM token_usage WHERE timestamp > datetime('now', '-{days} days')
            GROUP BY provider, model
        """
        ).fetchall()
        conn.close()
        return [
            {
                "provider": r[0],
                "model": r[1],
                "input_tokens": r[2] or 0,
                "output_tokens": r[3] or 0,
                "calls": r[4],
            }
            for r in stats
        ]
