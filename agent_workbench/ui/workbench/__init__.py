"""agent_workbench/ui/workbench/ — Workbench UI Runtime。

设计来源：
- 纯 UI 资产来自 experiments/ui_template.py（Git 标签 v0.6-alpha），
  经 v6/ui/base.py 提纯后复用。
- 架构遵循 PROJECT_BLUEPRINT.md 中 V6 Architecture Constitution：
  Runtime 不 import UI；UI 不 import RuntimeModule；UI 通过 Metadata 自动生成；
  Workbench 的中心是 Runtime。
"""
from __future__ import annotations

from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.metadata_adapter import MetadataAdapter
from agent_workbench.ui.workbench.navigator import Navigator
from agent_workbench.ui.workbench.workspace_host import WorkspaceHost
from agent_workbench.ui.workbench.inspector import Inspector
from agent_workbench.ui.workbench.status_bar import StatusBar
from agent_workbench.ui.workbench.command_bar import CommandBar
from agent_workbench.ui.workbench.workbench import Workbench
from agent_workbench.ui.workbench.workbench_host import WorkbenchHost
from agent_workbench.ui.workbench.title_bar import WorkbenchTitleBar
from agent_workbench.ui.workbench.chat_workspace import ChatWorkspaceItem

__all__ = [
    "ModulePresentation",
    "PropertyPresentation",
    "StatisticPresentation",
    "ActionPresentation",
    "MetadataAdapter",
    "Navigator",
    "WorkspaceHost",
    "Inspector",
    "StatusBar",
    "CommandBar",
    "Workbench",
    "WorkbenchHost",
    "WorkbenchTitleBar",
    "ChatWorkspaceItem",
]
