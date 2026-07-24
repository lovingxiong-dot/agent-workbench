"""tests/provider/test_provider_adapter.py — ProviderAdapter 测试。

v6.10.0-alpha Provider Integration Foundation。

边界：
  - 测试 ProviderEndpoint → ProviderViewModel 转换
  - 测试状态推导（disabled / needs_config / no_models / active）
  - 测试 protocol enum → string 转换
  - 不发起网络请求，不调用任何 Provider 实现
"""
from __future__ import annotations

import pytest

from agent_workbench.presentation.adapters.provider_adapter import ProviderAdapter
from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)


class TestProviderAdapterBasics:
    """ProviderAdapter 基础转换测试。"""

    def test_to_view_model_basic(self) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai_main",
            protocol=ProviderProtocol.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            models=["gpt-4", "gpt-3.5-turbo"],
            enabled=True,
        )
        adapter = ProviderAdapter()
        vm = adapter.to_view_model(endpoint)

        assert vm.provider_id == "openai_main"
        assert vm.name == "Openai_main"
        assert vm.protocol == "openai"
        assert vm.status == "active"
        assert vm.models == ["gpt-4", "gpt-3.5-turbo"]
        assert vm.base_url == "https://api.openai.com/v1"
        assert vm.has_api_key is True
        assert vm.metadata["enabled"] == "True"

    def test_to_list_view_model_with_active(self) -> None:
        endpoints = [
            ProviderEndpoint(
                provider_id="echo",
                protocol=ProviderProtocol.ECHO,
                models=["echo-1"],
            ),
            ProviderEndpoint(
                provider_id="openai",
                protocol=ProviderProtocol.OPENAI,
                api_key="sk-test",
                models=["gpt-4"],
            ),
        ]
        adapter = ProviderAdapter()
        list_vm = adapter.to_list_view_model(endpoints, active_provider_id="openai")

        assert list_vm.total_count == 2
        assert list_vm.active_provider_id == "openai"
        active = list_vm.get_active()
        assert active is not None
        assert active.provider_id == "openai"

    def test_to_list_view_model_empty(self) -> None:
        adapter = ProviderAdapter()
        list_vm = adapter.to_list_view_model([])

        assert list_vm.total_count == 0
        assert list_vm.providers == []
        assert list_vm.get_active() is None


class TestProviderAdapterStatusDerivation:
    """Provider 状态推导测试。"""

    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        return ProviderAdapter()

    def test_status_disabled(self, adapter: ProviderAdapter) -> None:
        endpoint = ProviderEndpoint(
            provider_id="p",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            enabled=False,
        )
        assert adapter.to_view_model(endpoint).status == "disabled"

    def test_status_needs_config_openai(self, adapter: ProviderAdapter) -> None:
        endpoint = ProviderEndpoint(
            provider_id="p",
            protocol=ProviderProtocol.OPENAI,
            api_key="",
            models=["m"],
        )
        assert adapter.to_view_model(endpoint).status == "needs_config"

    def test_status_active_echo_without_key(self, adapter: ProviderAdapter) -> None:
        endpoint = ProviderEndpoint(
            provider_id="echo",
            protocol=ProviderProtocol.ECHO,
            api_key="",
            models=["m"],
        )
        assert adapter.to_view_model(endpoint).status == "active"

    def test_status_no_models(self, adapter: ProviderAdapter) -> None:
        endpoint = ProviderEndpoint(
            provider_id="p",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=[],
        )
        assert adapter.to_view_model(endpoint).status == "no_models"

    def test_status_active_full_config(self, adapter: ProviderAdapter) -> None:
        endpoint = ProviderEndpoint(
            provider_id="p",
            protocol=ProviderProtocol.DEEPSEEK,
            api_key="sk",
            models=["deepseek-chat"],
        )
        assert adapter.to_view_model(endpoint).status == "active"


class TestProviderAdapterProtocolDerivation:
    """Provider protocol 推导测试。"""

    def test_enum_to_string(self) -> None:
        adapter = ProviderAdapter()
        endpoint = ProviderEndpoint(
            provider_id="claude",
            protocol=ProviderProtocol.ANTHROPIC,
            api_key="sk",
        )
        vm = adapter.to_view_model(endpoint)
        assert vm.protocol == "anthropic"

    def test_all_protocols_have_string_value(self) -> None:
        adapter = ProviderAdapter()
        for protocol in ProviderProtocol:
            endpoint = ProviderEndpoint(
                provider_id=f"test_{protocol.value}",
                protocol=protocol,
                api_key="sk" if protocol != ProviderProtocol.ECHO else "",
            )
            vm = adapter.to_view_model(endpoint)
            assert vm.protocol == protocol.value