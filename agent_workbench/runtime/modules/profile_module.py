"""agent_workbench/runtime/modules/profile_module.py — Profile 模块。

职责：
- Profile 切换、导入、导出、合并的 UI 入口。
- 委托 ProfileManager 执行实际操作。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class ProfileModule(BaseRuntimeModule):
    """Profile 配置模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None

    @property
    def namespace(self) -> str:
        return "profile"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """Profile 配置变更时，通知 UI 刷新 profile 列表。"""
        pass

    def metadata(self) -> ModuleMetadata:
        """返回 Profile Capability Metadata。"""
        profiles: list[dict] = []
        current = "default"
        if self._runtime is not None:
            profiles = self._runtime.profile_manager.list_profiles()
            current = self._runtime.profile_manager.current
        names = [p.get("name", "") for p in profiles]
        return ModuleMetadata(
            id="profile",
            type="profile",
            name="Profile",
            description="管理完整配置集合：切换、导入、导出、合并。",
            icon="user-circle",
            properties=[
                PropertyMetadata(
                    name="current",
                    label="Current Profile",
                    type="select",
                    value=current,
                    options=names,
                ),
            ],
            statistics=[
                StatisticMetadata(name="count", label="Profiles", value=len(names)),
            ],
            actions=[
                ActionMetadata(name="import", label="Import", icon="download"),
                ActionMetadata(name="export", label="Export", icon="upload"),
                ActionMetadata(name="merge", label="Merge", icon="merge"),
            ],
        )
