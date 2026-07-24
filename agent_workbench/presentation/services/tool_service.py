"""presentation/services/tool_service.py — Workbench Tool Service。

v6.10.0-alpha Tool Runtime Product Layer。

边界：
  - 不修改 Runtime ToolModule / ToolRegistry（frozen）
  - 通过 RuntimeToolBackend Protocol 委托 Runtime
  - UI 配置通过 ConfigStore 实现（Configuration-Driven Principle P5）
  - Tool 必须通过 Capability Runtime Contract 路由（不变 Capability）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from agent_workbench.presentation.adapters.tool_adapter import ToolAdapter
from agent_workbench.presentation.view_models.tool import (
    ToolListViewModel,
    ToolViewModel,
)


@dataclass
class ToolInfo:
    """Tool 运行时信息（v6-agent 层 view）。"""

    tool_id: str
    description: str = ""
    enabled: bool = True
    permission: str = "user"
    schema: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema is None:
            self.schema = {}


class RuntimeToolBackend(Protocol):
    """Runtime Tool Backend Protocol（v6-agent 层定义）。

    Runtime ToolModule 自然满足此 Protocol，但 v6-agent 层不直接 import Runtime。
    """

    def list_tool_dicts(self) -> List[Dict[str, Any]]:
        """列出所有 Tool 的 Runtime dict 表示。"""
        ...

    def set_tool_enabled(self, tool_id: str, enabled: bool) -> bool:
        """设置 Tool 开关。返回是否成功。"""
        ...

    def set_tool_config(self, tool_id: str, config: Dict[str, Any]) -> bool:
        """更新 Tool 配置（权限 / schema 等）。"""
        ...


@dataclass
class ToolConfigUpdate:
    """Tool 配置更新结果。"""

    success: bool
    tool_id: str
    error: str = ""


class WorkbenchToolServiceController:
    """Workbench Tool Service Controller（v6-agent 层）。

    职责：
      - 聚合 Runtime Tool Backend
      - 提供 UI 友好操作
      - 不修改 Runtime

    Boundary:
      - 不发起 Tool 执行（Tool execution is Capability Runtime Contract's job）
      - 仅做 enable/disable + config update
    """

    def __init__(
        self,
        backend: RuntimeToolBackend,
        adapter: Optional[ToolAdapter] = None,
    ) -> None:
        self._backend = backend
        self._adapter = adapter or ToolAdapter()

    # ─── List ────────────────────────────────────────────────

    def list_view_model(self) -> ToolListViewModel:
        """获取所有 Tool 的 ViewModel。"""
        tools = self._backend.list_tool_dicts()
        return self._adapter.to_list_view_model(tools)

    def get_view_model(self, tool_id: str) -> Optional[ToolViewModel]:
        """获取单个 Tool ViewModel。"""
        for tool_dict in self._backend.list_tool_dicts():
            if tool_dict.get("name") == tool_id:
                return self._adapter.to_view_model(tool_dict)
        return None

    # ─── Enable / Disable ────────────────────────────────────

    def enable_tool(self, tool_id: str) -> ToolConfigUpdate:
        """启用 Tool。"""
        ok = self._backend.set_tool_enabled(tool_id, True)
        if not ok:
            return ToolConfigUpdate(
                success=False, tool_id=tool_id, error=f"Tool '{tool_id}' 不存在。"
            )
        return ToolConfigUpdate(success=True, tool_id=tool_id)

    def disable_tool(self, tool_id: str) -> ToolConfigUpdate:
        """禁用 Tool。"""
        ok = self._backend.set_tool_enabled(tool_id, False)
        if not ok:
            return ToolConfigUpdate(
                success=False, tool_id=tool_id, error=f"Tool '{tool_id}' 不存在。"
            )
        return ToolConfigUpdate(success=True, tool_id=tool_id)

    # ─── Config Update ───────────────────────────────────────

    def update_tool_config(self, tool_id: str, config: Dict[str, Any]) -> ToolConfigUpdate:
        """更新 Tool 配置（permission / schema）。"""
        ok = self._backend.set_tool_config(tool_id, config)
        if not ok:
            return ToolConfigUpdate(
                success=False, tool_id=tool_id, error=f"Tool '{tool_id}' 不存在。"
            )
        return ToolConfigUpdate(success=True, tool_id=tool_id)