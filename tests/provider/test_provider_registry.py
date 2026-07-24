"""tests/provider/test_provider_registry.py — WorkbenchProviderRegistry 测试。

v6.10.0-alpha Provider Integration Foundation。

边界：
  - 测试 v6-agent 层聚合逻辑
  - 使用 Mock RuntimeProviderBackend，不依赖真实 Runtime
  - 不修改 Runtime Kernel
"""
from __future__ import annotations

import pytest

from agent_workbench.presentation.services.provider_registry import (
    ProviderInfo,
    RuntimeProviderBackend,
    WorkbenchProviderRegistry,
)


class MockRuntimeProviderBackend:
    """Mock Runtime Provider Backend（满足 RuntimeProviderBackend Protocol）。"""

    def __init__(
        self,
        providers: list[ProviderInfo] | None = None,
        active: str | None = None,
        switch_should_fail: bool = False,
    ) -> None:
        self._providers = providers or []
        self._active = active
        self._switch_should_fail = switch_should_fail

    def list_provider_names(self) -> list[str]:
        return [p.provider_id for p in self._providers]

    def list_provider_infos(self) -> list[ProviderInfo]:
        return list(self._providers)

    def get_active_provider_name(self) -> str | None:
        return self._active

    def switch_provider(self, provider_name: str) -> bool:
        if self._switch_should_fail:
            return False
        self._active = provider_name
        return True


class TestWorkbenchProviderRegistryBasics:
    """WorkbenchProviderRegistry 基础测试。"""

    def test_init_loads_active_provider(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[ProviderInfo(provider_id="echo", type_name="echo")],
            active="echo",
        )
        registry = WorkbenchProviderRegistry(backend)
        assert registry.active_provider_id == "echo"

    def test_init_no_active(self) -> None:
        backend = MockRuntimeProviderBackend()
        registry = WorkbenchProviderRegistry(backend)
        assert registry.active_provider_id is None

    def test_list_providers(self) -> None:
        providers = [
            ProviderInfo(provider_id="echo", type_name="echo", available_models=["echo-1"]),
            ProviderInfo(
                provider_id="openai",
                type_name="openai",
                available_models=["gpt-4", "gpt-3.5"],
            ),
        ]
        backend = MockRuntimeProviderBackend(providers=providers)
        registry = WorkbenchProviderRegistry(backend)

        result = registry.list_providers()
        assert len(result) == 2
        assert result[0].provider_id == "echo"
        assert result[1].available_models == ["gpt-4", "gpt-3.5"]

    def test_list_provider_names(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[
                ProviderInfo(provider_id="openai", type_name="openai"),
                ProviderInfo(provider_id="deepseek", type_name="deepseek"),
            ],
        )
        registry = WorkbenchProviderRegistry(backend)
        names = registry.list_provider_names()
        assert names == ["openai", "deepseek"]

    def test_get_provider_info_existing(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[
                ProviderInfo(provider_id="openai", type_name="openai"),
                ProviderInfo(provider_id="deepseek", type_name="deepseek"),
            ],
        )
        registry = WorkbenchProviderRegistry(backend)
        info = registry.get_provider_info("deepseek")
        assert info is not None
        assert info.provider_id == "deepseek"
        assert info.type_name == "deepseek"

    def test_get_provider_info_missing(self) -> None:
        backend = MockRuntimeProviderBackend(providers=[])
        registry = WorkbenchProviderRegistry(backend)
        assert registry.get_provider_info("nonexistent") is None


class TestWorkbenchProviderRegistrySwitch:
    """Provider 切换测试（关键 Runtime provider switching validation）。"""

    def test_switch_provider_success(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[
                ProviderInfo(provider_id="echo", type_name="echo"),
                ProviderInfo(provider_id="openai", type_name="openai"),
            ],
            active="echo",
        )
        registry = WorkbenchProviderRegistry(backend)
        result = registry.switch_provider("openai")

        assert result.success is True
        assert result.previous_id == "echo"
        assert result.new_id == "openai"
        assert registry.active_provider_id == "openai"

    def test_switch_provider_not_registered(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[ProviderInfo(provider_id="echo", type_name="echo")],
            active="echo",
        )
        registry = WorkbenchProviderRegistry(backend)
        result = registry.switch_provider("nonexistent")

        assert result.success is False
        assert result.previous_id == "echo"
        assert result.new_id == "echo"  # 保持原状
        assert "not registered" in result.error

    def test_switch_provider_backend_failure(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[
                ProviderInfo(provider_id="echo", type_name="echo"),
                ProviderInfo(provider_id="openai", type_name="openai"),
            ],
            active="echo",
            switch_should_fail=True,
        )
        registry = WorkbenchProviderRegistry(backend)
        result = registry.switch_provider("openai")

        assert result.success is False
        assert "refused" in result.error
        assert registry.active_provider_id == "echo"  # 未变更

    def test_refresh_updates_active(self) -> None:
        backend = MockRuntimeProviderBackend(
            providers=[ProviderInfo(provider_id="echo", type_name="echo")],
            active="echo",
        )
        registry = WorkbenchProviderRegistry(backend)
        # 模拟 Runtime 端切换（绕过 Workbench 层）
        backend._active = "deepseek"
        # registry 尚未刷新
        assert registry.active_provider_id == "echo"
        registry.refresh()
        assert registry.active_provider_id == "deepseek"