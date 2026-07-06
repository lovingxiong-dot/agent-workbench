"""v6/runtime/engines/interfaces.py — 八大引擎共享数据类型与抽象接口。

设计来源：
- docs/v6/SPEC.md 第 8 节引擎接口契约
- 用户原则：RuntimeContext 是唯一运行时状态对象（Single Source of Truth）

核心原则：
- Engine 不拥有状态，RuntimeContext 才拥有状态。
- 所有 Engine 统一接口：async def run(self, ctx: RuntimeContext) -> RuntimeContext。
- ChatMessage 只是 RuntimeContext.messages 的组成部分，不得成为 Engine 间通信对象。
- RuntimeContext 是可演进对象，Engine 只访问自身职责需要的字段。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════
# 共享数据类型
# ═══════════════════════════════════════════════════════


@dataclass
class ChatMessage:
    """标准聊天消息格式，作为 RuntimeContext.messages 的元素。"""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_langchain(self):
        """转换为 LangChain 消息（按需导入，降低硬依赖）。"""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        if self.role == "system":
            return SystemMessage(content=self.content)
        elif self.role == "user":
            return HumanMessage(content=self.content)
        elif self.role == "assistant":
            if self.tool_calls:
                return AIMessage(content=self.content, tool_calls=self.tool_calls)
            return AIMessage(content=self.content)
        elif self.role == "tool":
            return ToolMessage(
                content=self.content, tool_call_id=self.tool_call_id or ""
            )
        return HumanMessage(content=self.content)


@dataclass
class TokenUsage:
    """token 用量。"""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class InferenceMetrics:
    """推理指标。"""

    model_id: str = ""
    provider: str = ""
    success: bool = True
    error_code: str = ""
    ttft_ms: int = 0
    total_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class ToolCall:
    """工具调用请求。"""

    name: str
    args: Dict[str, Any]
    call_id: str = ""


@dataclass
class ToolResult:
    """工具执行结果。"""

    name: str
    result: str
    elapsed_ms: int = 0
    success: bool = True


class CompressionStrategy(str, Enum):
    """上下文压缩策略。"""

    SLIDING_WINDOW = "sliding_window"
    SEMANTIC_SUMMARY = "semantic_summary"
    ENTITY_PRESERVE = "entity_preserve"
    HYBRID = "hybrid"


@dataclass
class CompressionResult:
    """上下文压缩结果。"""

    messages: List[ChatMessage]
    compression_ratio: float = 0.0
    summary_text: Optional[str] = None
    preserved_entities: List[str] = field(default_factory=list)
    quality_score: float = 1.0


# ═══════════════════════════════════════════════════════
# 引擎基类与接口
# ═══════════════════════════════════════════════════════


class Engine(ABC):
    """引擎基类：统一 run(ctx) 接口。

    RuntimeContext 是唯一运行时状态对象。Engine 只读取/修改自己负责的字段，
    不拥有私有状态。
    """

    @abstractmethod
    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """执行引擎职责，修改 ctx 中对应字段后返回 ctx。"""
        pass


class IContextEngine(Engine):
    """上下文引擎：负责 project、workspace、runtime_state。

    读取 ctx.metadata 中：
    - user_input / chat_history / system_prompt / max_tokens / compression_strategy
    写回 ctx.messages。
    """

    pass


class IPromptEngine(Engine):
    """Prompt 引擎：负责 prompt、system_prompt。

    读取 ctx.metadata 中：
    - mode / phase / user_profile / workspace_context
    写回 ctx.metadata["system_prompt"]。
    """

    pass


class IInferenceEngine(Engine):
    """推理引擎：负责 messages、response。

    读取 ctx.messages / ctx.metadata 中 model / temperature / max_tokens / timeout。
    写回 ctx.messages（assistant 消息）和 ctx.metadata["response"] / ctx.metadata["inference_metrics"]。
    """

    pass


class IToolEngine(Engine):
    """工具引擎：负责 tool_calls、tool_results。

    读取 ctx.metadata["tool_calls"] / ctx.phase。
    写回 ctx.metadata["tool_results"]。
    """

    pass


class IPhaseEngine(Engine):
    """阶段引擎：负责 phase。

    读取 ctx.mode / ctx.phase。
    写回 ctx.phase。
    """

    pass


class IMemoryEngine(Engine):
    """记忆引擎：负责 memory、history、retrieved_context。

    读取 ctx.session_id / ctx.messages。
    写回 ctx.memory / ctx.metadata["memory_context"]。
    """

    pass


class IMetricsEngine(Engine):
    """指标引擎：负责 metrics。

    读取 ctx.metadata["metric_records"]（可选）。
    写回 ctx.metrics。
    """

    pass


class IPolicyEngine(Engine):
    """策略引擎：负责 policy、next_action。

    读取 ctx.metadata 中 policy_query / query_features / session_metrics。
    写回 ctx.metadata["policy_result"] / ctx.metadata["next_action"]。
    """

    pass
