"""agent_workbench/runtime/modules/model_module.py — Model 模块。

职责：
- Provider Registry。
- Sampling / Context 参数管理。
- 默认 Provider 选择。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.services.echo_provider import EchoProvider
from agent_workbench.services.model_provider import ModelProvider

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class ModelModule(BaseRuntimeModule):
    """Model 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: str = "echo"
        self._sampling: Dict[str, Any] = {}
        self._context: Dict[str, Any] = {}

    @property
    def namespace(self) -> str:
        return "model"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Model 配置：注册 provider、更新参数。"""
        providers_config = store.get("model.providers", [])
        new_providers: Dict[str, ModelProvider] = {}
        for cfg in providers_config:
            name = cfg.get("name")
            ptype = cfg.get("type")
            if not name or not ptype:
                continue
            if not cfg.get("enabled", True):
                continue
            provider = self._create_provider(ptype)
            if provider is not None:
                new_providers[name] = provider

        self._providers = new_providers
        self._default_provider = store.get("model.default_provider", "echo")
        self._sampling = store.get("model.sampling", {"temperature": 0.7, "max_tokens": 2048})
        self._context = store.get("model.context", {"max_history": 20})

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """使用默认 provider 生成回复。"""
        provider = self._providers.get(self._default_provider)
        if provider is None:
            return f"[错误：未找到 provider '{self._default_provider}']"
        return provider.chat(messages, {**self._sampling, **self._context})

    def list_providers(self) -> List[Dict[str, Any]]:
        """返回当前可用 provider 列表。"""
        return [{"name": name, "type": p.name} for name, p in self._providers.items()]

    @staticmethod
    def _create_provider(ptype: str) -> ModelProvider | None:
        """根据类型创建 provider 实例。"""
        if ptype == "echo":
            return EchoProvider()
        return None

    def to_form(self) -> Dict[str, Any]:
        """返回 Model 配置表单。"""
        return {
            "title": "Model",
            "description": "管理模型 Provider 与采样参数。",
            "fields": [
                {
                    "name": "default_provider",
                    "type": "select",
                    "label": "Default Provider",
                    "options": list(self._providers.keys()),
                    "value": self._default_provider,
                },
                {
                    "name": "temperature",
                    "type": "float",
                    "label": "Temperature",
                    "min": 0.0,
                    "max": 2.0,
                    "value": self._sampling.get("temperature", 0.7),
                },
                {
                    "name": "max_tokens",
                    "type": "integer",
                    "label": "Max Tokens",
                    "min": 1,
                    "max": 128000,
                    "value": self._sampling.get("max_tokens", 2048),
                },
                {
                    "name": "max_history",
                    "type": "integer",
                    "label": "Max History",
                    "min": 1,
                    "max": 1000,
                    "value": self._context.get("max_history", 20),
                },
            ],
        }
