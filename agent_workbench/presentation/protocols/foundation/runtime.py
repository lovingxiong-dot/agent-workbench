"""presentation/protocols/foundation/runtime.py — AgentRuntime Contract。

定义两个产品（Workbench v6 + Agent Manager OS）共同继承的 Agent Runtime 接口契约。

Phase 1: Foundation Contract Freeze — 仅定义接口，不实现。

约束：
  ✓ 仅 typing.Protocol + dataclass
  ✗ 零 Runtime Implementation import
  ✗ 零 UI import
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Protocol

from agent_workbench.presentation.protocols.foundation.data import (
    AgentIdentity,
    AgentSession,
    CapabilityDefinition,
    WorkflowState,
)
from agent_workbench.presentation.protocols.foundation.event import EventEnvelope


class RuntimeLifecycleState(str, Enum):
    """Runtime 生命周期状态。"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ExecutionHandle:
    """执行句柄：提交任务后返回的引用。

    字段：
    - task_id: 任务标识。
    - runtime_id: 任务所属 Runtime 实例标识。
    - session_id: 关联的会话标识。
    """
    task_id: str
    runtime_id: str
    session_id: str


@dataclass
class AgentRuntimeInfo:
    """Runtime 实例元信息。"""
    runtime_id: str
    version: str
    capabilities: List[str] = None  # type: ignore
    state: RuntimeLifecycleState = RuntimeLifecycleState.INITIALIZING
    started_at: float = 0.0

    def __post_init__(self) -> None:
        if self.capabilities is None:
            self.capabilities = []


class AgentRuntime(Protocol):
    """Agent Runtime Contract — Workbench v6 + Agent Manager OS 共同继承。

    约束：
      - 任何 Runtime 实现都必须满足此协议。
      - Workbench v6 与 Agent Manager OS 都消费此协议，不复制实现。

    关键操作：
      - start / stop: 生命周期管理。
      - execute: 提交单个 Agent 调用并返回结果。
      - pause / resume: 暂停 / 恢复某个 ExecutionHandle。
      - terminate: 取消某个 ExecutionHandle。
      - state / info: 查询状态与元信息。
    """

    def start(self) -> None:
        """启动 Runtime。"""
        ...

    def stop(self) -> None:
        """停止 Runtime。"""
        ...

    @property
    def state(self) -> RuntimeLifecycleState:
        """当前 Runtime 生命周期状态。"""
        ...

    @property
    def info(self) -> AgentRuntimeInfo:
        """Runtime 实例元信息。"""
        ...

    def execute(
        self,
        session: AgentSession,
        identity: AgentIdentity,
        input: Dict[str, Any],
    ) -> ExecutionHandle:
        """提交单个 Agent 调用并返回执行句柄。

        参数：
        - session: Agent 会话上下文。
        - identity: Agent 标识。
        - input: 输入数据。

        返回：
        - ExecutionHandle: 后续查询/暂停/恢复/取消的引用。
        """
        ...

    def pause(self, handle: ExecutionHandle) -> None:
        """暂停某个 ExecutionHandle 对应的执行。"""
        ...

    def resume(self, handle: ExecutionHandle) -> None:
        """恢复某个 ExecutionHandle 对应的执行。"""
        ...

    def terminate(self, handle: ExecutionHandle) -> None:
        """取消某个 ExecutionHandle 对应的执行。"""
        ...

    def workflow_state(self, handle: ExecutionHandle) -> WorkflowState:
        """查询 ExecutionHandle 对应的 Workflow 状态。"""
        ...

    def list_capabilities(self) -> List[CapabilityDefinition]:
        """列出 Runtime 支持的所有 Capability。"""
        ...

    def on_event(self, event: EventEnvelope) -> None:
        """事件回调入口（Runtime 内部事件订阅者）。"""
        ...