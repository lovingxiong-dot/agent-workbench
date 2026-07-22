"""Presentation Layer - bridge between Runtime and UI Shell.

Layers:
- view_models/ - Pure data contracts that UI consumes (zero Runtime imports)
- adapters/ - Convert Runtime objects to ViewModels

Architecture:
    Runtime (AgentRegistry, SessionManager, etc.)
        |
        v
    Presentation Adapter (adapters/)
        |
        v
    ViewModel (view_models/)
        |
        v
    UI Shell (ui/)
"""
from agent_workbench.presentation.view_models import (
    AgentRuntimeViewModel,
    AgentViewModel,
    CapabilityViewModel,
    ConversationViewModel,
    MemoryViewModel,
    SettingsViewModel,
    ToolViewModel,
)

__all__ = [
    "AgentViewModel",
    "AgentRuntimeViewModel",
    "ConversationViewModel",
    "CapabilityViewModel",
    "ToolViewModel",
    "SettingsViewModel",
    "MemoryViewModel",
]
