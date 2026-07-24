"""presentation/view_models/provider.py — Provider View Model。

v6.10.0-alpha Provider Integration Foundation。

设计原则：
  ✓ 纯数据，无 Runtime import
  ✓ 零 UI import
  ✓ 与 Foundation Protocol ProviderEndpoint 互补（UI 视图专用）

边界：
  - Foundation Protocol ProviderEndpoint（gateway.py）保持 frozen
  - ProviderViewModel 仅在 v6-agent 层定义
  - Runtime 层 ProviderRegistry 不修改
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProviderViewModel:
    """Provider UI 视图模型。

    用于 Workbench UI 展示 Provider 列表/卡片。
    数据来源：
      - Foundation Protocol: ProviderEndpoint（配置契约）
      - Runtime: ProviderRegistry.metadata()（运行时元数据）

    字段：
      - provider_id: Provider 唯一标识（与 ProviderEndpoint.provider_id 对齐）
      - name: 人类可读名称
      - protocol: ProviderProtocol 字符串值（openai/anthropic/...）
      - status: UI 展示状态（active / disabled / error / unknown）
      - models: 模型列表
      - base_url: API 端点
      - has_api_key: 是否配置了 API Key（UI 不暴露明文）
      - metadata: 扩展展示属性
    """

    provider_id: str
    name: str
    protocol: str = "custom"
    status: str = "unknown"
    models: List[str] = field(default_factory=list)
    base_url: str = ""
    has_api_key: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.models is None:
            self.models = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProviderListViewModel:
    """Provider 列表视图模型。"""

    providers: List[ProviderViewModel] = field(default_factory=list)
    active_provider_id: Optional[str] = None
    total_count: int = 0

    def __post_init__(self) -> None:
        if self.providers is None:
            self.providers = []
        self.total_count = len(self.providers)

    def get_active(self) -> Optional[ProviderViewModel]:
        if self.active_provider_id is None:
            return None
        for provider in self.providers:
            if provider.provider_id == self.active_provider_id:
                return provider
        return None