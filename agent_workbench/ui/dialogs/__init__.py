"""agent_workbench/ui/dialogs/ — 可复用的配置/新增对话框。"""
from __future__ import annotations

from agent_workbench.ui.dialogs.add_mcp_dialog import AddMcpDialog
from agent_workbench.ui.dialogs.add_memory_dialog import AddMemoryDialog
from agent_workbench.ui.dialogs.add_prompt_dialog import AddPromptDialog
from agent_workbench.ui.dialogs.add_provider_dialog import AddProviderDialog
from agent_workbench.ui.dialogs.add_skill_dialog import AddSkillDialog
from agent_workbench.ui.dialogs.add_workflow_dialog import AddWorkflowDialog

__all__ = [
    "AddProviderDialog",
    "AddMcpDialog",
    "AddSkillDialog",
    "AddWorkflowDialog",
    "AddPromptDialog",
    "AddMemoryDialog",
]
