"""agent_workbench/runtime/modules/session_module.py — Session 模块。

职责：
- 当前 Conversation 状态。
- History 浏览。
- Context Window 管理。
- Current Task / Statistics。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class SessionModule(BaseRuntimeModule):
    """Session 运行态模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None

    @property
    def namespace(self) -> str:
        return "session"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """Session 参数变更：更新 max_history / context_window。"""
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

    def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """返回最近会话历史摘要。"""
        if self._runtime is None:
            return []
        # 第一版从 RuntimeTrace 或上下文收集；此处占位
        return []

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
