"""presentation/services/provider_service.py — Provider Service Controller。

v6.10.0-alpha Provider Integration Foundation。

职责：
  - 在 v6-agent 层聚合 Provider 操作
  - 提供给 UI 的统一入口（list / add / remove / switch）
  - 配置驱动：通过 ConfigStore 操作 provider 配置（不修改源码）
  - 委托 WorkbenchProviderRegistry + WorkbenchController

边界：
  - 不修改 Runtime Kernel
  - 不修改 Capability Runtime Contract
  - 不修改 Decision Layer ABI
  - 不修改 Event Protocol
  - 不修改 Foundation Protocol
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from agent_workbench.presentation.adapters.provider_adapter import ProviderAdapter
from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.services.provider_registry import (
    ProviderInfo,
    RuntimeProviderBackend,
    SwitchResult,
    WorkbenchProviderRegistry,
)
from agent_workbench.presentation.services.provider_validator import (
    ProviderValidator,
    ValidationResult,
)
from agent_workbench.presentation.view_models.provider import (
    ProviderListViewModel,
    ProviderViewModel,
)


@dataclass
class AddProviderResult:
    """添加 Provider 结果。"""

    success: bool
    provider_id: str = ""
    validation: Optional[ValidationResult] = None
    error: str = ""


@dataclass
class RemoveProviderResult:
    """移除 Provider 结果。"""

    success: bool
    provider_id: str = ""
    error: str = ""


@dataclass
class ConfigStoreProtocol:
    """ConfigStore 接口契约（运行时配置存储）。

    WorkbenchProviderConfigBackend 必须实现此 Protocol。
    实际 ConfigStore 由 WorkbenchController 提供。
    """

    def get(self, key: str, default=None):
        """获取配置值。"""
        ...

    def set(self, key: str, value) -> None:
        """设置配置值。"""
        ...

    def add(self, key: str, value) -> None:
        """追加配置项到列表。"""
        ...


class WorkbenchProviderConfigBackend:
    """Provider 配置持久化后端（委托 ConfigStore）。

    Configuration-Driven Principle (P5):
      - UI 修改配置 → ConfigStore 持久化
      - ConfigStore changed signal → Runtime 热更新
      - 无需修改源码
    """

    _KEY = "model.providers"

    def __init__(self, config_store) -> None:
        self._store = config_store

    def list_provider_configs(self) -> list[dict]:
        """列出所有 Provider 配置字典（来源 ConfigStore）。"""
        return self._store.get(self._KEY, []) or []

    def upsert_provider_config(self, endpoint: ProviderEndpoint) -> bool:
        """新增或更新 Provider 配置。"""
        providers = self.list_provider_configs()
        config = self._endpoint_to_config(endpoint)
        existing_idx = None
        for i, p in enumerate(providers):
            if p.get("name") == endpoint.provider_id:
                existing_idx = i
                break
        if existing_idx is not None:
            providers[existing_idx] = config
        else:
            providers.append(config)
        self._store.set(self._KEY, providers)
        return True

    def remove_provider_config(self, provider_id: str) -> bool:
        """删除 Provider 配置。"""
        providers = self.list_provider_configs()
        new_providers = [p for p in providers if p.get("name") != provider_id]
        if len(new_providers) == len(providers):
            return False
        self._store.set(self._KEY, new_providers)
        return True

    def set_default_provider(self, provider_id: str) -> bool:
        """设置默认 Provider。"""
        self._store.set("model.default_provider", provider_id)
        return True

    def _endpoint_to_config(self, endpoint: ProviderEndpoint) -> dict:
        """ProviderEndpoint → ConfigStore dict。"""
        return {
            "name": endpoint.provider_id,
            "type": endpoint.protocol.value if isinstance(endpoint.protocol, ProviderProtocol) else str(endpoint.protocol),
            "enabled": endpoint.enabled,
            "models": list(endpoint.models),
            "model": endpoint.models[0] if endpoint.models else "",
            "api_key": endpoint.api_key,
            "base_url": endpoint.base_url,
        }


class ProviderServiceController:
    """Provider Service Controller（v6-agent 层）。

    职责：
      - 协调 WorkbenchProviderRegistry（运行时聚合）
      - 协调 WorkbenchProviderConfigBackend（配置持久化）
      - 暴露 ViewModel 给 UI
      - 验证 Provider 配置
    """

    def __init__(
        self,
        provider_registry: WorkbenchProviderRegistry,
        config_backend: WorkbenchProviderConfigBackend,
        adapter: Optional[ProviderAdapter] = None,
        validator: Optional[ProviderValidator] = None,
    ) -> None:
        self._registry = provider_registry
        self._config = config_backend
        self._adapter = adapter or ProviderAdapter()
        self._validator = validator or ProviderValidator()

    # ─── List ────────────────────────────────────────────────

    def list_view_model(self) -> ProviderListViewModel:
        """获取所有 Provider 的 ViewModel（供 UI 列表展示）。"""
        configs = self._config.list_provider_configs()
        endpoints = [self._config_to_endpoint(c) for c in configs]
        active_id = self._registry.active_provider_id
        return self._adapter.to_list_view_model(endpoints, active_id)

    def get_view_model(self, provider_id: str) -> Optional[ProviderViewModel]:
        """获取单个 Provider ViewModel。"""
        for endpoint in self._config_to_endpoints():
            if endpoint.provider_id == provider_id:
                vm = self._adapter.to_view_model(endpoint)
                if self._registry.active_provider_id == provider_id:
                    vm.status = "active"
                return vm
        return None

    # ─── Add ─────────────────────────────────────────────────

    def add_provider(self, endpoint: ProviderEndpoint) -> AddProviderResult:
        """添加 Provider 配置。

        Steps:
          1. 验证配置
          2. 持久化到 ConfigStore（Runtime 自动热更新）
        """
        validation = self._validator.validate(endpoint)
        if not validation.valid:
            return AddProviderResult(
                success=False,
                provider_id=endpoint.provider_id,
                validation=validation,
                error="; ".join(i.message for i in validation.errors),
            )
        self._config.upsert_provider_config(endpoint)
        return AddProviderResult(
            success=True,
            provider_id=endpoint.provider_id,
            validation=validation,
        )

    # ─── Remove ──────────────────────────────────────────────

    def remove_provider(self, provider_id: str) -> RemoveProviderResult:
        """删除 Provider 配置。"""
        if provider_id == self._registry.active_provider_id:
            return RemoveProviderResult(
                success=False,
                provider_id=provider_id,
                error="不能删除当前激活的 Provider。",
            )
        ok = self._config.remove_provider_config(provider_id)
        if not ok:
            return RemoveProviderResult(
                success=False,
                provider_id=provider_id,
                error=f"Provider '{provider_id}' 不存在。",
            )
        return RemoveProviderResult(success=True, provider_id=provider_id)

    # ─── Switch ──────────────────────────────────────────────

    def switch_provider(self, provider_id: str) -> SwitchResult:
        """切换激活 Provider。

        Steps:
          1. 通过 Runtime ProviderRegistry 切换
          2. 同步 ConfigStore 的 default_provider
        """
        result = self._registry.switch_provider(provider_id)
        if result.success:
            self._config.set_default_provider(provider_id)
        return result

    # ─── Refresh ─────────────────────────────────────────────

    def refresh(self) -> None:
        """从 Runtime 刷新状态。"""
        self._registry.refresh()

    # ─── Helpers ─────────────────────────────────────────────

    def _config_to_endpoints(self) -> List[ProviderEndpoint]:
        """ConfigStore dicts → ProviderEndpoint list。"""
        return [self._config_to_endpoint(c) for c in self._config.list_provider_configs()]

    @staticmethod
    def _config_to_endpoint(config: dict) -> ProviderEndpoint:
        """ConfigStore dict → ProviderEndpoint。"""
        protocol_str = config.get("type", "custom")
        try:
            protocol = ProviderProtocol(protocol_str)
        except ValueError:
            protocol = ProviderProtocol.CUSTOM
        return ProviderEndpoint(
            provider_id=config.get("name", ""),
            protocol=protocol,
            base_url=config.get("base_url", ""),
            api_key=config.get("api_key", ""),
            models=list(config.get("models", []) or [config.get("model", "")]),
            enabled=bool(config.get("enabled", True)),
        )