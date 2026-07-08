"""agent_workbench/runtime/capability/state.py — Capability 运行时生命周期状态契约。

设计约束：
- CapabilityState 只描述能力在 Runtime 中的生命周期阶段，不携带业务结果。
- CapabilityExecutionState 挂靠在 Registry 中，不写入 Task 五字段。
- 状态枚举为 Runtime 契约，预留 CANCELLED / TIMEOUT / SKIPPED 供 Workflow 阶段使用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityState(str, Enum):
    """Capability 生命周期状态。"""

    PENDING = "pending"
    RESOLVED = "resolved"          # 已从 Intent 解析出 Definition
    SCHEDULED = "scheduled"        # 已进入 Orchestrator
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"        # 预留：Workflow / 用户取消
    TIMEOUT = "timeout"            # 预留：执行超时
    SKIPPED = "skipped"            # 预留：条件分支跳过


@dataclass
class CapabilityExecutionState:
    """Capability 在某次执行中的运行时状态快照。

    - capability_id: 对应 CapabilityDefinition.id。
    - state: 当前生命周期状态。
    - task_id: 关联的 Task.id（如存在）。
    - started_at / finished_at:  Unix 时间戳。
    - error: 失败时的可读错误信息。
    - metadata: 扩展字段（不保存 Trace / History / Statistics 等重数据）。
    """

    capability_id: str
    state: CapabilityState
    task_id: str | None = None
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
