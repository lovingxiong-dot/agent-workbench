"""agent_workbench/runtime/provider_registry.py — Provider 注册表。

职责：
- 注册 Provider 类（按 provider name 索引）。
- 按需实例化 Provider。
- 暴露所有已注册 Provider 的 MetadataDefinition，供 Workbench UI 选择。
"""
from __future__ import annotations

from typing import Type

from agent_workbench.metadata import MetadataAction, MetadataDefinition, MetadataProperty, MetadataStatistics, ValueType
from agent_workbench.services.claude_provider import ClaudeProvider
from agent_workbench.services.deepseek_provider import DeepSeekProvider
from agent_workbench.services.echo_provider import EchoProvider
from agent_workbench.services.gemini_provider import GeminiProvider
from agent_workbench.services.kimi_provider import KimiProvider
from agent_workbench.services.model_provider import ModelProvider
from agent_workbench.services.openai_provider import OpenAIProvider
from agent_workbench.services.qwen_provider import QwenProvider


class ProviderRegistry:
    """Provider 注册表。"""

    def __init__(self) -> None:
        self._providers: dict[str, Type[ModelProvider]] = {}

    def register(self, provider_class: Type[ModelProvider]) -> None:
        """注册一个 Provider 类。"""
        instance = provider_class()
        self._providers[instance.name] = provider_class

    def get(self, name: str) -> ModelProvider | None:
        """按名称实例化一个 Provider；未注册返回 None。"""
        provider_class = self._providers.get(name)
        if provider_class is None:
            return None
        return provider_class()

    def has(self, name: str) -> bool:
        """是否已注册指定 Provider。"""
        return name in self._providers

    def list_names(self) -> list[str]:
        """返回所有已注册 Provider 名称（有序）。"""
        return sorted(self._providers.keys())

    def list_providers(self) -> list[MetadataDefinition]:
        """返回所有已注册 Provider 的 MetadataDefinition。"""
        return [self._provider_metadata(name) for name in self.list_names()]

    def _provider_metadata(self, name: str) -> MetadataDefinition:
        provider_class = self._providers[name]
        instance = provider_class()
        return MetadataDefinition(
            id=name,
            type="provider",
            name=name.capitalize(),
            description=f"{name.capitalize()} 兼容 Provider。",
            icon="cpu-chip",
            properties=[
                MetadataProperty(
                    id="model",
                    name="Model",
                    description="模型名称。",
                    value_type=ValueType.STRING,
                ),
                MetadataProperty(
                    id="api_key",
                    name="API Key",
                    description="API 密钥。",
                    value_type=ValueType.SECRET,
                    sensitive=True,
                ),
                MetadataProperty(
                    id="base_url",
                    name="Base URL",
                    description="自定义 API 端点（可选）。",
                    value_type=ValueType.STRING,
                ),
                MetadataProperty(
                    id="enabled",
                    name="Enabled",
                    description="是否启用该 Provider。",
                    value_type=ValueType.BOOL,
                    current_value=True,
                ),
            ],
            statistics=[
                MetadataStatistics(id="type", name="Type", value=name, unit="name"),
            ],
            actions=[
                MetadataAction(id="validate", label="Validate", icon="check"),
            ],
        )


def create_default_provider_registry() -> ProviderRegistry:
    """创建包含所有内置 Provider 的默认注册表。"""
    registry = ProviderRegistry()
    for provider_class in (
        EchoProvider,
        OpenAIProvider,
        ClaudeProvider,
        GeminiProvider,
        KimiProvider,
        QwenProvider,
        DeepSeekProvider,
    ):
        registry.register(provider_class)
    return registry
