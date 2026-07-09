"""agent_workbench/runtime/modules/memory_module.py — Memory 模块。

职责：
- Memory Provider 管理。
- Memory 参数配置。
- Memory 生命周期管理（初始化 / 释放）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ValueType,
)
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
        """热更新 Memory 配置：重建 MemoryService。

        优先读取 memory.configs 列表（Workbench UI 新增 Memory Store 时使用），
        若不存在则回退到传统 memory 字典配置。
        """
        self._enabled = store.get("memory.enabled", True)
        memory_configs = store.get("memory.configs", [])
        legacy_config = store.get("memory", {})

        if memory_configs:
            active_config = next(
                (cfg for cfg in memory_configs if cfg.get("enabled", True)),
                memory_configs[0],
            )
            self._config = {
                "provider": active_config.get("provider", "sqlite"),
                "sqlite": {"path": active_config.get("path", "storage/agents/agent_workbench/memory.db")},
                "max_records": active_config.get("max_records", 10000),
            }
        else:
            self._config = legacy_config

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

    def metadata(self) -> MetadataDefinition:
        """返回 Memory Capability Metadata。"""
        db_path = self._config.get("sqlite", {}).get("path", "")
        records = 0
        namespaces: list[str] = []
        if self._service is not None:
            records = self._service.count()
            namespaces = self._service.namespaces()
        return MetadataDefinition(
            id="memory",
            type="memory",
            name="Memory",
            description="管理 Memory Provider 与命名空间。",
            icon="database",
            properties=[
                MetadataProperty(
                    id="enabled",
                    name="Memory Enabled",
                    description="是否启用 Memory。",
                    value_type=ValueType.BOOL,
                    current_value=self._enabled,
                ),
                MetadataProperty(
                    id="provider",
                    name="Provider",
                    description="Memory Provider 类型。",
                    value_type=ValueType.ENUM,
                    current_value=self._config.get("provider", "sqlite"),
                    options=["sqlite"],
                ),
                MetadataProperty(
                    id="sqlite.path",
                    name="SQLite Path",
                    description="SQLite 数据库路径。",
                    value_type=ValueType.PATH,
                    current_value=db_path,
                ),
                MetadataProperty(
                    id="max_records",
                    name="Max Records",
                    description="最大记录数限制。",
                    value_type=ValueType.INT,
                    current_value=self._config.get("max_records", 10000),
                ),
            ],
            statistics=[
                MetadataStatistics(id="records", name="Records", value=records, unit="count"),
                MetadataStatistics(id="namespaces", name="Namespaces", value=namespaces, unit="list"),
                MetadataStatistics(id="status", name="Status", value="active" if self._enabled and self._service else "inactive", unit="state"),
            ],
            actions=[
                MetadataAction(id="clear", label="Clear Memory", icon="trash"),
                MetadataAction(id="reload", label="Reload", icon="refresh"),
            ],
        )
