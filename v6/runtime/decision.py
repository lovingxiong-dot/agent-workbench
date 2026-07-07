"""v6/runtime/decision.py — Runtime Decision 模型。

设计来源：V6.5 Runtime Foundation Layer Step 5.5。

核心原则：
- Decision 是 PlannerLoop 的输出，也是 Orchestrator 的输入。
- Decision 只描述"下一步做什么"，不执行业务逻辑。
- action 使用枚举，避免字符串漂移。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DecisionAction(str, Enum):
    """决策动作枚举。"""

    EXECUTE_ENGINE = "execute_engine"
    WAIT = "wait"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass
class Decision:
    """单次决策结果。

    字段说明：
    - action: 决策动作，例如 execute_engine / complete / fail / wait。
    - target: 目标能力或 Engine 名称；EXECUTE_ENGINE 时必填。
    - reason: 决策原因，供调试与可解释性。
    - metadata: 额外元数据，例如 confidence / policy / alternatives。
    """

    action: str
    target: Optional[str] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """统一把枚举转成字符串存储，保持序列化一致性。"""
        if isinstance(self.action, DecisionAction):
            self.action = self.action.value

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "action": self.action,
            "target": self.target,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def execute(
        cls,
        target: str,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Decision":
        """工厂方法：执行 Engine。"""
        return cls(
            action=DecisionAction.EXECUTE_ENGINE,
            target=target,
            reason=reason,
            metadata=metadata or {},
        )

    @classmethod
    def complete(
        cls,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Decision":
        """工厂方法：完成任务。"""
        return cls(
            action=DecisionAction.COMPLETE,
            reason=reason,
            metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Decision":
        """工厂方法：任务失败。"""
        return cls(
            action=DecisionAction.FAIL,
            reason=reason,
            metadata=metadata or {},
        )

    @classmethod
    def wait(
        cls,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Decision":
        """工厂方法：等待。"""
        return cls(
            action=DecisionAction.WAIT,
            reason=reason,
            metadata=metadata or {},
        )
