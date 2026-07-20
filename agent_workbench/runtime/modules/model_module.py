"""agent_workbench/runtime/modules/model_module.py — Model 模块。

职责：
- Provider Registry。
- Sampling / Context 参数管理。
- 默认 Provider 选择。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ValueType,
)
from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.runtime.provider_registry import create_default_provider_registry
from agent_workbench.services.model_provider import ModelProvider

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class ModelModule(BaseRuntimeModule):
    """Model 能力模块。

    支持一个 Provider 下多个 Model 运行时切换。
    """

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._registry = create_default_provider_registry()
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: str = "echo"
        self._current_model: str = ""
        self._available_models: Dict[str, list[str]] = {}  # provider_name → [model_names]
        self._sampling: Dict[str, Any] = {}
        self._context: Dict[str, Any] = {}

    @property
    def namespace(self) -> str:
        return "model"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Model 配置：注册 provider、更新参数、解析可用模型列表。"""
        providers_config = store.get("model.providers", [])
        new_providers: Dict[str, ModelProvider] = {}
        new_models: Dict[str, list[str]] = {}
        for cfg in providers_config:
            name = cfg.get("name")
            ptype = cfg.get("type")
            if not name or not ptype:
                continue
            if not cfg.get("enabled", True):
                continue
            provider = self._create_provider(ptype)
            if provider is not None:
                provider.configure(cfg)
                new_providers[name] = provider
                # 解析可用模型列表
                models = cfg.get("models", [cfg.get("model", "")])
                if isinstance(models, list) and models:
                    new_models[name] = models

        self._providers = new_providers
        self._available_models = new_models
        self._default_provider = store.get("model.default_provider", "echo")
        # 默认使用第一个模型
        default_models = new_models.get(self._default_provider, [])
        if not self._current_model and default_models:
            self._current_model = default_models[0]
        self._sampling = store.get("model.sampling", {"temperature": 0.7, "max_tokens": 2048})
        self._context = store.get("model.context", {"max_history": 20})

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """使用默认 provider 和当前模型生成回复。"""
        provider = self._providers.get(self._default_provider)
        if provider is None:
            return f"[错误：未找到 provider '{self._default_provider}']"
        params = {**self._sampling, **self._context}
        if self._current_model:
            params["model"] = self._current_model
        return provider.chat(messages, params)

    def chat_stream(self, messages: List[Dict[str, str]]):
        """使用默认 provider 和当前模型流式生成回复。"""
        provider = self._providers.get(self._default_provider)
        if provider is None:
            return iter([f"[错误：未找到 provider '{self._default_provider}']"])
        params = {**self._sampling, **self._context}
        if self._current_model:
            params["model"] = self._current_model
        return provider.chat_stream(messages, params)

    def switch_model(self, model_name: str) -> bool:
        """切换到指定模型（需在当前 Provider 的可用模型列表中）。"""
        models = self._available_models.get(self._default_provider, [])
        if model_name in models:
            self._current_model = model_name
            return True
        return False

    def list_models(self) -> list[str]:
        """返回当前 Provider 的可用模型列表。"""
        return list(self._available_models.get(self._default_provider, []))

    @property
    def current_model(self) -> str:
        """当前使用的模型名称。"""
        return self._current_model

    def list_providers(self) -> List[Dict[str, Any]]:
        """返回当前可用 provider 列表。"""
        return [{"name": name, "type": p.name} for name, p in self._providers.items()]

    def provider_types(self) -> list[str]:
        """返回注册表中所有支持的 Provider 类型名称。"""
        return self._registry.list_names()

    def get_active_provider_info(self) -> Dict[str, Any]:
        """返回当前默认 provider 的摘要信息（供 Trace 使用）。"""
        provider = self._providers.get(self._default_provider)
        if provider is None:
            return {"provider": self._default_provider, "type": "unknown"}
        info: Dict[str, Any] = {"provider": self._default_provider, "type": provider.name}
        config = getattr(provider, "_config", None)
        if isinstance(config, dict):
            info["model"] = config.get("model", "—")
            info["endpoint"] = config.get("base_url", "—")
        return info

    def _create_provider(self, ptype: str) -> ModelProvider | None:
        """根据类型从注册表创建 provider 实例。"""
        return self._registry.get(ptype)

    def metadata(self) -> MetadataDefinition:
        """返回 Model Capability Metadata。"""
        provider_names = list(self._providers.keys())
        return MetadataDefinition(
            id="model",
            type="model",
            name="Model",
            description="管理模型 Provider 与采样参数。",
            icon="cpu-chip",
            properties=[
                MetadataProperty(
                    id="default_provider",
                    name="Default Provider",
                    description="当前默认使用的模型 Provider。",
                    value_type=ValueType.ENUM,
                    current_value=self._default_provider,
                    options=provider_names,
                ),
                MetadataProperty(
                    id="sampling.temperature",
                    name="Temperature",
                    description="采样温度，控制输出随机性。",
                    value_type=ValueType.FLOAT,
                    current_value=self._sampling.get("temperature", 0.7),
                ),
                MetadataProperty(
                    id="sampling.max_tokens",
                    name="Max Tokens",
                    description="单次生成最大 Token 数。",
                    value_type=ValueType.INT,
                    current_value=self._sampling.get("max_tokens", 2048),
                ),
            ],
            statistics=[
                MetadataStatistics(id="providers", name="Providers", value=len(provider_names), unit="count"),
                MetadataStatistics(id="active_provider", name="Active", value=self._default_provider, unit="name"),
            ],
            actions=[
                MetadataAction(id="validate", label="Validate Provider", icon="check"),
            ],
        )
