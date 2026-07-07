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

    def to_form(self) -> Dict[str, Any]:
        """返回 Session 配置表单。"""
        return {
            "title": "Session",
            "description": "当前会话与上下文窗口参数。",
            "fields": [
                {
                    "name": "max_history",
                    "type": "integer",
                    "label": "Max History Messages",
                    "min": 1,
                    "max": 1000,
                    "value": self._runtime.config.get("session.max_history", 20) if self._runtime else 20,
                },
                {
                    "name": "context_window",
                    "type": "integer",
                    "label": "Context Window (tokens)",
                    "min": 512,
                    "max": 128000,
                    "value": self._runtime.config.get("session.context_window", 4096) if self._runtime else 4096,
                },
            ],
        }
