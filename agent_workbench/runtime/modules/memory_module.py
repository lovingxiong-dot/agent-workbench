"""agent_workbench/runtime/modules/memory_module.py — Memory 模块。

职责：
- Memory Provider 管理。
- Memory 参数配置。
- Memory 生命周期管理（初始化 / 释放）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.services.memory_service import MemoryService

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class MemoryModule(BaseRuntimeModule):
    """Memory 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._service: MemoryService | None = None
        self._enabled: bool = True
        self._config: Dict[str, Any] = {}

    @property
    def namespace(self) -> str:
        return "memory"

    @property
    def service(self) -> MemoryService | None:
        return self._service

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Memory 配置：重建 MemoryService。"""
        self._enabled = store.get("memory.enabled", True)
        self._config = store.get("memory", {})

        if not self._enabled:
            self._dispose_service()
            return

        provider = self._config.get("provider", "sqlite")
        if provider == "sqlite":
            db_path = self._config.get("sqlite", {}).get("path", "storage/agents/agent_workbench/memory.db")
            self._dispose_service()
            self._service = MemoryService(db_path)

    def save(self, content: str, namespace: str = "default", task_id: str = "", metadata: Dict[str, Any] | None = None) -> None:
        """保存记忆。"""
        if self._service is None or not self._enabled:
            return
        from agent_workbench.services.memory_service import MemoryRecord
        self._service.save(MemoryRecord(content, namespace=namespace, task_id=task_id, metadata=metadata))

    def query(self, namespace: str | None = None, limit: int = 100):
        """查询记忆。"""
        if self._service is None:
            return []
        return self._service.query(namespace=namespace, limit=limit)

    def dispose(self) -> None:
        self._dispose_service()

    def _dispose_service(self) -> None:
        if self._service is not None:
            self._service.close()
            self._service = None

    def to_form(self) -> Dict[str, Any]:
        """返回 Memory 配置表单。"""
        return {
            "title": "Memory",
            "description": "管理 SQLite Memory Provider 与命名空间。",
            "fields": [
                {
                    "name": "enabled",
                    "type": "boolean",
                    "label": "Memory Enabled",
                    "value": self._enabled,
                },
                {
                    "name": "provider",
                    "type": "select",
                    "label": "Provider",
                    "options": ["sqlite"],
                    "value": self._config.get("provider", "sqlite"),
                },
                {
                    "name": "db_path",
                    "type": "text",
                    "label": "SQLite Path",
                    "value": self._config.get("sqlite", {}).get("path", ""),
                },
                {
                    "name": "max_records",
                    "type": "integer",
                    "label": "Max Records",
                    "min": 1,
                    "max": 1000000,
                    "value": self._config.get("max_records", 10000),
                },
            ],
        }
