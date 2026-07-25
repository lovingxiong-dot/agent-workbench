"""v6/runtime/execution_metadata.py — 单次执行的身份元数据。

Phase 3.11-A: Execution Identity Model。
Phase 3.11-D v0.3: deadline_at 模型替换 timeout_seconds；新增 ExecutionControl 归属。
设计文档：docs/v6/phase3-11-a-execution-model-design.md
             docs/v6/phase3-11-d-parent-child-execution-design.md
ADR-015 v0.3 — Parent-Child Execution Propagation。

核心原则：
- ExecutionMetadata 是 Execution Identity，不是 Task Identity。
- Task 是业务模型，ExecutionMetadata 是执行模型。
- 不写入 RuntimeEvent.payload，不替代 Task，不包含 UI 相关字段。
- 零 graph 字段（除 parent_execution_id 单向引用）。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from v6.runtime.execution_control import ExecutionControl


@dataclass
class ExecutionMetadata:
    """单次执行的身份元数据。

    关系：
        Task 1 ──── ExecutionMetadata A  (第 1 次执行)
              └──── ExecutionMetadata B  (retry 第 2 次执行)

    Phase 3.11-D v0.3 关键变更：
    - timeout_seconds → deadline_at（绝对时间点）
    - 新增 control: ExecutionControl 字段（v0.3 归属迁移）
    - 零 graph 字段（parent_execution_id 是唯一 graph 字段）
    """

    # ── Identity ──────────────────────────────────────
    execution_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    task_id: str = ""
    # v0.3: parent_execution_id 是唯一 graph 字段，单一指向
    parent_execution_id: Optional[str] = None

    # ── Timestamps ────────────────────────────────────
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    # ── Control (v0.3) ────────────────────────────────
    # v0.3: 替换 timeout_seconds，deadline 是绝对时间点
    deadline_at: Optional[datetime] = None
    # v0.3: ExecutionControl 归属 ExecutionMetadata
    control: ExecutionControl = field(default_factory=ExecutionControl)

    # ── Retry ─────────────────────────────────────────
    retry_count: int = 0
    max_retries: int = 0

    # ── Priority ──────────────────────────────────────
    priority: int = 0  # 0 = default, higher = more urgent

    # ── Tags ──────────────────────────────────────────
    tags: list[str] = field(default_factory=list)

    # ── Computed Properties ───────────────────────────

    @property
    def is_deadline_reached(self) -> bool:
        """判断是否已到达 deadline（基于 deadline_at）。"""
        if self.deadline_at is None:
            return False
        return datetime.now(timezone.utc) >= self.deadline_at

    @property
    def duration_seconds(self) -> Optional[float]:
        """执行耗时（秒），未完成时返回 None。"""
        if self.started_at is None:
            return None
        end = self.finished_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def is_root_execution(self) -> bool:
        """是否无父执行（顶级任务）。"""
        return self.parent_execution_id is None

    @property
    def is_retry(self) -> bool:
        """是否为重试执行。"""
        return self.retry_count > 0