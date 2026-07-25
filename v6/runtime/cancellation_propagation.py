"""v6/runtime/cancellation_propagation.py — Cancellation 传播上下文。

Phase 3.11-D v0.3 — CancellationPropagationContext + PropagationType。
设计文档：docs/v6/phase3-11-d-parent-child-execution-design.md
ADR-015 v0.3 — Parent-Child Execution Propagation。

核心原则：
- 取消传播通过结构化上下文传递，取代字符串拼接。
- Context 是 invariant owner：内部 enforce depth + origin/chain invariant。
- frozen dataclass：不可变；extend() 返回新实例。
- v0.3: 移除 PARENT_TIMEOUT，统一为 DEADLINE_EXCEEDED。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Tuple, Optional


class CancellationPropagationLimitExceeded(Exception):
    """v0.3: 取消传播链深度超限异常。"""

    def __init__(self, depth: int, max_depth: int) -> None:
        self.depth = depth
        self.max_depth = max_depth
        super().__init__(
            f"Cancellation propagation chain depth {depth} exceeds limit {max_depth}"
        )


class PropagationType(str, Enum):
    """v0.3: 取消传播触发类型。

    v0.3 变更：移除 PARENT_TIMEOUT，统一为 DEADLINE_EXCEEDED。
    """
    USER_REQUEST = "user_request"
    PARENT_CANCELLED = "parent_cancelled"
    DEADLINE_EXCEEDED = "deadline_exceeded"


# v0.3: 取消传播链最大深度（防御栈溢出）
MAX_PROPAGATION_DEPTH = 32


@dataclass(frozen=True)
class CancellationPropagationContext:
    """取消传播上下文（v0.3: frozen + invariants）。

    不可变 dataclass，每次传播创建新实例（extend 语义）。

    Invariants：
    - chain[0] == origin_execution_id（__post_init__ 验证）
    - len(chain) ≤ MAX_PROPAGATION_DEPTH（extend() 内部 enforce）

    用于：
    - TASK_CANCELLED 事件 payload（to_payload()）
    - CancellationToken.reason 记录（to_reason_string()）
    - Trace 调试
    """
    propagation_type: PropagationType
    origin_execution_id: str
    chain: Tuple[str, ...]
    reason: str
    initiated_at: datetime

    def __post_init__(self) -> None:
        """v0.3: enforce origin/chain invariant。"""
        if self.chain and self.chain[0] != self.origin_execution_id:
            raise ValueError(
                f"chain[0] ({self.chain[0]}) must equal "
                f"origin_execution_id ({self.origin_execution_id})"
            )

    @staticmethod
    def user_request(
        origin_execution_id: str,
        reason: str = "",
    ) -> "CancellationPropagationContext":
        """顶层用户取消。"""
        return CancellationPropagationContext(
            propagation_type=PropagationType.USER_REQUEST,
            origin_execution_id=origin_execution_id,
            chain=(origin_execution_id,),  # v0.3: chain[0] = origin
            reason=reason or "user_request",
            initiated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def deadline_exceeded(
        execution_id: str,
        deadline_at: datetime,
    ) -> "CancellationPropagationContext":
        """v0.3: Deadline 到期触发的取消。"""
        return CancellationPropagationContext(
            propagation_type=PropagationType.DEADLINE_EXCEEDED,
            origin_execution_id=execution_id,
            chain=(execution_id,),
            reason=f"deadline exceeded at {deadline_at.isoformat()}",
            initiated_at=datetime.now(timezone.utc),
        )

    def extend(
        self,
        current_execution_id: str,
        new_type: Optional[PropagationType] = None,
    ) -> "CancellationPropagationContext":
        """v0.3: 生成下一级传播上下文，内部 enforce depth limit。

        Args:
            current_execution_id: 当前 execution（要被 cancel 的）
            new_type: 若指定，覆盖 propagation_type

        Raises:
            CancellationPropagationLimitExceeded: chain depth 超限
        """
        new_depth = len(self.chain) + 1
        if new_depth > MAX_PROPAGATION_DEPTH:
            raise CancellationPropagationLimitExceeded(
                depth=new_depth,
                max_depth=MAX_PROPAGATION_DEPTH,
            )

        return CancellationPropagationContext(
            propagation_type=new_type or self.propagation_type,
            origin_execution_id=self.origin_execution_id,
            chain=self.chain + (current_execution_id,),
            reason=self.reason,
            initiated_at=self.initiated_at,
        )

    def to_payload(self) -> dict:
        """转换为 TASK_CANCELLED 事件 payload。"""
        return {
            "propagation_type": self.propagation_type.value,
            "origin_execution_id": self.origin_execution_id,
            "chain": list(self.chain),
            "reason": self.reason,
            "initiated_at": self.initiated_at.isoformat(),
        }

    def to_reason_string(self) -> str:
        """人类可读 reason 字符串。"""
        if self.propagation_type == PropagationType.USER_REQUEST:
            return self.reason or "user_request"
        return f"{self.propagation_type.value}:{self.origin_execution_id}"

    def max_chain_depth(self) -> int:
        """返回 chain 长度。"""
        return len(self.chain)