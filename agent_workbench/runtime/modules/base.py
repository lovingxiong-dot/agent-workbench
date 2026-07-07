"""agent_workbench/runtime/modules/base.py — RuntimeModule 基类。

所有 Agent Workbench V6 模块都继承此类，统一生命周期：
- initialize：模块初始化，可获取 Runtime 或其他模块引用。
- apply_config：配置变更时热更新。
- dispose：资源释放。
- to_form：生成 UI 表单结构（描述哪些字段可编辑）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

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
    def to_form(self) -> Dict[str, Any]:
        """返回该模块的 UI 表单描述。"""
        ...
