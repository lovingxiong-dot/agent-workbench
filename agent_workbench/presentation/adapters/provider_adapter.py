"""presentation/adapters/provider_adapter.py — Provider Adapter。

v6.10.0-alpha Provider Integration Foundation。

设计原则：
  ✓ 仅转换 Foundation Protocol 数据 → UI ViewModel
  ✓ 零 Runtime Implementation import（仅引用 metadata 协议 dataclass）
  ✓ Adapter 是 UI 层数据流的唯一翻译点

边界：
  - Foundation Protocol ProviderEndpoint（frozen）→ ProviderViewModel
  - 不修改任何 frozen 路径
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.view_models.provider import (
    ProviderListViewModel,
    ProviderViewModel,
)


class ProviderAdapter:
    """Provider Foundation Protocol → ViewModel Adapter。

    职责：
      - to_view_model: ProviderEndpoint → ProviderViewModel
      - to_list_view_model: Iterable[ProviderEndpoint] → ProviderListViewModel
      - derive_status: 推导 UI 展示状态
      - derive_protocol: 推导协议字符串
    """

    def to_view_model(self, endpoint: ProviderEndpoint) -> ProviderViewModel:
        """将 ProviderEndpoint 转换为 ProviderViewModel。

        Args:
            endpoint: Foundation Protocol ProviderEndpoint。

        Returns:
            ProviderViewModel 适用于 UI 渲染。
        """
        return ProviderViewModel(
            provider_id=endpoint.provider_id,
            name=endpoint.provider_id.capitalize(),
            protocol=self._derive_protocol(endpoint.protocol),
            status=self._derive_status(endpoint),
            models=list(endpoint.models),
            base_url=endpoint.base_url,
            has_api_key=bool(endpoint.api_key),
            metadata={
                "enabled": str(endpoint.enabled),
            },
        )

    def to_list_view_model(
        self,
        endpoints: Iterable[ProviderEndpoint],
        active_provider_id: Optional[str] = None,
    ) -> ProviderListViewModel:
        """将 ProviderEndpoint 列表转换为 ProviderListViewModel。

        Args:
            endpoints: Foundation Protocol ProviderEndpoint 列表。
            active_provider_id: 当前激活的 Provider ID（用于 UI 标识）。

        Returns:
            ProviderListViewModel 适用于列表渲染。
        """
        view_models = [self.to_view_model(ep) for ep in endpoints]
        return ProviderListViewModel(
            providers=view_models,
            active_provider_id=active_provider_id,
        )

    def _derive_status(self, endpoint: ProviderEndpoint) -> str:
        """推导 Provider UI 展示状态。

        规则：
          - enabled=False        → "disabled"
          - 缺 api_key (除 echo) → "needs_config"
          - 缺 models            → "no_models"
          - 否则                 → "active"
        """
        if not endpoint.enabled:
            return "disabled"
        # echo Provider 不需要 API Key
        if endpoint.protocol == ProviderProtocol.ECHO and not endpoint.api_key:
            return "active"
        if not endpoint.api_key:
            return "needs_config"
        if not endpoint.models:
            return "no_models"
        return "active"

    def _derive_protocol(self, protocol: ProviderProtocol) -> str:
        """将 Foundation Protocol enum 转换为字符串标识。"""
        if isinstance(protocol, ProviderProtocol):
            return protocol.value
        return str(protocol)