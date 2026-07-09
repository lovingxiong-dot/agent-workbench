"""agent_workbench/services/gemini_provider.py — Gemini Provider。

通过 OpenAI 兼容接口接入 Google Gemini。
默认 endpoint：https://generativelanguage.googleapis.com/v1beta/openai
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.openai_provider import OpenAIProvider


class GeminiProvider(OpenAIProvider):
    """Gemini 兼容 Provider。"""

    @property
    def name(self) -> str:
        return "gemini"

    def configure(self, config: Dict[str, Any]) -> None:
        if not config.get("base_url"):
            config = {**config, "base_url": "https://generativelanguage.googleapis.com/v1beta/openai"}
        super().configure(config)
