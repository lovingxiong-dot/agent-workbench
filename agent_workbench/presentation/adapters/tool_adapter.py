"""presentation/adapters/tool_adapter.py — Tool Adapter。

v6.10.0-alpha Tool Runtime Product Layer。

边界：
  - 接收 Runtime Tool dict（来自 ToolModule.list_tools()）
  - 转换为 ToolViewModel 供 UI 渲染
  - 不修改 Runtime ToolModule / ToolRegistry
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from agent_workbench.presentation.view_models.tool import (
    ToolListViewModel,
    ToolViewModel,
)


class ToolAdapter:
    """Tool dict (Runtime) → ToolViewModel (UI) Adapter。"""

    def to_view_model(self, tool_dict: Dict[str, Any]) -> ToolViewModel:
        """转换 Runtime Tool dict 为 ToolViewModel。

        Args:
            tool_dict: Runtime ToolModule.list_tools() 返回的元素。

        Returns:
            ToolViewModel 适用于 UI 渲染。
        """
        enabled = bool(tool_dict.get("enabled", True))
        return ToolViewModel(
            tool_id=tool_dict.get("name", ""),
            name=tool_dict.get("name", "Unknown"),
            description=tool_dict.get("description", ""),
            status="enabled" if enabled else "disabled",
            permission=tool_dict.get("permission", "user"),
            schema=dict(tool_dict.get("schema", {}) or {}),
            metadata={
                "enabled": str(enabled),
                "permission": tool_dict.get("permission", "user"),
            },
        )

    def to_list_view_model(self, tools: Iterable[Dict[str, Any]]) -> ToolListViewModel:
        """转换 Runtime Tool dict 列表为 ToolListViewModel。"""
        view_models = [self.to_view_model(t) for t in tools]
        return ToolListViewModel(tools=view_models)