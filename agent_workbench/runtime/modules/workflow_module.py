"""agent_workbench/runtime/modules/workflow_module.py — Workflow 模块。

职责：
- Workflow 模板管理。
- 简单步骤列表形式的 Workflow 热更新。
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


class WorkflowModule(BaseRuntimeModule):
    """Workflow 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._templates: Dict[str, Dict[str, Any]] = {}

    @property
    def namespace(self) -> str:
        return "workflow"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Workflow 配置：加载模板列表。"""
        templates = store.get("workflow.templates", [])
        self._templates = {t["name"]: t for t in templates if "name" in t}

    def list_templates(self) -> List[Dict[str, Any]]:
        """返回所有 workflow 模板。"""
        return list(self._templates.values())

    def get_template(self, name: str) -> Dict[str, Any] | None:
        """按名称获取 workflow 模板。"""
        return self._templates.get(name)

    def metadata(self) -> MetadataDefinition:
        """返回 Workflow Capability Metadata。"""
        enabled_count = sum(1 for t in self._templates.values() if t.get("enabled", True))
        return MetadataDefinition(
            id="workflow",
            type="workflow",
            name="Workflow",
            description="管理 Workflow 模板。",
            icon="arrows-right-left",
            properties=[
                MetadataProperty(
                    id="templates",
                    name="Templates",
                    description="已注册的 Workflow 模板列表。",
                    value_type=ValueType.LIST,
                    current_value=self.list_templates(),
                ),
            ],
            statistics=[
                MetadataStatistics(id="total", name="Total Workflows", value=len(self._templates), unit="count"),
                MetadataStatistics(id="enabled", name="Enabled", value=enabled_count, unit="count"),
            ],
            actions=[
                MetadataAction(id="reload", label="Reload Workflows", icon="refresh"),
            ],
        )
