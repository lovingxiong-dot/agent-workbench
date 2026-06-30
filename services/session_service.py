import sqlite3
import json
import os
import sys
from datetime import datetime


def _get_app_root() -> str:
    """返回应用根目录：打包时为 exe 同级目录，源码时为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DB_PATH = os.path.join(_get_app_root(), "storage", "conversations.db")


class SessionService:
    """对话持久化服务（支持 project_path 维度）"""

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
            updated_at TEXT,
            project_path TEXT DEFAULT ''
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
        # 迁移旧数据库，添加 project_path 列
        self._ensure_project_path_column()

    def _ensure_project_path_column(self):
        """Schema 迁移：为旧表增加 project_path 列"""
        conn = sqlite3.connect(self.db_path)
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(conversations)").fetchall()]
            if "project_path" not in cols:
                conn.execute("ALTER TABLE conversations ADD COLUMN project_path TEXT DEFAULT ''")
                conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def list_conversations(self, project_path=None) -> list:
        """列出会话；传入 project_path 则按目录过滤"""
        conn = sqlite3.connect(self.db_path)
        if project_path is not None:
            rows = conn.execute(
                "SELECT id, title, mode, model, created_at, project_path FROM conversations "
                "WHERE project_path=? ORDER BY updated_at DESC",
                (project_path,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, mode, model, created_at, project_path FROM conversations "
                "ORDER BY updated_at DESC"
            ).fetchall()
        conn.close()
        return [
            {"id": r[0], "title": r[1], "mode": r[2], "model": r[3], "created_at": r[4], "project_path": r[5] or ""}
            for r in rows
        ]

    def list_projects(self) -> list:
        """列出所有有会话记录的目录"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT project_path, MAX(updated_at) AS last_at FROM conversations "
            "WHERE project_path != '' GROUP BY project_path ORDER BY last_at DESC"
        ).fetchall()
        conn.close()
        return [{"path": r[0], "updated_at": r[1]} for r in rows]

    def create_conversation(self, conv_id, title, mode="ask", model="tool-agent", project_path=""):
        conn = sqlite3.connect(self.db_path)
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO conversations VALUES (?,?,?,?,?,?,?)",
            (conv_id, title, mode, model, now, now, project_path or ""),
        )
        conn.commit()
        conn.close()

    def get_conversation_project_path(self, conversation_id) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT project_path FROM conversations WHERE id=?", (conversation_id,)
        ).fetchone()
        conn.close()
        return row[0] if row else ""

    def get_conversation_mode_model(self, conversation_id) -> tuple:
        """返回会话保存的 (mode, model)，若不存在则返回 ('', '')"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT mode, model FROM conversations WHERE id=?", (conversation_id,)
        ).fetchone()
        conn.close()
        return (row[0], row[1]) if row else ("", "")

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
        # 去重：同会话 + 同角色 + 同内容 已存在则跳过，防止防御性 flush 制造重复
        existing = conn.execute(
            "SELECT 1 FROM messages WHERE conversation_id=? AND role=? AND content=? LIMIT 1",
            (conversation_id, role, content),
        ).fetchone()
        if existing:
            conn.close()
            return
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
