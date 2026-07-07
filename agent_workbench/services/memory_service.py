"""agent_workbench/services/memory_service.py — SQLite Memory 服务。

第一版只提供基础 CRUD + namespace，不引入 embedding / 向量搜索 / RAG。
未来可替换 backend，但 MemoryModule 通过此服务交互。
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryRecord:
    """Memory 记录。"""

    def __init__(
        self,
        content: str,
        namespace: str = "default",
        task_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
        created_at: Optional[float] = None,
    ) -> None:
        self.id = record_id or uuid.uuid4().hex
        self.task_id = task_id
        self.namespace = namespace
        self.content = content
        self.metadata = metadata or {}
        self.created_at = created_at or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "namespace": self.namespace,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class MemoryService:
    """SQLite 后端 Memory 服务。"""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._closed = False
        self._ensure_table()

    def close(self) -> None:
        """释放资源占位；SQLite 使用短连接，无需额外关闭。"""
        self._closed = True

    def save(self, record: MemoryRecord) -> MemoryRecord:
        """保存或更新记录。"""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                INSERT INTO memories (id, task_id, namespace, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    task_id=excluded.task_id,
                    namespace=excluded.namespace,
                    content=excluded.content,
                    metadata=excluded.metadata,
                    created_at=excluded.created_at
                """,
                (
                    record.id,
                    record.task_id,
                    record.namespace,
                    record.content,
                    json.dumps(record.metadata, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()
        return record

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        """按 id 读取记录。"""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute(
                "SELECT id, task_id, namespace, content, metadata, created_at FROM memories WHERE id=?",
                (record_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def query(
        self,
        namespace: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MemoryRecord]:
        """按 namespace / task_id 查询记录，按时间倒序。"""
        conditions: List[str] = []
        params: List[Any] = []
        if namespace is not None:
            conditions.append("namespace=?")
            params.append(namespace)
        if task_id is not None:
            conditions.append("task_id=?")
            params.append(task_id)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT id, task_id, namespace, content, metadata, created_at FROM memories {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def delete(self, record_id: str) -> bool:
        """删除记录；不存在返回 False。"""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id=?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_namespace(self, namespace: str) -> int:
        """清空某个 namespace；返回删除条数。"""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE namespace=?", (namespace,))
            conn.commit()
            return cursor.rowcount

    def namespaces(self) -> List[str]:
        """返回所有 namespace。"""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute("SELECT DISTINCT namespace FROM memories ORDER BY namespace").fetchall()
        return [row[0] for row in rows]

    def _ensure_table(self) -> None:
        """初始化 SQLite 表。"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    namespace TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at REAL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_namespace ON memories(namespace)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON memories(task_id)")
            conn.commit()

    @staticmethod
    def _row_to_record(row: tuple) -> MemoryRecord:
        return MemoryRecord(
            record_id=row[0],
            task_id=row[1],
            namespace=row[2],
            content=row[3],
            metadata=json.loads(row[4]) if row[4] else {},
            created_at=row[5],
        )
