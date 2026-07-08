"""agent_workbench/ui/workspaces/ — Workbench Workspace 实现集合。"""
from __future__ import annotations

from agent_workbench.ui.workspaces.chat_workspace import ChatWorkspace
from agent_workbench.ui.workspaces.provider_workspace import ProviderWorkspace
from agent_workbench.ui.workspaces.skill_workspace import SkillWorkspace
from agent_workbench.ui.workspaces.tool_workspace import ToolWorkspace

__all__ = [
    "ChatWorkspace",
    "SkillWorkspace",
    "ToolWorkspace",
    "ProviderWorkspace",
]
