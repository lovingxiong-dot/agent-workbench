"""v6/runtime/engines/interfaces.py — 八大引擎抽象接口。

设计来源：
- docs/v6/SPEC.md 第 8 节引擎接口契约
- 用户原则：RuntimeContext 是唯一运行时状态对象；Engine 统一 run(ctx) 接口

依赖说明：
- 本模块从 v6.runtime.types 导入 ChatMessage 等共享类型。
- 本模块不导入 RuntimeContext，使用字符串前向引用避免循环导入。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from v6.runtime.types import (
    ChatMessage,
    CompressionResult,
    CompressionStrategy,
    InferenceMetrics,
    TokenUsage,
    ToolCall,
    ToolResult,
)

# 重新导出类型，保持 engines 包外部调用方兼容
__all__ = [
    "Engine",
    "IContextEngine",
    "IPromptEngine",
    "IInferenceEngine",
    "IToolEngine",
    "IPhaseEngine",
    "IMemoryEngine",
    "IMetricsEngine",
    "IPolicyEngine",
    "ChatMessage",
    "TokenUsage",
    "InferenceMetrics",
    "ToolCall",
    "ToolResult",
    "CompressionStrategy",
    "CompressionResult",
]


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
    写回 ctx.messages（assistant 消息）和 ctx.metadata['response'] / ctx.metadata['inference_metrics']。
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
    写回 ctx.memory / ctx.metadata['memory_context']。
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
    写回 ctx.metadata['policy_result'] / ctx.metadata['next_action']。
    """

    pass
