"""v6/runtime/enums.py — Runtime Kernel 核心枚举。

设计来源：docs/v6/SPEC.md 第 8 节及 Runtime Kernel 演进方向。

目的：
- 统一 Runtime Phase、Trace Event、Runtime State 的命名，避免字符串漂移。
- 为后续 RuntimeTask 五对象模型（Context/Trace/Metrics/Result/State）做准备。
- 当前不强制拆分 RuntimeTask，但先把枚举语义固定下来。
"""
from __future__ import annotations

from enum import Enum, auto


class RuntimePhase(str, Enum):
    """Runtime 执行阶段枚举。

    所有 Engine、Trace、Scheduler 统一引用这一份，避免 "tool"/"Tool"/"TOOLS" 漂移。
    """

    INPUT = "input"
    PLAN = "plan"
    MEMORY = "memory"
    TOOL = "tool"
    INFERENCE = "inference"
    OUTPUT = "output"
    FINISH = "finish"


class TraceEvent(str, Enum):
    """Trace 事件类型枚举。

    按 Runtime Observability 分层组织：
    Task -> Capability -> Engine -> Provider -> Execution -> Stream。
    后续 Timeline / Debug / Replay / Metrics / Tree UI 全部统一引用这一份。

    设计原则：
    - 不绑定 LLM Streaming，支持 Image/Video/Tool/Workflow 等多模态能力。
    - Provider/Service/Model 事件为可选，不同 Engine 按需发射。
    """

    # Task 生命周期
    TASK_START = "task_start"
    TASK_FINISH = "task_finish"
    TASK_ERROR = "task_error"

    # Capability 路由
    CAPABILITY_RESOLVED = "capability_resolved"

    # Engine 选择与执行
    ENGINE_SELECTED = "engine_selected"
    ENGINE_START = "engine_start"
    ENGINE_END = "engine_end"
    ENGINE_INPUT_READ = "engine_input_read"

    # Provider / Service / Model（可选）
    PROVIDER_SELECTED = "provider_selected"
    SERVICE_SELECTED = "service_selected"
    MODEL_SELECTED = "model_selected"

    # Execution 执行
    REQUEST_SENT = "request_sent"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_FINISHED = "execution_finished"

    # Stream 流式输出
    FIRST_TOKEN = "first_token"
    CHUNK_RECEIVED = "chunk_received"
    STREAM_FINISHED = "stream_finished"

    # Legacy / Foundation 兼容事件
    HANDLER_DISPATCH = "handler_dispatch"
    HANDLER_MISSING = "handler_missing"
    ADAPTER_SUBMIT = "adapter_submit"
    ADAPTER_CANCEL = "adapter_cancel"
    MODEL_INVOKE = "model_invoke"
    MODEL_FINISH = "model_finish"
    PROMPT_BUILD = "prompt_build"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    TOOL_INVOKE = "tool_invoke"
    TOOL_RESULT = "tool_result"
    EMIT_START = "emit_start"
    EMIT_CHUNK = "emit_chunk"
    EMIT_END = "emit_end"
    EMIT_ERROR = "emit_error"


# TraceEvent 所属层级，用于 Tree UI 与 parent_id 推断。
TRACE_EVENT_LEVEL: dict[TraceEvent, str] = {
    TraceEvent.TASK_START: "task",
    TraceEvent.TASK_FINISH: "task",
    TraceEvent.TASK_ERROR: "task",
    TraceEvent.HANDLER_DISPATCH: "task",
    TraceEvent.HANDLER_MISSING: "task",
    TraceEvent.CAPABILITY_RESOLVED: "capability",
    TraceEvent.ENGINE_SELECTED: "engine",
    TraceEvent.ENGINE_START: "engine",
    TraceEvent.ENGINE_END: "engine",
    TraceEvent.ENGINE_INPUT_READ: "engine",
    TraceEvent.PROVIDER_SELECTED: "provider",
    TraceEvent.SERVICE_SELECTED: "provider",
    TraceEvent.MODEL_SELECTED: "provider",
    TraceEvent.REQUEST_SENT: "request",
    TraceEvent.EXECUTION_STARTED: "execution",
    TraceEvent.EXECUTION_PROGRESS: "execution",
    TraceEvent.EXECUTION_FINISHED: "execution",
    TraceEvent.FIRST_TOKEN: "stream",
    TraceEvent.CHUNK_RECEIVED: "stream",
    TraceEvent.STREAM_FINISHED: "stream",
    TraceEvent.ADAPTER_SUBMIT: "adapter",
    TraceEvent.ADAPTER_CANCEL: "adapter",
    TraceEvent.MODEL_INVOKE: "execution",
    TraceEvent.MODEL_FINISH: "execution",
    TraceEvent.PROMPT_BUILD: "execution",
    TraceEvent.MEMORY_READ: "memory",
    TraceEvent.MEMORY_WRITE: "memory",
    TraceEvent.TOOL_INVOKE: "tool",
    TraceEvent.TOOL_RESULT: "tool",
    TraceEvent.EMIT_START: "stream",
    TraceEvent.EMIT_CHUNK: "stream",
    TraceEvent.EMIT_END: "stream",
    TraceEvent.EMIT_ERROR: "stream",
}

# 层级父子关系，供 Trace Hook 自动推断 parent_id。
TRACE_EVENT_PARENT_LEVEL: dict[str, str | None] = {
    "task": None,
    "capability": "task",
    "engine": "task",
    "provider": "execution",
    "request": "execution",
    "execution": "engine",
    "stream": "execution",
    "adapter": "task",
    "memory": "task",
    "tool": "engine",
}


class RuntimeState(str, Enum):
    """Runtime Task 生命周期状态枚举（向后兼容）。

    Phase 3.11 起，新代码应使用 LifecycleState + ActivityState 双状态模型。
    本枚举保留用于旧代码兼容。
    """

    CREATED = "created"
    QUEUED = "queued"
    PLANNING = "planning"
    EXECUTING = "executing"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class LifecycleState(str, Enum):
    """任务生命周期状态（Phase 3.11-A 双状态模型）。

    每个 Task 在当前时刻仅处于一个 LifecycleState。
    终态：COMPLETED / FAILED / CANCELLED。
    """

    CREATED = "created"       # 任务已创建，尚未提交
    QUEUED = "queued"         # 已提交到调度队列，等待分配
    PLANNING = "planning"     # 正在规划执行策略
    EXECUTING = "executing"   # 正在执行（ActivityState 描述具体活动）
    COMPLETED = "completed"   # 终态：执行成功
    FAILED = "failed"         # 终态：执行失败
    CANCELLED = "cancelled"   # 终态：已取消


class ActivityState(str, Enum):
    """当前执行活动状态（Phase 3.11-A 双状态模型）。

    仅在 LifecycleState.EXECUTING 期间有意义。
    其他 LifecycleState 下固定为 IDLE。
    """

    IDLE = "idle"           # 无活动（非 EXECUTING 状态）
    RUNNING = "running"     # 正在执行（通用）
    STREAMING = "streaming" # 流式输出中（LLM）
    WAITING = "waiting"     # 等待外部事件（Tool/MCP/API）
    PAUSED = "paused"       # 已暂停（用户或系统触发）


# LifecycleState → RuntimeState 向后兼容映射
_LIFECYCLE_TO_RUNTIME: dict[LifecycleState, RuntimeState] = {
    LifecycleState.CREATED: RuntimeState.CREATED,
    LifecycleState.QUEUED: RuntimeState.QUEUED,
    LifecycleState.PLANNING: RuntimeState.PLANNING,
    LifecycleState.EXECUTING: RuntimeState.EXECUTING,
    LifecycleState.COMPLETED: RuntimeState.COMPLETED,
    LifecycleState.FAILED: RuntimeState.FAILED,
    LifecycleState.CANCELLED: RuntimeState.CANCELLED,
}


def lifecycle_to_runtime(lifecycle: LifecycleState) -> RuntimeState:
    """将 LifecycleState 映射到旧 RuntimeState（向后兼容）。"""
    return _LIFECYCLE_TO_RUNTIME.get(lifecycle, RuntimeState.CREATED)
