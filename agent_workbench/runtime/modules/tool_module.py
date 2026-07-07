"""agent_workbench/runtime/modules/tool_module.py — Tool 模块。

职责：
- Tool 注册、开关、权限管理。
- 委托 ToolRegistry 执行实际操作。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.services.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class ToolModule(BaseRuntimeModule):
    """Tool 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._registry = ToolRegistry()

    @property
    def namespace(self) -> str:
        return "tool"

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Tool 配置：开关、权限。"""
        enabled = store.get("tool.enabled", True)
        registry_config = store.get("tool.registry", [])
        self._registry.apply_config(registry_config)
        # 未在 registry_config 中显式列出的 tool 默认保持原状态，但受总开关影响可后续扩展

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回所有 tool 状态。"""
        return [tool.to_dict() for tool in self._registry.list_tools()]

    def metadata(self) -> ModuleMetadata:
        """返回 Tool Capability Metadata。"""
        tools = self.list_tools()
        enabled_count = sum(1 for t in tools if t.get("enabled", False))
        return ModuleMetadata(
            id="tool",
            type="tool",
            name="Tool",
            description="管理工具注册、开关与权限。",
            icon="wrench",
            properties=[
                PropertyMetadata(
                    name="enabled",
                    label="Tools Enabled",
                    type="boolean",
                    value=True,
                ),
            ],
            statistics=[
                StatisticMetadata(name="total", label="Total Tools", value=len(tools)),
                StatisticMetadata(name="enabled", label="Enabled", value=enabled_count),
                StatisticMetadata(
                    name="registry",
                    label="Registry",
                    value=tools,
                    format="json",
                ),
            ],
            actions=[
                ActionMetadata(name="reload", label="Reload Registry", icon="refresh"),
            ],
        )
