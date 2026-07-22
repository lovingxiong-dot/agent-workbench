"""presentation/adapters/settings_adapter.py - SettingsAdapter.

Converts Runtime Config/Provider objects to SettingsViewModel.
"""
from __future__ import annotations

from agent_workbench.presentation.view_models.settings import SettingsViewModel


class SettingsAdapter:
    """Converts Runtime Config/Provider objects to SettingsViewModel for UI consumption."""

    def to_view_model(self, config: object) -> SettingsViewModel:
        """Convert a Runtime Config object to SettingsViewModel.

        Args:
            config: Runtime Config object (from ConfigStore or ProviderRegistry).

        Returns:
            SettingsViewModel suitable for UI rendering.
        """
        return SettingsViewModel(
            provider=getattr(config, "provider", ""),
            provider_options=list(getattr(config, "provider_options", [])),
            model=getattr(config, "model", ""),
            model_options=list(getattr(config, "model_options", [])),
            temperature=float(getattr(config, "temperature", 0.7)),
            max_tokens=int(getattr(config, "max_tokens", 4096)),
            top_p=float(getattr(config, "top_p", 0.9)),
            api_key=getattr(config, "api_key", ""),
            base_url=getattr(config, "base_url", ""),
            theme=getattr(config, "theme", "dark"),
            theme_options=list(getattr(config, "theme_options", ["dark", "light"])),
            system_prompt=getattr(config, "system_prompt", ""),
            default_agent=getattr(config, "default_agent", ""),
        )