"""tests/provider/test_provider_service.py — ProviderServiceController 测试。

v6.10.0-alpha Provider Integration Foundation。

边界：
  - 测试 ProviderServiceController 聚合逻辑
  - 使用 Mock ConfigStore / Mock RuntimeProviderBackend
  - 不修改 Runtime Kernel
  - Configuration-Driven 验证：UI 操作 → ConfigStore → Runtime Backend
"""
from __future__ import annotations

from typing import List, Optional

import pytest

from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.services.provider_registry import (
    ProviderInfo,
    RuntimeProviderBackend,
    WorkbenchProviderRegistry,
)
from agent_workbench.presentation.services.provider_service import (
    ProviderServiceController,
    WorkbenchProviderConfigBackend,
)


class MockConfigStore:
    """Mock ConfigStore（用于 ProviderServiceController 测试）。"""

    def __init__(self, initial: Optional[dict] = None) -> None:
        self._data: dict = initial or {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def add(self, key: str, value) -> None:
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(value)


class MockRuntimeProviderBackend:
    """Mock RuntimeProviderBackend。"""

    def __init__(self, providers: Optional[List[ProviderInfo]] = None, active: Optional[str] = None) -> None:
        self._providers = providers or []
        self._active = active

    def list_provider_names(self) -> List[str]:
        return [p.provider_id for p in self._providers]

    def list_provider_infos(self) -> List[ProviderInfo]:
        return list(self._providers)

    def get_active_provider_name(self) -> Optional[str]:
        return self._active

    def switch_provider(self, provider_name: str) -> bool:
        if provider_name not in self.list_provider_names():
            return False
        self._active = provider_name
        return True


def make_controller(
    providers: Optional[List[ProviderInfo]] = None,
    active: Optional[str] = None,
    initial_configs: Optional[List[dict]] = None,
) -> ProviderServiceController:
    """工厂：构造 ProviderServiceController。"""
    backend = MockRuntimeProviderBackend(providers, active)
    registry = WorkbenchProviderRegistry(backend)
    store = MockConfigStore({"model.providers": initial_configs or []})
    config_backend = WorkbenchProviderConfigBackend(store)
    return ProviderServiceController(registry, config_backend)


class TestProviderServiceList:
    """ProviderServiceController.list_view_model 测试。"""

    def test_empty_list(self) -> None:
        controller = make_controller()
        vm = controller.list_view_model()
        assert vm.total_count == 0
        assert vm.providers == []

    def test_list_with_configs(self) -> None:
        configs = [
            {
                "name": "openai",
                "type": "openai",
                "api_key": "sk-test",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "enabled": True,
            },
            {
                "name": "echo",
                "type": "echo",
                "models": ["echo-1"],
                "enabled": True,
            },
        ]
        controller = make_controller(
            providers=[
                ProviderInfo(provider_id="openai", type_name="openai"),
                ProviderInfo(provider_id="echo", type_name="echo"),
            ],
            active="openai",
            initial_configs=configs,
        )
        vm = controller.list_view_model()
        assert vm.total_count == 2
        assert vm.active_provider_id == "openai"

    def test_get_view_model(self) -> None:
        configs = [
            {
                "name": "openai",
                "type": "openai",
                "api_key": "sk",
                "models": ["gpt-4"],
                "enabled": True,
            }
        ]
        controller = make_controller(initial_configs=configs)
        vm = controller.get_view_model("openai")
        assert vm is not None
        assert vm.provider_id == "openai"

    def test_get_view_model_missing(self) -> None:
        controller = make_controller()
        assert controller.get_view_model("nonexistent") is None


class TestProviderServiceAdd:
    """ProviderServiceController.add_provider 测试。"""

    def test_add_success(self) -> None:
        controller = make_controller(
            providers=[ProviderInfo(provider_id="openai", type_name="openai")],
        )
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            models=["gpt-4"],
        )
        result = controller.add_provider(endpoint)
        assert result.success is True
        assert result.provider_id == "openai"
        assert result.validation is not None
        assert result.validation.valid is True

    def test_add_validation_failure(self) -> None:
        controller = make_controller()
        # Missing API key for openai
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="",
            models=["gpt-4"],
        )
        result = controller.add_provider(endpoint)
        assert result.success is False
        assert any(i.code == "MISSING_API_KEY" for i in result.validation.errors)

    def test_add_persists_to_configstore(self) -> None:
        store = MockConfigStore()
        backend = MockRuntimeProviderBackend()
        registry = WorkbenchProviderRegistry(backend)
        config_backend = WorkbenchProviderConfigBackend(store)
        controller = ProviderServiceController(registry, config_backend)

        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        controller.add_provider(endpoint)
        # ConfigStore 现在应该有 model.providers
        providers = store.get("model.providers", [])
        assert len(providers) == 1
        assert providers[0]["name"] == "openai"


class TestProviderServiceRemove:
    """ProviderServiceController.remove_provider 测试。"""

    def test_remove_success(self) -> None:
        configs = [{"name": "openai", "type": "openai", "models": ["gpt-4"]}]
        controller = make_controller(
            providers=[ProviderInfo(provider_id="openai", type_name="openai")],
            initial_configs=configs,
        )
        result = controller.remove_provider("openai")
        assert result.success is True

    def test_remove_active_fails(self) -> None:
        configs = [{"name": "openai", "type": "openai", "models": ["gpt-4"]}]
        controller = make_controller(
            providers=[ProviderInfo(provider_id="openai", type_name="openai")],
            active="openai",
            initial_configs=configs,
        )
        result = controller.remove_provider("openai")
        assert result.success is False
        # Error message should indicate the provider is active (CN/EN)
        assert ("激活" in result.error) or ("active" in result.error.lower())

    def test_remove_nonexistent(self) -> None:
        controller = make_controller()
        result = controller.remove_provider("nonexistent")
        assert result.success is False


class TestProviderServiceSwitch:
    """ProviderServiceController.switch_provider 测试。"""

    def test_switch_success(self) -> None:
        configs = [{"name": "openai", "type": "openai", "models": ["gpt-4"]}]
        controller = make_controller(
            providers=[ProviderInfo(provider_id="openai", type_name="openai")],
            initial_configs=configs,
        )
        result = controller.switch_provider("openai")
        assert result.success is True
        assert result.new_id == "openai"
        # Verify default_provider was updated
        # (我们没有在 store 里 set, 验证 switch 委托了 registry)

    def test_switch_unregistered(self) -> None:
        controller = make_controller()
        result = controller.switch_provider("nonexistent")
        assert result.success is False


class TestConfigBackend:
    """WorkbenchProviderConfigBackend 测试。"""

    def test_upsert_new(self) -> None:
        store = MockConfigStore()
        backend = WorkbenchProviderConfigBackend(store)
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        ok = backend.upsert_provider_config(endpoint)
        assert ok is True
        assert len(backend.list_provider_configs()) == 1

    def test_upsert_existing(self) -> None:
        store = MockConfigStore({"model.providers": [
            {"name": "openai", "type": "openai", "api_key": "old", "models": ["gpt-3.5"]}
        ]})
        backend = WorkbenchProviderConfigBackend(store)
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="new",
            models=["gpt-4"],
        )
        backend.upsert_provider_config(endpoint)
        configs = backend.list_provider_configs()
        assert len(configs) == 1
        assert configs[0]["api_key"] == "new"

    def test_remove_existing(self) -> None:
        store = MockConfigStore({"model.providers": [
            {"name": "openai", "type": "openai", "models": ["gpt-4"]},
            {"name": "echo", "type": "echo", "models": ["e"]},
        ]})
        backend = WorkbenchProviderConfigBackend(store)
        ok = backend.remove_provider_config("openai")
        assert ok is True
        configs = backend.list_provider_configs()
        assert len(configs) == 1
        assert configs[0]["name"] == "echo"

    def test_remove_nonexistent(self) -> None:
        store = MockConfigStore({"model.providers": []})
        backend = WorkbenchProviderConfigBackend(store)
        ok = backend.remove_provider_config("nonexistent")
        assert ok is False

    def test_endpoint_to_config_roundtrip(self) -> None:
        store = MockConfigStore()
        backend = WorkbenchProviderConfigBackend(store)
        endpoint = ProviderEndpoint(
            provider_id="custom_main",
            protocol=ProviderProtocol.CUSTOM,
            api_key="k",
            base_url="http://localhost:8080/v1",
            models=["model-a", "model-b"],
            enabled=False,
        )
        backend.upsert_provider_config(endpoint)
        configs = backend.list_provider_configs()
        config = configs[0]
        assert config["name"] == "custom_main"
        assert config["type"] == "custom"
        assert config["base_url"] == "http://localhost:8080/v1"
        assert config["models"] == ["model-a", "model-b"]
        assert config["enabled"] is False


class TestModelModuleBackend:
    """ModelModuleBackend 测试（适配 Runtime ModelModule）。"""

    def test_list_provider_names(self) -> None:
        class MockModelModule:
            def list_providers(self):
                return [{"name": "openai"}, {"name": "echo"}]

            def get_current_provider_name(self):
                return "openai"

            def switch_provider(self, name):
                return True

            def list_models(self):
                return ["gpt-4"]

        from agent_workbench.presentation.services.model_module_backend import (
            ModelModuleBackend,
        )
        backend = ModelModuleBackend(MockModelModule())
        names = backend.list_provider_names()
        assert names == ["openai", "echo"]

    def test_get_active_provider_name(self) -> None:
        class MockModelModule:
            def list_providers(self):
                return []
            def get_current_provider_name(self):
                return "echo"
            def switch_provider(self, name):
                return False
            def list_models(self):
                return []

        from agent_workbench.presentation.services.model_module_backend import (
            ModelModuleBackend,
        )
        backend = ModelModuleBackend(MockModelModule())
        assert backend.get_active_provider_name() == "echo"

    def test_switch_provider(self) -> None:
        class MockModelModule:
            def list_providers(self):
                return [{"name": "openai"}]
            def get_current_provider_name(self):
                return "echo"
            def switch_provider(self, name):
                return name == "openai"
            def list_models(self):
                return []

        from agent_workbench.presentation.services.model_module_backend import (
            ModelModuleBackend,
        )
        backend = ModelModuleBackend(MockModelModule())
        assert backend.switch_provider("openai") is True
        assert backend.switch_provider("nonexistent") is False