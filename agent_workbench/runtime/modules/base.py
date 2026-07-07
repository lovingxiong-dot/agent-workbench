"""agent_workbench/runtime/modules/base.py — RuntimeModule 基类。

所有 Agent Workbench V6 模块都继承此类，统一生命周期：
- initialize：模块初始化，可获取 Runtime 引用。
- apply_config：配置变更时热更新。
- dispose：资源释放。
- metadata：返回 Capability Metadata（模块唯一对外暴露的能力描述）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from agent_workbench.runtime.metadata import ModuleMetadata

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime
    from agent_workbench.runtime.config_store import ConfigStore


class BaseRuntimeModule(ABC):
    """Agent Workbench 模块基类。"""

    @property
    @abstractmethod
    def namespace(self) -> str:
        """模块对应的配置 namespace，例如 'model'、'prompt'。"""
        ...

    def initialize(self, runtime: "AgentRuntime") -> None:
        """模块初始化。子类可重写以获取 Runtime 引用。"""
        pass

    @abstractmethod
    def apply_config(self, store: "ConfigStore") -> None:
        """根据 ConfigStore 当前配置热更新模块状态。"""
        ...

    def dispose(self) -> None:
        """释放模块资源。子类可重写。"""
        pass

    @abstractmethod
    def metadata(self) -> ModuleMetadata:
        """返回模块 Capability Metadata（不含 UI 概念）。

        UI 通过 MetadataAdapter 将 Metadata 翻译为 PresentationModel。
        """
        ...
