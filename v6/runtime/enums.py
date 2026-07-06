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

    后续 Timeline / Debug / Replay / Metrics 全部统一引用这一份。
    """

    # Runtime 生命周期
    TASK_START = "task_start"
    TASK_FINISH = "task_finish"
    TASK_ERROR = "task_error"
    HANDLER_DISPATCH = "handler_dispatch"
    HANDLER_MISSING = "handler_missing"

    # Adapter
    ADAPTER_SUBMIT = "adapter_submit"
    ADAPTER_CANCEL = "adapter_cancel"

    # Engine 通用
    ENGINE_START = "engine_start"
    ENGINE_END = "engine_end"
    ENGINE_INPUT_READ = "engine_input_read"

    # Inference
    MODEL_INVOKE = "model_invoke"
    MODEL_FINISH = "model_finish"
    PROMPT_BUILD = "prompt_build"

    # Memory
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"

    # Tool
    TOOL_INVOKE = "tool_invoke"
    TOOL_RESULT = "tool_result"

    # Event 输出
    EMIT_START = "emit_start"
    EMIT_CHUNK = "emit_chunk"
    EMIT_END = "emit_end"
    EMIT_ERROR = "emit_error"


class RuntimeState(str, Enum):
    """Runtime Task 生命周期状态枚举。

    未来可迁移到 RuntimeTask.state；当前先由 RuntimeContext.status 承载。
    """

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
