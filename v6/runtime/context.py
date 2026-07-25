"""v6/runtime/context.py — 单次任务运行时上下文。

设计来源：docs/v6/SPEC.md 第 4、8 节。

核心原则：
- RuntimeContext 是运行时唯一状态对象（Single Source of Truth）。
- RuntimeContext 保存 Runtime Facts，不拥有 Runtime Behavior / 业务能力。
- Engine/Service 产生 Facts，写入 RuntimeContext；Runtime 编排 Engine 执行顺序。
- Engine 之间零耦合，不直接彼此调用，只通过 RuntimeContext 共享状态。
- RuntimeContext 允许拥有数据管理能力（add_message / clone / snapshot / restore / freeze / reset / to_dict 等）。
- 禁止出现 ctx.call_llm() / ctx.execute_tool() / ctx.save_memory() / ctx.invoke_agent() / ctx.dispatch() 等业务方法。
- messages 元素为 ChatMessage，不再使用裸 dict。
"""
from __future__ import annotations

import copy
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v6.runtime.enums import ActivityState, LifecycleState, RuntimeState, lifecycle_to_runtime
from v6.runtime.execution_control import ExecutionControl
from v6.runtime.execution_metadata import ExecutionMetadata
from v6.runtime.metrics import RuntimeMetrics
from v6.runtime.result import RuntimeResult
from v6.runtime.trace import RuntimeTrace
from v6.runtime.types import ChatMessage


@dataclass
class RuntimeContext:
    """维护单次任务的运行时事实（Runtime Facts）。

    RuntimeContext 是 Runtime State Container（运行时状态容器），不是 Runtime Manager。
    字段可演进，Engine 不应假设字段集合固定。
    """

    task_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    group_user_id: Optional[str] = None

    # 执行状态
    phase: str = ""
    mode: str = ""
    model: str = ""
    provider: str = ""

    # 项目与记忆
    project_path: str = ""
    memory: Dict[str, Any] = field(default_factory=dict)

    # 消息、工具
    messages: List[ChatMessage] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    # Engine 执行请求载荷。EngineManager 在调度时写入，Engine.execute(ctx) 从 ctx.request 读取。
    request: Any = None

    # 统计信息（Statistics）与最终输出（Output）
    # 当前挂载在 Context 上，未来可平滑迁移到 RuntimeTask.metrics / RuntimeTask.result。
    metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)
    result: RuntimeResult = field(default_factory=RuntimeResult)

    # 执行历史（History），供调试、回放、审计
    trace: RuntimeTrace = field(default_factory=RuntimeTrace)

    # 通用元数据容器，Engine 可读写自己负责的字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: RuntimeState = RuntimeState.CREATED
    created_at: float = field(default_factory=time.time)

    # Phase 3.11-A: 双状态模型 + Execution Identity
    lifecycle: LifecycleState = LifecycleState.CREATED
    activity: ActivityState = ActivityState.IDLE
    execution: Optional[ExecutionMetadata] = None

    # Phase 3.11-C: 执行控制（聚合 CancellationToken 等控制令牌）
    control: ExecutionControl = field(default_factory=ExecutionControl)

    def __post_init__(self) -> None:
        self._lock = threading.RLock()

    @classmethod
    def new(
        cls,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> "RuntimeContext":
        """工厂方法：自动生成 task_id，保持 Runtime 生命周期可追踪性。

        业务代码应优先使用此方法，避免手动填写无意义的 task_id。
        """
        return cls(
            task_id=task_id or uuid.uuid4().hex,
            session_id=session_id,
            **kwargs,
        )

    def attach_execution(self, execution: "ExecutionMetadata") -> None:
        """v0.3: 统一 ExecutionMetadata 绑定入口。

        在 execution 创建后调用，确保 ctx.control 与 ctx.execution.control
        引用同一 ExecutionControl 实例（不变量：避免双 CancellationToken）。
        """
        with self._lock:
            self.execution = execution
            # 同步 control 引用（保证 is 同一对象）
            self.control = execution.control

    # ─────────────────────────────────────────────────────────
    # 数据管理方法（允许）
    # ─────────────────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        """追加一条 ChatMessage 到上下文。"""
        with self._lock:
            self.messages.append(ChatMessage(role=role, content=content))

    def set_status(self, status: RuntimeState | str) -> None:
        """线程安全地更新任务状态；接受枚举或字符串以保持兼容性。

        同时同步 lifecycle 字段（向后兼容映射）。
        """
        with self._lock:
            if isinstance(status, RuntimeState):
                self.status = status
            else:
                self.status = RuntimeState(status)
            # 同步 lifecycle（向后兼容）
            self._sync_status_to_lifecycle()

    def set_lifecycle(self, lifecycle: LifecycleState, activity: ActivityState | None = None) -> None:
        """Phase 3.11-A: 线程安全地更新双状态模型。

        同时同步旧 status 字段（向后兼容）。
        """
        with self._lock:
            self.lifecycle = lifecycle
            if activity is not None:
                self.activity = activity
            # 同步旧 status（向后兼容）
            self.status = lifecycle_to_runtime(lifecycle)

    def _sync_status_to_lifecycle(self) -> None:
        """将旧 status 同步到新 lifecycle 字段（向后兼容）。"""
        _status_to_lifecycle: dict[RuntimeState, LifecycleState] = {
            RuntimeState.CREATED: LifecycleState.CREATED,
            RuntimeState.QUEUED: LifecycleState.QUEUED,
            RuntimeState.PLANNING: LifecycleState.PLANNING,
            RuntimeState.EXECUTING: LifecycleState.EXECUTING,
            RuntimeState.RUNNING: LifecycleState.EXECUTING,
            RuntimeState.COMPLETED: LifecycleState.COMPLETED,
            RuntimeState.FAILED: LifecycleState.FAILED,
            RuntimeState.CANCELLED: LifecycleState.CANCELLED,
        }
        self.lifecycle = _status_to_lifecycle.get(self.status, LifecycleState.CREATED)

    def snapshot(self) -> Dict[str, Any]:
        """返回当前状态的深拷贝快照（用于 Checkpoint / Replay / Rollback）。"""
        with self._lock:
            return self._make_snapshot()

    freeze = snapshot  # 别名：强调不可变快照语义

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """从快照恢复状态（Rollback / Replay 基础）。"""
        with self._lock:
            self.task_id = snapshot.get("task_id", self.task_id)
            self.session_id = snapshot.get("session_id", self.session_id)
            self.conversation_id = snapshot.get("conversation_id", self.conversation_id)
            self.group_user_id = snapshot.get("group_user_id", self.group_user_id)
            self.phase = snapshot.get("phase", "")
            self.mode = snapshot.get("mode", "")
            self.model = snapshot.get("model", "")
            self.provider = snapshot.get("provider", "")
            self.project_path = snapshot.get("project_path", "")
            self.memory = copy.deepcopy(snapshot.get("memory", {}))
            self.tool_calls = copy.deepcopy(snapshot.get("tool_calls", []))
            self.request = copy.deepcopy(snapshot.get("request"))
            self.metrics = self._restore_metrics(snapshot.get("metrics"))
            self.result = self._restore_result(snapshot.get("result"))
            self.metadata = copy.deepcopy(snapshot.get("metadata", {}))
            self.status = self._restore_state(snapshot.get("status", RuntimeState.CREATED))
            self.created_at = snapshot.get("created_at", time.time())
            # Phase 3.11-A: 恢复双状态模型
            self.lifecycle = self._restore_lifecycle(snapshot.get("lifecycle", "created"))
            self.activity = self._restore_activity(snapshot.get("activity", "idle"))
            self.execution = self._restore_execution(snapshot.get("execution"))
            # Phase 3.11-C: 恢复控制状态
            self.control = self._restore_control(snapshot.get("control"))
            # v0.3: 恢复 ABI 不变量（control 与 execution.control 同一对象）
            if self.execution is not None:
                self.control = self.execution.control
            # trace 恢复：若快照含 steps 则重建 RuntimeTrace，否则保留当前实例
            raw_trace = snapshot.get("trace")
            if isinstance(raw_trace, dict) and "steps" in raw_trace:
                self.trace = RuntimeTrace()
                for s in raw_trace["steps"]:
                    self.trace.add(
                        node=s.get("node", ""),
                        action=s.get("action", ""),
                        phase=s.get("phase", ""),
                        payload=s.get("payload", {}),
                    )
            raw_messages = snapshot.get("messages", [])
            self.messages = [
                ChatMessage(**copy.deepcopy(m)) if isinstance(m, dict) else copy.deepcopy(m)
                for m in raw_messages
            ]

    def reset(self) -> None:
        """重置为初始空状态（保留 task_id 等标识）。"""
        with self._lock:
            self.phase = ""
            self.mode = ""
            self.model = ""
            self.provider = ""
            self.project_path = ""
            self.memory.clear()
            self.messages.clear()
            self.tool_calls.clear()
            self.request = None
            self.metrics.reset()
            self.result.reset()
            self.trace.clear()
            self.metadata.clear()
            self.status = RuntimeState.CREATED
            self.lifecycle = LifecycleState.CREATED
            self.activity = ActivityState.IDLE
            self.execution = None
            self.control = ExecutionControl()

    def clone(self) -> "RuntimeContext":
        """深拷贝自身，生成独立副本。"""
        with self._lock:
            # v0.3: 手动 deep-copy ExecutionMetadata（避免 deepcopy 进入
            # ExecutionControl 的 threading.Event 不可 pickle）
            cloned_execution = None
            if self.execution is not None:
                cloned_execution = ExecutionMetadata(
                    execution_id=self.execution.execution_id,
                    task_id=self.execution.task_id,
                    parent_execution_id=self.execution.parent_execution_id,
                    created_at=self.execution.created_at,
                    started_at=self.execution.started_at,
                    finished_at=self.execution.finished_at,
                    deadline_at=self.execution.deadline_at,
                    retry_count=self.execution.retry_count,
                    max_retries=self.execution.max_retries,
                    priority=self.execution.priority,
                    tags=list(self.execution.tags),
                )
                # control 是新实例（execution.control 已由 default_factory 创建）

            cloned = RuntimeContext(
                task_id=self.task_id,
                session_id=self.session_id,
                conversation_id=self.conversation_id,
                group_user_id=self.group_user_id,
                phase=self.phase,
                mode=self.mode,
                model=self.model,
                provider=self.provider,
                project_path=self.project_path,
                memory=copy.deepcopy(self.memory),
                messages=copy.deepcopy(self.messages),
                tool_calls=copy.deepcopy(self.tool_calls),
                request=copy.deepcopy(self.request),
                metrics=RuntimeMetrics(**self.metrics.snapshot()),
                result=RuntimeResult(**self.result.snapshot()),
                metadata=copy.deepcopy(self.metadata),
                status=self.status,
                created_at=self.created_at,
                lifecycle=self.lifecycle,
                activity=self.activity,
                execution=cloned_execution,
                control=ExecutionControl(),  # 新实例（深拷贝 threading.Event 不可 pickle）
            )
        # v0.3: 重建 control 与 execution.control 的 is 关系（保持 ABI 不变量）
        if cloned.execution is not None:
            cloned.control = cloned.execution.control
        # trace 是独立的可变对象，需要单独深拷贝步骤
        cloned.trace = RuntimeTrace()
        for step in self.trace.steps():
            cloned.trace.add(
                node=step.node,
                action=step.action,
                phase=step.phase,
                payload=step.payload,
            )
        return cloned

    def to_dict(self) -> Dict[str, Any]:
        """序列化上下文为字典（兼容旧接口，语义同 snapshot）。"""
        return self.snapshot()

    # ─────────────────────────────────────────────────────────
    # 内部辅助
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _restore_metrics(raw: Any) -> RuntimeMetrics:
        if isinstance(raw, RuntimeMetrics):
            return raw
        if isinstance(raw, dict):
            return RuntimeMetrics(**raw)
        return RuntimeMetrics()

    @staticmethod
    def _restore_result(raw: Any) -> RuntimeResult:
        if isinstance(raw, RuntimeResult):
            return raw
        if isinstance(raw, dict):
            return RuntimeResult(**raw)
        return RuntimeResult()

    @staticmethod
    def _restore_state(raw: Any) -> RuntimeState:
        if isinstance(raw, RuntimeState):
            return raw
        if isinstance(raw, str):
            return RuntimeState(raw)
        return RuntimeState.CREATED

    @staticmethod
    def _restore_lifecycle(raw: Any) -> LifecycleState:
        if isinstance(raw, LifecycleState):
            return raw
        if isinstance(raw, str):
            return LifecycleState(raw)
        return LifecycleState.CREATED

    @staticmethod
    def _restore_activity(raw: Any) -> ActivityState:
        if isinstance(raw, ActivityState):
            return raw
        if isinstance(raw, str):
            return ActivityState(raw)
        return ActivityState.IDLE

    @staticmethod
    def _restore_execution(raw: Any) -> Optional[ExecutionMetadata]:
        if isinstance(raw, ExecutionMetadata):
            return raw
        if isinstance(raw, dict):
            return ExecutionMetadata(
                execution_id=raw.get("execution_id", ""),
                task_id=raw.get("task_id", ""),
                parent_execution_id=raw.get("parent_execution_id"),
            )
        return None

    @staticmethod
    def _restore_control(raw: Any) -> ExecutionControl:
        """从快照恢复控制状态。

        CancellationToken 基于 threading.Event，不可序列化。
        恢复时创建新实例，若快照标记为已取消则重新触发取消。
        """
        control = ExecutionControl()
        if isinstance(raw, dict) and raw.get("cancelled"):
            control.cancel(raw.get("cancel_reason", ""))
        return control

    def _make_snapshot(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "group_user_id": self.group_user_id,
            "phase": self.phase,
            "mode": self.mode,
            "model": self.model,
            "provider": self.provider,
            "project_path": self.project_path,
            "memory": copy.deepcopy(self.memory),
            "messages": [copy.deepcopy(m.__dict__) for m in self.messages],
            "tool_calls": copy.deepcopy(self.tool_calls),
            "request": copy.deepcopy(self.request),
            "metrics": self.metrics.snapshot(),
            "result": self.result.snapshot(),
            "trace": self.trace.snapshot(),
            "metadata": copy.deepcopy(self.metadata),
            "status": self.status.value if isinstance(self.status, RuntimeState) else self.status,
            "created_at": self.created_at,
            "lifecycle": self.lifecycle.value,
            "activity": self.activity.value,
            "execution": {
                "execution_id": self.execution.execution_id,
                "task_id": self.execution.task_id,
                "parent_execution_id": self.execution.parent_execution_id,
            } if self.execution is not None else None,
            # Phase 3.11-C: 控制状态快照（CancellationToken 不可序列化，仅保存状态）
            "control": {
                "cancelled": self.control.is_cancelled,
                "cancel_reason": self.control.cancellation.reason,
            },
        }
