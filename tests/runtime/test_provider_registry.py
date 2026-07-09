"""Tests for ProviderRegistry and built-in provider discovery."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.metadata import MetadataDefinition
from agent_workbench.runtime.modules.model_module import ModelModule
from agent_workbench.runtime.provider_registry import ProviderRegistry, create_default_provider_registry
from agent_workbench.services.claude_provider import ClaudeProvider
from agent_workbench.services.deepseek_provider import DeepSeekProvider
from agent_workbench.services.echo_provider import EchoProvider
from agent_workbench.services.gemini_provider import GeminiProvider
from agent_workbench.services.kimi_provider import KimiProvider
from agent_workbench.services.model_provider import ModelProvider
from agent_workbench.services.openai_provider import OpenAIProvider
from agent_workbench.services.qwen_provider import QwenProvider


class TestProviderRegistry:
    def test_create_default_registry_contains_all_builtin_providers(self):
        registry = create_default_provider_registry()
        names = registry.list_names()
        assert names == sorted(names)
        assert set(names) == {
            "claude",
            "deepseek",
            "echo",
            "gemini",
            "kimi",
            "openai",
            "qwen",
        }

    @pytest.mark.parametrize(
        "name,provider_class",
        [
            ("echo", EchoProvider),
            ("openai", OpenAIProvider),
            ("claude", ClaudeProvider),
            ("gemini", GeminiProvider),
            ("kimi", KimiProvider),
            ("qwen", QwenProvider),
            ("deepseek", DeepSeekProvider),
        ],
    )
    def test_get_instantiates_provider(self, name: str, provider_class: type[ModelProvider]):
        registry = create_default_provider_registry()
        provider = registry.get(name)
        assert provider is not None
        assert isinstance(provider, provider_class)
        assert provider.name == name

    def test_get_unknown_returns_none(self):
        registry = create_default_provider_registry()
        assert registry.get("unknown") is None

    def test_has_checks_registration(self):
        registry = create_default_provider_registry()
        assert registry.has("openai") is True
        assert registry.has("missing") is False

    def test_register_duplicate_updates_entry(self):
        registry = ProviderRegistry()
        registry.register(EchoProvider)
        registry.register(EchoProvider)
        assert registry.list_names() == ["echo"]

    def test_list_providers_returns_metadata(self):
        registry = create_default_provider_registry()
        metas = registry.list_providers()
        assert len(metas) == 7
        assert all(isinstance(m, MetadataDefinition) for m in metas)
        assert {m.id for m in metas} == set(registry.list_names())


class TestModelModuleProviderTypes:
    def test_model_module_exposes_registry_provider_types(self):
        module = ModelModule()
        types = module.provider_types()
        assert isinstance(types, list)
        assert set(types) == {
            "claude",
            "deepseek",
            "echo",
            "gemini",
            "kimi",
            "openai",
            "qwen",
        }
