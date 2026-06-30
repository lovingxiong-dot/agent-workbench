"""
repository.py — v4 会话持久化仓库

设计原则：
- 所有消息的唯一权威来源
- SessionRuntime 的内存缓存只是性能优化，不替代 DB
- 所有 CRUD 操作都是同步的（SQLite 在本地，无网络延迟）
- 支持按时间排序、置顶、重名
"""
import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager

from .models import SessionMetadata, Message, Environment, TaskPhase, TaskState, SessionType


def _get_app_root() -> str:
    """返回应用根目录：打包时为 exe 同级目录，源码时为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_default_db_path() -> str:
    return os.path.join(_get_app_root(), "storage", "conversations_v4.db")


DB_PATH = _get_default_db_path()


class SessionRepository:
    """会话持久化仓库（消息权威）
    
    职责：
    - 会话 CRUD（创建、查询、更新、删除）
    - 消息 CRUD（所有消息必须写 DB）
    - 环境持久化（Work 模式的 project_root、tools 等）
    - 任务状态持久化（Phase 快照）
    - 列表排序（按时间 + 置顶）
    """

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    session_type TEXT CHECK(session_type IN ('chat', 'work')),
                    mode TEXT DEFAULT 'ask',
                    model TEXT DEFAULT 'tool-agent',
                    project_path TEXT DEFAULT '',
                    pinned INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT CHECK(role IN ('user','ai','system','tool')),
                    content TEXT,
                    tool_calls TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS environments (
                    session_id TEXT PRIMARY KEY,
                    project_root TEXT DEFAULT '',
                    tools TEXT,  -- JSON list
                    interpreter TEXT DEFAULT '',
                    workspace_context TEXT DEFAULT '',
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_states (
                    session_id TEXT PRIMARY KEY,
                    phase TEXT DEFAULT 'idle',
                    task_count INTEGER DEFAULT 0,
                    current_task INTEGER DEFAULT 0,
                    updated_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.commit()

    # ═══════════════════════════════════════════════════
    # 会话 CRUD
    # ═══════════════════════════════════════════════════
    def create_session(self, metadata: SessionMetadata) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    """INSERT INTO sessions 
                       (session_id, title, session_type, mode, model, project_path, pinned, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (metadata.session_id, metadata.title, metadata.session_type.value,
                     metadata.mode, metadata.model, metadata.project_path,
                     1 if metadata.pinned else 0,
                     metadata.created_at.isoformat(), metadata.updated_at.isoformat())
                )
                # 初始化环境（Work 模式才有内容）
                if metadata.session_type == SessionType.WORK and metadata.project_path:
                    conn.execute(
                        "INSERT INTO environments (session_id, project_root) VALUES (?, ?)",
                        (metadata.session_id, metadata.project_path)
                    )
                # 初始化任务状态
                conn.execute(
                    "INSERT INTO task_states (session_id, phase, updated_at) VALUES (?, ?, ?)",
                    (metadata.session_id, TaskPhase.IDLE.value, datetime.now().isoformat())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_metadata(row)

    def list_sessions(self, project_path: Optional[str] = None) -> List[SessionMetadata]:
        """列出会话，按置顶 + 更新时间排序
        
        排序规则：
        1. pinned=1 的在前
        2. 同 pinned 的按 updated_at DESC
        """
        with self._connect() as conn:
            if project_path is not None:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE project_path = ? ORDER BY pinned DESC, updated_at DESC",
                    (project_path,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions ORDER BY pinned DESC, updated_at DESC"
                ).fetchall()
            return [self._row_to_metadata(r) for r in rows]

    def update_session(self, session_id: str, update_timestamp: bool = True, **kwargs) -> bool:
        """更新会话字段（title、mode、model、project_path、pinned）"""
        allowed = {"title", "mode", "model", "project_path", "pinned"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        if update_timestamp:
            fields["updated_at"] = datetime.now().isoformat()

        with self._connect() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
            values = list(fields.values()) + [session_id]
            conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE session_id = ?",
                values
            )
            conn.commit()
            return True

    def delete_session(self, session_id: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM environments WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM task_states WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return True

    # ═══════════════════════════════════════════════════
    # 消息 CRUD（唯一权威）
    # ═══════════════════════════════════════════════════
    def add_message(self, message: Message) -> bool:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO messages 
                   (message_id, session_id, role, content, tool_calls, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (message.message_id, message.session_id, message.role,
                 message.content, message.tool_calls, message.created_at.isoformat())
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (datetime.now().isoformat(), message.session_id)
            )
            conn.commit()
            return True

    def get_messages(self, session_id: str) -> List[Message]:
        """获取会话的所有消息，按时间排序"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            ).fetchall()
            return [self._row_to_message(r) for r in rows]

    def get_last_message(self, session_id: str, role: Optional[str] = None) -> Optional[Message]:
        """获取最后一条消息（可选按角色过滤）"""
        with self._connect() as conn:
            if role:
                row = conn.execute(
                    "SELECT * FROM messages WHERE session_id = ? AND role = ? ORDER BY created_at DESC LIMIT 1",
                    (session_id, role)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                    (session_id,)
                ).fetchone()
            return self._row_to_message(row) if row else None

    # ═══════════════════════════════════════════════════
    # 环境 CRUD
    # ═══════════════════════════════════════════════════
    def get_environment(self, session_id: str) -> Environment:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM environments WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                return Environment(project_root="")
            tools = []
            if row["tools"]:
                try:
                    tools = json.loads(row["tools"])
                except json.JSONDecodeError:
                    pass
            return Environment(
                project_root=row["project_root"] or "",
                tools=tools,
                interpreter=row["interpreter"] or "",
                workspace_context=row["workspace_context"] or "",
            )

    def update_environment(self, session_id: str, env: Environment) -> bool:
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO environments 
                   (session_id, project_root, tools, interpreter, workspace_context)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, env.project_root, json.dumps(env.tools),
                 env.interpreter, env.workspace_context)
            )
            conn.commit()
            return True

    # ═══════════════════════════════════════════════════
    # 任务状态 CRUD
    # ═══════════════════════════════════════════════════
    def get_task_state(self, session_id: str) -> TaskState:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_states WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                return TaskState(session_id, TaskPhase.IDLE)
            return TaskState(
                session_id=session_id,
                phase=TaskPhase(row["phase"]),
                task_count=row["task_count"] or 0,
                current_task=row["current_task"] or 0,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            )

    def update_task_state(self, state: TaskState) -> bool:
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO task_states
                   (session_id, phase, task_count, current_task, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (state.session_id, state.phase.value, state.task_count,
                 state.current_task, datetime.now().isoformat())
            )
            conn.commit()
            return True

    # ═══════════════════════════════════════════════════
    # 内部转换
    # ═══════════════════════════════════════════════════
    def _row_to_metadata(self, row) -> SessionMetadata:
        return SessionMetadata(
            session_id=row["session_id"],
            title=row["title"],
            session_type=SessionType(row["session_type"]),
            mode=row["mode"],
            model=row["model"],
            project_path=row["project_path"] or "",
            pinned=bool(row["pinned"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
        )

    def _row_to_message(self, row) -> Message:
        return Message(
            message_id=row["message_id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"] or "",
            tool_calls=row["tool_calls"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
        )
