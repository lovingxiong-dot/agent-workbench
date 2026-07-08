"""agent_workbench/ui/workspace_registry.py — Workspace 注册表。"""
from __future__ import annotations

from agent_workbench.ui.workspace import Workspace


class WorkspaceRegistry:
    """Workspace 类型注册表。"""

    def __init__(self) -> None:
        self._workspaces: dict[str, type[Workspace]] = {}

    def register(self, workspace_class: type[Workspace]) -> None:
        """注册一个 Workspace 类。"""
        if not issubclass(workspace_class, Workspace):
            raise TypeError(f"Workspace class required, got {workspace_class!r}")
        wid = workspace_class.workspace_id
        if not wid:
            raise ValueError(f"Workspace {workspace_class.__name__} must define workspace_id")
        if wid in self._workspaces:
            raise ValueError(f"Workspace {wid!r} already registered")
        self._workspaces[wid] = workspace_class

    def unregister(self, workspace_id: str) -> type[Workspace] | None:
        """注销指定 Workspace。"""
        return self._workspaces.pop(workspace_id, None)

    def get(self, workspace_id: str) -> type[Workspace] | None:
        """根据 id 获取 Workspace 类。"""
        return self._workspaces.get(workspace_id)

    def list(self) -> list[type[Workspace]]:
        """返回所有已注册 Workspace 类，按 title 排序。"""
        return sorted(self._workspaces.values(), key=lambda cls: cls.title or cls.workspace_id)

    def __contains__(self, workspace_id: str) -> bool:
        return workspace_id in self._workspaces

    def __len__(self) -> int:
        return len(self._workspaces)
