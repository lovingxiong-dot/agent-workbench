"""agent_workbench/services/kimi_provider.py — Kimi (Moonshot) Provider。

通过 OpenAI 兼容接口接入 Moonshot Kimi。
默认 endpoint：https://api.moonshot.cn/v1
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.openai_provider import OpenAIProvider


class KimiProvider(OpenAIProvider):
    """Kimi 兼容 Provider。"""

    @property
    def name(self) -> str:
        return "kimi"

    def configure(self, config: Dict[str, Any]) -> None:
        if not config.get("base_url"):
            config = {**config, "base_url": "https://api.moonshot.cn/v1"}
        super().configure(config)
