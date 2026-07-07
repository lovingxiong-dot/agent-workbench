"""agent_workbench/services/tool_registry.py — Tool 注册表。

职责：
- 注册 / 注销 Tool。
- Tool 启用开关。
- Tool 权限级别（user / admin）。
- 查询可用 Tool。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """Tool 描述。"""

    name: str
    description: str = ""
    enabled: bool = True
    permission: str = "user"  # user / admin
    handler: Optional[Callable[..., Any]] = field(default=None, repr=False)
    schema: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "permission": self.permission,
            "schema": self.schema,
        }


class ToolRegistry:
    """Tool 注册表。"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        handler: Optional[Callable[..., Any]] = None,
        description: str = "",
        enabled: bool = True,
        permission: str = "user",
        schema: Optional[Dict[str, Any]] = None,
    ) -> Tool:
        """注册 Tool；同名覆盖。"""
        tool = Tool(
            name=name,
            description=description,
            enabled=enabled,
            permission=permission,
            handler=handler,
            schema=schema or {},
        )
        self._tools[name] = tool
        return tool

    def unregister(self, name: str) -> bool:
        """注销 Tool；不存在返回 False。"""
        if name not in self._tools:
            return False
        del self._tools[name]
        return True

    def get(self, name: str) -> Optional[Tool]:
        """按名称获取 Tool。"""
        return self._tools.get(name)

    def list_tools(self, enabled_only: bool = False, permission: Optional[str] = None) -> List[Tool]:
        """列出 Tool；可过滤启用状态和权限。"""
        result = list(self._tools.values())
        if enabled_only:
            result = [t for t in result if t.enabled]
        if permission is not None:
            result = [t for t in result if t.permission == permission]
        return result

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """设置 Tool 开关。"""
        tool = self._tools.get(name)
        if tool is None:
            return False
        tool.enabled = enabled
        return True

    def apply_config(self, registry_config: List[Dict[str, Any]]) -> None:
        """根据配置更新已注册 Tool 的开关和权限。"""
        for item in registry_config:
            name = item.get("name")
            if name is None:
                continue
            tool = self._tools.get(name)
            if tool is None:
                self.register(name, enabled=item.get("enabled", True), permission=item.get("permission", "user"))
            else:
                tool.enabled = item.get("enabled", tool.enabled)
                tool.permission = item.get("permission", tool.permission)
