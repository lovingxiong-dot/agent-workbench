"""agent_workbench/runtime/modules/session_module.py — Session 模块。

职责：
- 当前 Conversation 状态。
- Session 级别消息历史（多轮上下文）。
- Context Window 管理。
- 消息存储与查询。
"""
from __future__ import annotations

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


class SessionModule(BaseRuntimeModule):
    """Session 运行态模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentWorkbenchRuntime | None" = None
        self._messages: Dict[str, List[ChatMessage]] = {}

    @property
    def namespace(self) -> str:
        return "session"

    def initialize(self, runtime: "AgentWorkbenchRuntime") -> None:
        self._runtime = runtime

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
        for m in messages:
            if (m.role, m.content) not in existing_contents:
                existing.append(m)

    def clear(self, session_id: str) -> bool:
        """清除指定 Session 的消息历史。

        Returns:
            True 如果存在并已清除，False 如果 Session 不存在。
        """
        if session_id in self._messages:
            del self._messages[session_id]
            return True
        return False

    def persist(self) -> None:
        """持久化 Session 消息到磁盘（未来实现）。"""
        pass

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
