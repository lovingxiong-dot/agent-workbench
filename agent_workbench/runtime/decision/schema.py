"""agent_workbench/runtime/decision/schema.py — Runtime Decision Layer 协议对象。

设计约束：
- 本文件只定义协议（schema），禁止导入 capability / planner / service / orchestrator 等执行层模块。
- 所有引用均使用 str / dict / list 等基础类型，避免循环依赖。
- Decision Layer 属于 Runtime Kernel Control Plane，不是 Capability Module。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuntimeMode(str, Enum):
    """Runtime 调度模式。"""

    CHAT = "chat"
    ACTION = "action"
    WORKFLOW = "workflow"


class IntentType(str, Enum):
    """Intent 类型（第一版基础集合，避免无限字符串）。"""

    GENERAL_QUERY = "general_query"
    CREATE_ARTIFACT = "create_artifact"
    ANALYZE = "analyze"
    TRANSFORM = "transform"
    EXECUTE_ACTION = "execute_action"
    SEARCH = "search"


class IntentError(Exception):
    """Intent 解析或校验失败。"""


@dataclass
class Intent:
    """LLM Interpreter 输出：结构化用户意图。

    字段说明：
    - mode: Runtime 调度模式。
    - type: 意图类型。
    - entities: 从用户输入提取的命名实体。
    - raw_input: 原始用户输入（用于可解释性与回退）。
    """

    mode: RuntimeMode
    type: IntentType
    entities: dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value if isinstance(self.mode, Enum) else self.mode,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "entities": dict(self.entities),
            "raw_input": self.raw_input,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Intent":
        return cls(
            mode=RuntimeMode(data.get("mode", "chat")),
            type=IntentType(data.get("type", "general_query")),
            entities=dict(data.get("entities", {})),
            raw_input=data.get("raw_input", ""),
        )


@dataclass
class RuntimeDecision:
    """Orchestrator 控制平面入口。

    字段说明：
    - mode: Runtime 调度模式。
    - intent: 结构化意图。
    - route: 确定性路由目标，例如 "capability://coding.python" 或 "workflow://default"。
    - payload: 执行层需要的附加数据（不携带具体对象，仅基础类型）。
    - capability_chain: ACTION 模式下可选的静态能力链（以原始 dict list 形式存在，避免依赖 chain.py）。
    - execution_plan: WORKFLOW 模式下可选的执行计划引用（以 dict 形式存在，避免依赖 planner）。

    依赖方向：
        decision → orchestrator → capability → service
    禁止 decision 反向依赖 capability / planner / service。
    """

    mode: RuntimeMode
    intent: Intent
    route: str
    payload: dict[str, Any] | None = None
    capability_chain: list[dict[str, Any]] | None = None
    execution_plan: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value if isinstance(self.mode, Enum) else self.mode,
            "intent": self.intent.to_dict(),
            "route": self.route,
            "payload": dict(self.payload) if self.payload is not None else None,
            "capability_chain": (
                [dict(item) for item in self.capability_chain]
                if self.capability_chain is not None
                else None
            ),
            "execution_plan": dict(self.execution_plan) if self.execution_plan is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeDecision":
        return cls(
            mode=RuntimeMode(data.get("mode", "chat")),
            intent=Intent.from_dict(data.get("intent", {})),
            route=data.get("route", ""),
            payload=dict(data["payload"]) if data.get("payload") is not None else None,
            capability_chain=(
                [dict(item) for item in data["capability_chain"]]
                if data.get("capability_chain") is not None
                else None
            ),
            execution_plan=dict(data["execution_plan"]) if data.get("execution_plan") is not None else None,
        )
