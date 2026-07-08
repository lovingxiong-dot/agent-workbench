"""agent_workbench/runtime/capability — Capability Runtime 契约层。

本包承载 v6.9.3-alpha 引入的 Capability 一级运行时对象，以及 v6.9.6-alpha 冻结的 Runtime Contract：
- model: CapabilityDefinition / CapabilityCategory / CapabilityMode / CapabilityPersona / CapabilityIntent / CapabilityMatch
- context: CapabilityContext / WorkspaceContext / AttachmentContext / SelectionContext / ExecutionContext / CapabilityContextBuilder
- state: CapabilityState / CapabilityExecutionState
- chain: CapabilityStep / CapabilityChain
- graph: CapabilityNode / CapabilityRegistry（运行时索引扩展）

设计约束：
- CapabilityDefinition 纯数据，禁止携带 Runtime 状态。
- CapabilityContext / CapabilityState 挂靠在 Registry 索引中，不写入 Task 五字段。
"""
from __future__ import annotations

from agent_workbench.runtime.capability.chain import CapabilityChain, CapabilityStep
from agent_workbench.runtime.capability.context import (
    AttachmentContext,
    CapabilityContext,
    CapabilityContextBuilder,
    DefaultCapabilityContextBuilder,
    ExecutionContext,
    SelectionContext,
    WorkspaceContext,
)
from agent_workbench.runtime.capability.graph import CapabilityRegistry
from agent_workbench.runtime.capability.model import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityIntent,
    CapabilityMatch,
    CapabilityMode,
    CapabilityPersona,
)
from agent_workbench.runtime.capability.state import CapabilityExecutionState, CapabilityState

__all__ = [
    "AttachmentContext",
    "CapabilityCategory",
    "CapabilityChain",
    "CapabilityContext",
    "CapabilityContextBuilder",
    "CapabilityDefinition",
    "CapabilityExecutionState",
    "CapabilityIntent",
    "CapabilityMatch",
    "CapabilityMode",
    "CapabilityPersona",
    "CapabilityRegistry",
    "CapabilityState",
    "CapabilityStep",
    "DefaultCapabilityContextBuilder",
    "ExecutionContext",
    "SelectionContext",
    "WorkspaceContext",
]
