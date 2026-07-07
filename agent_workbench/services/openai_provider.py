"""agent_workbench/services/openai_provider.py — OpenAI 兼容 Provider。

支持任何 OpenAI 兼容端点（OpenAI、DeepSeek、本地 vLLM/Ollama 等）。
配置项：base_url, api_key, model, temperature, top_p, max_tokens, request_timeout。
"""
from __future__ import annotations

import os
import re
from collections.abc import Iterator
from typing import Any, Dict, List

from agent_workbench.services.model_provider import ModelProvider


class OpenAIProvider(ModelProvider):
    """OpenAI 兼容 Provider，支持流式输出。"""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._client: Any | None = None

    @property
    def name(self) -> str:
        return "openai"

    def configure(self, config: Dict[str, Any]) -> None:
        """保存 provider 专属配置。"""
        self._config = config
        self._client = None  # 配置变更后重置客户端

    def chat(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> str:
        """非流式生成完整回复。"""
        return "".join(self.chat_stream(messages, params))

    def chat_stream(
        self, messages: List[Dict[str, str]], params: Dict[str, Any]
    ) -> Iterator[str]:
        """流式生成回复。"""
        client = self._get_client()
        model = self._config.get("model") or params.get("model", "gpt-4o-mini")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2048)
        top_p = params.get("top_p", 1.0)
        timeout = self._config.get("request_timeout", 120)

        stream = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            timeout=timeout,
            stream=True,
        )
        for chunk in stream:
            delta = getattr(chunk.choices[0].delta, "content", None)
            if delta:
                yield delta

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """校验必要配置。"""
        model = config.get("model")
        api_key = self._expand(config.get("api_key", ""))
        return isinstance(model, str) and bool(model) and isinstance(api_key, str) and bool(api_key)

    def _get_client(self) -> Any:
        """延迟创建并缓存 openai 客户端。"""
        if self._client is not None:
            return self._client

        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("openai package is required for OpenAIProvider") from exc

        base_url = self._config.get("base_url", "https://api.openai.com/v1")
        api_key = self._expand(self._config.get("api_key", ""))
        if not api_key:
            raise RuntimeError("OpenAI provider api_key is empty")

        self._client = openai.OpenAI(base_url=base_url, api_key=api_key)
        return self._client

    @staticmethod
    def _expand(value: Any) -> Any:
        """展开 ${VAR} 形式的环境变量。"""
        if not isinstance(value, str):
            return value
        match = re.fullmatch(r"\$\{([^}]+)\}", value)
        if match:
            return os.environ.get(match.group(1), "")
        return value
