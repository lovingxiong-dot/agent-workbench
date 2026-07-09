"""agent_workbench/services/qwen_provider.py — Qwen (DashScope) Provider。

通过 OpenAI 兼容接口接入阿里云百炼 Qwen。
默认 endpoint：https://dashscope.aliyuncs.com/compatible-mode/v1
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.openai_provider import OpenAIProvider


class QwenProvider(OpenAIProvider):
    """Qwen 兼容 Provider。"""

    @property
    def name(self) -> str:
        return "qwen"

    def configure(self, config: Dict[str, Any]) -> None:
        if not config.get("base_url"):
            config = {**config, "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
        super().configure(config)
