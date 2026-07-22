"""Presentation Adapters.

Each adapter converts Runtime domain objects to ViewModels that UI Shell consumes.
"""
from agent_workbench.presentation.adapters.agent_adapter import AgentAdapter
from agent_workbench.presentation.adapters.capability_adapter import CapabilityAdapter
from agent_workbench.presentation.adapters.conversation_adapter import ConversationAdapter
from agent_workbench.presentation.adapters.memory_adapter import MemoryAdapter
from agent_workbench.presentation.adapters.settings_adapter import SettingsAdapter

__all__ = [
    "AgentAdapter",
    "ConversationAdapter",
    "CapabilityAdapter",
    "MemoryAdapter",
    "SettingsAdapter",
]
