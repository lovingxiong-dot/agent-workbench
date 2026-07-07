"""agent_workbench/runtime/modules/profile_module.py — Profile 模块。

职责：
- Profile 切换、导入、导出、合并的 UI 入口。
- 委托 ProfileManager 执行实际操作。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
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

    def to_form(self) -> Dict[str, Any]:
        """返回 Profile 配置表单。"""
        profiles: list[dict] = []
        current = "default"
        if self._runtime is not None:
            profiles = self._runtime.profile_manager.list_profiles()
            current = self._runtime.profile_manager.current

        return {
            "title": "Profile",
            "description": "管理完整配置集合。",
            "fields": [
                {
                    "name": "current",
                    "type": "select",
                    "label": "Current Profile",
                    "options": [p.get("name", "") for p in profiles],
                    "value": current,
                },
                {"name": "import_path", "type": "file", "label": "Import Profile"},
                {"name": "export_name", "type": "text", "label": "Export As"},
            ],
        }
