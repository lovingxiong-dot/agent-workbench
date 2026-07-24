"""presentation/services/model_module_backend.py — ModelModule → RuntimeProviderBackend Adapter。

v6.10.0-alpha Provider Integration Foundation。

职责：
  - 将 Runtime ModelModule（frozen）适配为 RuntimeProviderBackend Protocol
  - 让 WorkbenchProviderRegistry 不直接依赖 ModelModule
  - 隔离 Runtime 实现变化对 v6-agent 层的影响

边界：
  - 不修改 ModelModule（Runtime frozen）
  - 仅作数据转换层
"""
from __future__ import annotations

from typing import List, Optional

from agent_workbench.presentation.services.provider_registry import (
    ProviderInfo,
    RuntimeProviderBackend,
)


class ModelModuleBackend:
    """ModelModule → RuntimeProviderBackend Adapter。

    实现 RuntimeProviderBackend Protocol 接口。
    将 ModelModule.list_providers() / switch_provider() 等转换为 ProviderInfo。
    """

    def __init__(self, model_module) -> None:
        self._module = model_module

    def list_provider_names(self) -> List[str]:
        """列出所有已注册 Provider 名称。"""
        return [p["name"] for p in self._module.list_providers()]

    def list_provider_infos(self) -> List[ProviderInfo]:
        """列出所有 ProviderInfo。"""
        active_name = self._module.get_current_provider_name()
        result: List[ProviderInfo] = []
        for provider_dict in self._module.list_providers():
            provider_id = provider_dict.get("name", "")
            models = self._get_models_for(provider_id)
            result.append(
                ProviderInfo(
                    provider_id=provider_id,
                    type_name=provider_dict.get("type", "unknown"),
                    available_models=models,
                    is_active=(provider_id == active_name),
                    config=provider_dict,
                )
            )
        return result

    def get_active_provider_name(self) -> Optional[str]:
        """获取当前激活 Provider。"""
        return self._module.get_current_provider_name()

    def switch_provider(self, provider_name: str) -> bool:
        """切换 Provider。"""
        return self._module.switch_provider(provider_name)

    def _get_models_for(self, provider_name: str) -> List[str]:
        """获取 Provider 可用模型列表。

        ModelModule.list_models() 返回当前 Provider 的模型。
        这里简化：返回当前 active 模型列表（仅作占位）。
        未来可扩展为每个 Provider 的独立模型列表。
        """
        if provider_name == self._module.get_current_provider_name():
            return self._module.list_models()
        return []