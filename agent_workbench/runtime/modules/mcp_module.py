"""agent_workbench/runtime/modules/mcp_module.py — MCP 模块。

职责：
- MCP Server 配置管理。
- 维护可用 MCP server 列表，供未来 ToolRuntime 动态接入。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ValueType,
)
from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class McpModule(BaseRuntimeModule):
    """MCP 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._servers: List[Dict[str, Any]] = []

    @property
    def namespace(self) -> str:
        return "mcp"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 MCP 配置：加载启用的 server 列表。"""
        self._servers = store.get("mcp.servers", [])

    def list_servers(self) -> List[Dict[str, Any]]:
        """返回当前 MCP server 配置列表。"""
        return list(self._servers)

    def metadata(self) -> MetadataDefinition:
        """返回 MCP Capability Metadata。"""
        enabled_count = sum(1 for s in self._servers if s.get("enabled", True))
        return MetadataDefinition(
            id="mcp",
            type="mcp",
            name="MCP",
            description="管理 MCP Server 配置。",
            icon="plug",
            properties=[
                MetadataProperty(
                    id="servers",
                    name="Servers",
                    description="已注册的 MCP Server 列表。",
                    value_type=ValueType.LIST,
                    current_value=self._servers,
                ),
            ],
            statistics=[
                MetadataStatistics(id="total", name="Total Servers", value=len(self._servers), unit="count"),
                MetadataStatistics(id="enabled", name="Enabled", value=enabled_count, unit="count"),
            ],
            actions=[
                MetadataAction(id="reload", label="Reload Servers", icon="refresh"),
            ],
        )
