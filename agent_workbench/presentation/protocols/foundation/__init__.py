"""presentation/protocols/foundation/ — Foundation Contract v1.0。

Phase 1: Foundation Contract Freeze。
两个产品（Workbench v6 + Agent Manager OS）共同继承的祖先接口契约。

约束：
  ✓ 纯 Python 数据模型（dataclass + Protocol）
  ✓ 零 Runtime Implementation import
  ✓ 零 PySide6 import
  ✗ 不引用 v6/runtime/*.py
  ✗ 不引用 v6/ui/*
  ✗ 不引用 WorkbenchController / V6UIApplication

四个契约：
  - runtime.py     AgentRuntime Protocol
  - event.py       EventEnvelope + EventBus Protocol
  - data.py        AgentIdentity / AgentSession / WorkflowState / CapabilityDefinition
  - gateway.py     Gateway Protocol
"""
from agent_workbench.presentation.protocols.foundation.data import (
    AgentIdentity,
    AgentMessage,
    AgentSession,
    AgentType,
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityParameter,
    WorkflowPhase,
    WorkflowState,
    WorkflowStep,
)
from agent_workbench.presentation.protocols.foundation.event import (
    EventBus,
    EventChannel,
    EventEnvelope,
)
from agent_workbench.presentation.protocols.foundation.gateway import (
    Gateway,
    GatewayMode,
    GatewayRequest,
    GatewayResponse,
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.protocols.foundation.runtime import (
    AgentRuntime,
    AgentRuntimeInfo,
    ExecutionHandle,
    RuntimeLifecycleState,
)

__all__ = [
    # Runtime
    "AgentRuntime",
    "AgentRuntimeInfo",
    "ExecutionHandle",
    "RuntimeLifecycleState",
    # Event
    "EventBus",
    "EventChannel",
    "EventEnvelope",
    # Data - Identity
    "AgentIdentity",
    "AgentType",
    # Data - Session
    "AgentSession",
    "AgentMessage",
    # Data - Workflow
    "WorkflowState",
    "WorkflowStep",
    "WorkflowPhase",
    # Data - Capability
    "CapabilityDefinition",
    "CapabilityParameter",
    "CapabilityCategory",
    # Gateway
    "Gateway",
    "GatewayMode",
    "GatewayRequest",
    "GatewayResponse",
    "ProviderEndpoint",
    "ProviderProtocol",
]