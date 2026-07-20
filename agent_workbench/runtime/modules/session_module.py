"""agent_workbench/runtime/modules/session_module.py — Session 模块。

职责：
- 当前 Conversation 状态。
- Session 级别消息历史（多轮上下文）。
- Context Window 管理。
- 消息存储与查询（JSON 持久化）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from v6.runtime.types import ChatMessage

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime

# Session 数据目录（与 v6._paths 一致，使用 storage/ 目录）
_SESSION_DATA_DIR = Path(__file__).resolve().parents[3] / "storage" / "sessions"
_LAST_SESSION_FILE = _SESSION_DATA_DIR / "_last_session.txt"


class SessionModule(BaseRuntimeModule):
    """Session 运行态模块 — 支持 JSON 持久化。

    消息存储位置：storage/sessions/session_{id}.json
    上次会话 ID：storage/sessions/_last_session.txt
    """

    def __init__(self) -> None:
        self._runtime: "AgentWorkbenchRuntime | None" = None
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._current_session_id: str | None = None
        self._auto_save = True

    @property
    def namespace(self) -> str:
        return "session"

    @property
    def current_session_id(self) -> str | None:
        return self._current_session_id

    def initialize(self, runtime: "AgentWorkbenchRuntime") -> None:
        self._runtime = runtime
        _SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def apply_config(self, store: ConfigStore) -> None:
        """Session 参数变更：更新 max_history / context_window。"""
        pass

    def history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """返回指定 Session 的消息历史。

        Args:
            session_id: 会话标识。
            limit: 最大返回条数。

        Returns:
            消息列表，每条包含 role 和 content。
        """
        messages = self._messages.get(session_id, [])
        return [{"role": m.role, "content": m.content} for m in messages[-limit:]]

    def append(self, session_id: str, messages: List[ChatMessage]) -> None:
        """向 Session 追加消息（去重）。

        Args:
            session_id: 会话标识。
            messages: 要追加的消息列表。
        """
        existing = self._messages.setdefault(session_id, [])
        existing_contents = {(m.role, m.content) for m in existing}
        added = False
        for m in messages:
            if (m.role, m.content) not in existing_contents:
                existing.append(m)
                existing_contents.add((m.role, m.content))
                added = True
        if added and self._auto_save:
            self._persist_session(session_id)

    def clear(self, session_id: str) -> bool:
        """清除指定 Session 的消息历史（含磁盘文件）。

        Returns:
            True 如果存在并已清除，False 如果 Session 不存在。
        """
        if session_id in self._messages:
            del self._messages[session_id]
        filepath = _SESSION_DATA_DIR / f"session_{session_id}.json"
        if filepath.exists():
            filepath.unlink()
        return True

    def persist(self) -> None:
        """持久化所有 Session 消息到磁盘。"""
        for session_id in self._messages:
            self._persist_session(session_id)

    def load(self, session_id: str) -> List[Dict[str, Any]]:
        """从磁盘加载指定 Session 的消息历史。

        Args:
            session_id: 会话标识。

        Returns:
            消息列表，若文件不存在则返回空列表。
        """
        filepath = _SESSION_DATA_DIR / f"session_{session_id}.json"
        if not filepath.exists():
            return []
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            messages = [ChatMessage(role=m["role"], content=m["content"]) for m in data]
            self._messages[session_id] = messages
            self._current_session_id = session_id
            return [{"role": m.role, "content": m.content} for m in messages]
        except (json.JSONDecodeError, KeyError):
            return []

    def load_last_active(self) -> str | None:
        """加载上次活跃的 Session ID 并恢复消息。

        Returns:
            上次活跃的 session_id，若不存在则返回 None。
        """
        if not _LAST_SESSION_FILE.exists():
            return None
        session_id = _LAST_SESSION_FILE.read_text(encoding="utf-8").strip()
        if not session_id:
            return None
        msgs = self.load(session_id)
        if msgs:
            self._current_session_id = session_id
            return session_id
        return None

    def save_last_active(self) -> None:
        """保存当前 Session ID 为最后活跃会话。"""
        if self._current_session_id:
            _LAST_SESSION_FILE.write_text(self._current_session_id, encoding="utf-8")

    def start_session(self, session_id: str) -> None:
        """开始或切换到一个 Session。

        Args:
            session_id: 会话标识。
        """
        self._current_session_id = session_id
        if session_id not in self._messages:
            self._messages[session_id] = []
        self.save_last_active()

    def _persist_session(self, session_id: str) -> None:
        """持久化单个 Session 到 JSON 文件。"""
        messages = self._messages.get(session_id, [])
        filepath = _SESSION_DATA_DIR / f"session_{session_id}.json"
        data = [{"role": m.role, "content": m.content} for m in messages]
        # 原子写入：先写临时文件再重命名
        tmp = filepath.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(filepath)

    def current_state(self) -> Dict[str, Any]:
        """返回当前会话状态摘要。"""
        if self._runtime is None:
            return {}
        ctx = self._runtime.current_context()
        if ctx is None:
            return {
                "status": "idle",
                "messages_count": 0,
                "task_id": None,
            }
        return {
            "status": ctx.status.value if hasattr(ctx.status, "value") else str(ctx.status),
            "task_id": ctx.task_id,
            "session_id": ctx.session_id,
            "messages_count": len(ctx.messages),
            "context_window": self._runtime.config.get("session.context_window", 4096),
            "max_history": self._runtime.config.get("session.max_history", 20),
        }

    def metadata(self) -> ModuleMetadata:
        """返回 Session Capability Metadata。"""
        state = self.current_state()
        max_history = self._runtime.config.get("session.max_history", 20) if self._runtime else 20
        context_window = self._runtime.config.get("session.context_window", 4096) if self._runtime else 4096
        return ModuleMetadata(
            id="session",
            type="session",
            name="Session",
            description="当前会话、历史与上下文窗口。",
            icon="chat-bubble",
            properties=[
                PropertyMetadata(
                    name="max_history",
                    label="Max History Messages",
                    type="number",
                    value=max_history,
                ),
                PropertyMetadata(
                    name="context_window",
                    label="Context Window (tokens)",
                    type="number",
                    value=context_window,
                ),
            ],
            statistics=[
                StatisticMetadata(name="status", label="Status", value=state.get("status", "idle")),
                StatisticMetadata(name="task_id", label="Task ID", value=state.get("task_id") or "—"),
                StatisticMetadata(name="session_id", label="Session ID", value=state.get("session_id") or "—"),
                StatisticMetadata(name="messages_count", label="Messages", value=state.get("messages_count", 0)),
            ],
            actions=[],
        )
