"""agent_workbench/runtime/module_registry.py — RuntimeModule 注册表。

职责：
- 注册 10 个 RuntimeModule。
- 按 namespace 查找模块。
- 统一调用 initialize / apply_config / dispose。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from agent_workbench.runtime.modules.base import BaseRuntimeModule

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime
    from agent_workbench.runtime.config_store import ConfigStore


class ModuleRegistry:
    """Agent Workbench 模块注册表。"""

    def __init__(self) -> None:
        self._modules: Dict[str, BaseRuntimeModule] = {}
        self._order: List[str] = []

    def register(self, module: BaseRuntimeModule) -> None:
        """注册一个模块。"""
        namespace = module.namespace
        self._modules[namespace] = module
        if namespace not in self._order:
            self._order.append(namespace)

    def get(self, namespace: str) -> BaseRuntimeModule | None:
        """按 namespace 获取模块。"""
        return self._modules.get(namespace)

    def namespaces(self) -> List[str]:
        """返回已注册模块的 namespace 列表（按注册顺序）。"""
        return list(self._order)

    def modules(self) -> List[BaseRuntimeModule]:
        """返回已注册模块列表（按注册顺序）。"""
        return [self._modules[name] for name in self._order]

    def initialize_all(self, runtime: "AgentRuntime") -> None:
        """初始化所有模块。"""
        for module in self.modules():
            module.initialize(runtime)

    def apply_all(self, store: "ConfigStore") -> None:
        """对所有模块应用当前配置。"""
        for module in self.modules():
            module.apply_config(store)

    def dispose_all(self) -> None:
        """释放所有模块资源。"""
        for module in self.modules():
            module.dispose()
