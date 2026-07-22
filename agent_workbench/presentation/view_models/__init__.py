"""UI ViewModel Contract.

These ViewModels define the data contract between UI Shell and Presentation Layer.
UI Shell ONLY consumes these models - it never imports Runtime objects directly.

Design constraints:
- Pure dataclasses, no Runtime imports, no UI imports, no I/O.
- All fields have default values for backward compatibility.
- Naming reflects AI OS Shell concepts, not IDE concepts.
"""
from agent_workbench.presentation.view_models.agent import (
    AgentRuntimeViewModel,
    AgentViewModel,
)
from agent_workbench.presentation.view_models.capability import (
    CapabilityViewModel,
    ToolViewModel,
)
from agent_workbench.presentation.view_models.conversation import ConversationViewModel
from agent_workbench.presentation.view_models.memory import MemoryViewModel
from agent_workbench.presentation.view_models.settings import SettingsViewModel

__all__ = [
    "AgentViewModel",
    "AgentRuntimeViewModel",
    "ConversationViewModel",
    "CapabilityViewModel",
    "ToolViewModel",
    "SettingsViewModel",
    "MemoryViewModel",
]
