"""presentation/services/tool_module_backend.py — ToolModule → RuntimeToolBackend Adapter。

v6.10.0-alpha Tool Runtime Product Layer。

职责：
  - 适配 Runtime ToolModule（frozen）为 RuntimeToolBackend Protocol
  - 让 WorkbenchToolServiceController 不直接依赖 ToolModule
"""
from __future__ import annotations

from typing import Any, Dict, List

from agent_workbench.presentation.services.tool_service import RuntimeToolBackend


class ToolModuleBackend:
    """ToolModule → RuntimeToolBackend Adapter。"""

    def __init__(self, tool_module) -> None:
        self._module = tool_module

    def list_tool_dicts(self) -> List[Dict[str, Any]]:
        """列出所有 Tool dict。"""
        return self._module.list_tools()

    def set_tool_enabled(self, tool_id: str, enabled: bool) -> bool:
        """设置 Tool 开关（通过 ToolRegistry.set_enabled）。"""
        registry = self._module.registry
        if registry is None:
            return False
        return registry.set_enabled(tool_id, enabled)

    def set_tool_config(self, tool_id: str, config: Dict[str, Any]) -> bool:
        """更新 Tool 配置（permission / schema）。

        限制：当前只支持 permission 更新（ToolRegistry 公开 API）。
        Schema 更新通过 apply_config 触发（需要 ConfigStore 协调）。
        """
        registry = self._module.registry
        if registry is None:
            return False
        tool = registry.get(tool_id)
        if tool is None:
            return False
        # 仅更新公开字段
        if "permission" in config:
            tool.permission = str(config["permission"])
        if "enabled" in config:
            tool.enabled = bool(config["enabled"])
        if "description" in config:
            tool.description = str(config["description"])
        return True