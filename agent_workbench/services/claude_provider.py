"""agent_workbench/services/claude_provider.py — Claude Provider。

通过 OpenAI 兼容接口接入 Anthropic Claude。
默认 endpoint：https://api.anthropic.com/v1
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.openai_provider import OpenAIProvider


class ClaudeProvider(OpenAIProvider):
    """Claude 兼容 Provider。"""

    @property
    def name(self) -> str:
        return "claude"

    def configure(self, config: Dict[str, Any]) -> None:
        if not config.get("base_url"):
            config = {**config, "base_url": "https://api.anthropic.com/v1"}
        super().configure(config)
