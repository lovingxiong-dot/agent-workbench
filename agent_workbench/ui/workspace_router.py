"""agent_workbench/ui/workspace_router.py — Workspace 路由与生命周期管理。"""
from __future__ import annotations

from agent_workbench.ui.workspace import Workspace
from agent_workbench.ui.workspace_registry import WorkspaceRegistry


class WorkspaceRouter:
    """Workspace 路由器。"""

    def __init__(self, registry: WorkspaceRegistry, host) -> None:
        from agent_workbench.ui.workbench.workspace_host import WorkspaceHost

        self._registry = registry
        self._host: WorkspaceHost = host
        self._current_id: str | None = None
        self._current_workspace: Workspace | None = None
        self._instances: dict[str, Workspace] = {}

    @property
    def current_id(self) -> str | None:
        return self._current_id

    @property
    def current_workspace(self) -> Workspace | None:
        return self._current_workspace

    def switch_to(self, workspace_id: str) -> Workspace | None:
        """切换到指定 Workspace。"""
        if workspace_id == self._current_id:
            return self._current_workspace

        workspace_class = self._registry.get(workspace_id)
        if workspace_class is None:
            return None

        if self._current_workspace is not None:
            self._current_workspace.on_deactivate()

        workspace = self._instances.get(workspace_id)
        if workspace is None:
            workspace = workspace_class()
            self._instances[workspace_id] = workspace
            self._host.register_workspace(workspace_id, workspace)

        self._current_id = workspace_id
        self._current_workspace = workspace
        workspace.on_activate()
        self._host.switch_to(workspace_id)
        return workspace

    def close_all(self) -> None:
        """关闭所有 Workspace 实例。"""
        if self._current_workspace is not None:
            self._current_workspace.on_deactivate()
            self._current_workspace = None
            self._current_id = None
        for workspace in self._instances.values():
            workspace.on_close()
        self._instances.clear()
