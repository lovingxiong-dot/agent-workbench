"""agent_workbench/services/deepseek_provider.py — DeepSeek Provider。

通过 OpenAI 兼容接口接入 DeepSeek。
默认 endpoint：https://api.deepseek.com/v1
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek 兼容 Provider。"""

    @property
    def name(self) -> str:
        return "deepseek"

    def configure(self, config: Dict[str, Any]) -> None:
        if not config.get("base_url"):
            config = {**config, "base_url": "https://api.deepseek.com/v1"}
        super().configure(config)
