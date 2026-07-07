"""agent_workbench/runtime/modules/trace_module.py — Trace 模块。

职责：
- Trace 开关。
- 日志等级。
- Runtime Trace 参数。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class TraceModule(BaseRuntimeModule):
    """Trace 观测模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._enabled: bool = True
        self._level: str = "INFO"
        self._persist: bool = True

    @property
    def namespace(self) -> str:
        return "trace"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Trace 配置。"""
        self._enabled = store.get("trace.enabled", True)
        self._level = store.get("trace.level", "INFO")
        self._persist = store.get("trace.persist", True)

    def to_form(self) -> Dict[str, Any]:
        """返回 Trace 配置表单。"""
        return {
            "title": "Trace",
            "description": "管理 Runtime Trace 与日志等级。",
            "fields": [
                {
                    "name": "enabled",
                    "type": "boolean",
                    "label": "Trace Enabled",
                    "value": self._enabled,
                },
                {
                    "name": "level",
                    "type": "select",
                    "label": "Log Level",
                    "options": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "value": self._level,
                },
                {
                    "name": "persist",
                    "type": "boolean",
                    "label": "Persist Trace",
                    "value": self._persist,
                },
            ],
        }
