"""agent_workbench/runtime/modules/skill_module.py — Skill 模块。

职责：
- Skill 注册表。
- Skill 配置热更新。
- 为 CapabilityRegistry / ToolRegistry 提供 Skill 元数据。
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


class SkillModule(BaseRuntimeModule):
    """Skill 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._skills: Dict[str, Dict[str, Any]] = {}

    @property
    def namespace(self) -> str:
        return "skill"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Skill 配置：加载 skill registry。"""
        skills = store.get("skill.registry", [])
        self._skills = {s["name"]: s for s in skills if "name" in s}

    def list_skills(self) -> List[Dict[str, Any]]:
        """返回所有 skill 配置。"""
        return list(self._skills.values())

    def get_skill(self, name: str) -> Dict[str, Any] | None:
        """按名称获取 skill 配置。"""
        return self._skills.get(name)

    def metadata(self) -> MetadataDefinition:
        """返回 Skill Capability Metadata。"""
        enabled_count = sum(1 for s in self._skills.values() if s.get("enabled", True))
        return MetadataDefinition(
            id="skill",
            type="skill",
            name="Skill",
            description="管理 Skill 注册表。",
            icon="puzzle-piece",
            properties=[
                MetadataProperty(
                    id="registry",
                    name="Registry",
                    description="已注册的 Skill 列表。",
                    value_type=ValueType.LIST,
                    current_value=self.list_skills(),
                ),
            ],
            statistics=[
                MetadataStatistics(id="total", name="Total Skills", value=len(self._skills), unit="count"),
                MetadataStatistics(id="enabled", name="Enabled", value=enabled_count, unit="count"),
            ],
            actions=[
                MetadataAction(id="reload", label="Reload Skills", icon="refresh"),
            ],
        )
