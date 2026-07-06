"""v6/runtime/types.py — V6 Runtime 基础共享类型。

设计原则：
- 本模块位于 Runtime 类型层最底部，不依赖任何 Engine、RuntimeContext 或业务模块。
- ChatMessage、ToolCall、ToolResult、TokenUsage、InferenceMetrics 等类型在此定义。
- RuntimeContext 从本模块导入 ChatMessage；interfaces.py 也从本模块导入。
- 依赖方向固定：RuntimeContext 包含 ChatMessage，而不是 RuntimeContext 依赖 interfaces。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    """标准聊天消息格式。

    ChatMessage 是 RuntimeContext.messages 的组成部分，不是 Runtime 的顶层对象。
    字段可演进（未来可增加 tool_call_id、images、attachments、tokens 等），
    外部代码应优先使用 RuntimeContext.add_message() 而非直接构造。
    """

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


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
