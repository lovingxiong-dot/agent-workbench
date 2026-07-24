"""presentation/services/provider_registry.py — Workbench Provider Registry。

v6.10.0-alpha Provider Integration Foundation。

设计原则：
  ✓ v6-agent 层聚合层，委托 Runtime ProviderRegistry
  ✓ 不修改 Runtime Kernel（ProviderRegistry 保持 frozen）
  ✓ 通过 Protocol 接口（RuntimeProviderBackend Protocol）解耦
  ✓ UI 配置可零代码修改注册新 Provider

边界（关键）：
  - WorkbenchProviderRegistry 在 v6-agent 层
  - 它使用 Protocol 接口从 Runtime 拉取 Provider 元数据
  - 它不修改 Runtime ProviderRegistry
  - 它不修改 Capability Runtime Contract
  - 它不修改 Decision Layer ABI
  - 它不修改 Event Protocol

切换语义：
  - switch_provider() 仅修改 v6-agent 层 active 状态
  - 通过 ProviderAdapter 通知 UI
  - Runtime 实际切换由 RuntimeProviderBackend 提供
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol


@dataclass
class ProviderInfo:
    """Provider 运行时信息（v6-agent 层聚合 view）。

    与 Foundation Protocol ProviderEndpoint 区分：
      - ProviderEndpoint: 配置契约（frozen）
      - ProviderInfo: v6-agent 层聚合（runtime status + config + active）
    """

    provider_id: str
    type_name: str
    available_models: List[str] = field(default_factory=list)
    is_active: bool = False
    config: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.available_models is None:
            self.available_models = []
        if self.config is None:
            self.config = {}


class RuntimeProviderBackend(Protocol):
    """Runtime Provider Backend Protocol（v6-agent 层定义）。

    Runtime 层不需要实现这个 Protocol，但 Runtime ProviderRegistry 自然满足此 Protocol。
    v6-agent 层仅依赖此 Protocol，不直接 import Runtime ProviderRegistry。
    """

    def list_provider_names(self) -> List[str]:
        """列出所有已注册 Provider 的名称（有序）。"""
        ...

    def list_provider_infos(self) -> List[ProviderInfo]:
        """列出所有 Provider 运行时信息。"""
        ...

    def get_active_provider_name(self) -> Optional[str]:
        """获取当前激活 Provider 名称。"""
        ...

    def switch_provider(self, provider_name: str) -> bool:
        """切换 Provider。返回是否成功。"""
        ...


@dataclass
class SwitchResult:
    """Provider 切换结果（v6-agent 层 view）。"""

    success: bool
    previous_id: Optional[str] = None
    new_id: Optional[str] = None
    error: str = ""


class WorkbenchProviderRegistry:
    """Workbench Provider Registry（v6-agent 层）。

    职责：
      - 聚合 Runtime Provider Backend 的状态
      - 维护 active provider 视图
      - 提供零代码扩展点（通过 RuntimeProviderBackend Protocol）

    边界：
      - 不修改 Runtime ProviderRegistry
      - 不直接依赖 Runtime 类（仅依赖 Protocol）
      - 不发起对 Runtime 内核的侵入
    """

    def __init__(self, backend: RuntimeProviderBackend) -> None:
        self._backend = backend
        self._active_provider_id: Optional[str] = backend.get_active_provider_name()

    @property
    def active_provider_id(self) -> Optional[str]:
        return self._active_provider_id

    def list_providers(self) -> List[ProviderInfo]:
        """列出所有 Provider 运行时信息（来自 Runtime）。"""
        return self._backend.list_provider_infos()

    def list_provider_names(self) -> List[str]:
        """列出所有 Provider 名称。"""
        return self._backend.list_provider_names()

    def get_provider_info(self, provider_id: str) -> Optional[ProviderInfo]:
        """获取指定 Provider 的运行时信息。"""
        for info in self._backend.list_provider_infos():
            if info.provider_id == provider_id:
                return info
        return None

    def switch_provider(self, provider_id: str) -> SwitchResult:
        """切换 Provider。

        Args:
            provider_id: 目标 Provider 名称。

        Returns:
            SwitchResult 包含成功状态、前后值与错误信息。
        """
        previous = self._active_provider_id
        if provider_id not in self._backend.list_provider_names():
            return SwitchResult(
                success=False,
                previous_id=previous,
                new_id=previous,
                error=f"Provider '{provider_id}' is not registered.",
            )
        ok = self._backend.switch_provider(provider_id)
        if not ok:
            return SwitchResult(
                success=False,
                previous_id=previous,
                new_id=previous,
                error=f"Backend refused to switch to '{provider_id}'.",
            )
        self._active_provider_id = provider_id
        return SwitchResult(
            success=True,
            previous_id=previous,
            new_id=provider_id,
        )

    def refresh(self) -> None:
        """从 Runtime 重新拉取 active provider 状态。"""
        self._active_provider_id = self._backend.get_active_provider_name()