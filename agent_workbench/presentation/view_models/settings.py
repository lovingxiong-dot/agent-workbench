"""presentation/view_models/settings.py - SettingsViewModel.

Represents user-configurable settings in the UI (RightPanel settings page).
Pure data - no Runtime imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SettingsViewModel:
    """User-configurable settings displayed in the RightPanel settings page.

    The UI renders this as form controls in the settings panel. It knows
    nothing about ConfigStore or ProviderRegistry.
    """

    provider: str = ""
    provider_options: List[str] = field(default_factory=list)
    model: str = ""
    model_options: List[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    api_key: str = ""
    base_url: str = ""
    theme: str = "dark"  # dark, light
    theme_options: List[str] = field(default_factory=lambda: ["dark", "light"])
    system_prompt: str = ""
    default_agent: str = ""