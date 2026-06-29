"""
AI Engine — 模块化八引擎层

从 AgentOrchestrator 上帝类拆分的 8 个独立引擎，
遵循单一职责原则，通过接口契约交互。

使用方式：
    from agent_engine.engines import (
        ContextEngine, PromptEngine, InferenceEngine, ToolEngine,
        PhaseEngine, MemoryEngine, MetricsEngine, PolicyEngine,
    )

    # 初始化
    policy = PolicyEngine(config["ai_engine"])
    metrics = MetricsEngine()
    ctx = ContextEngine(policy_engine=policy, metrics_engine=metrics)
    prm = PromptEngine(base_prompts=config["manual_modes"], user_rules=rules)
    inf = InferenceEngine(policy_engine=policy, metrics_engine=metrics, llm_registry=registry)
"""

from .interfaces import (
    Message, TokenUsage, InferenceMetrics, ToolCall, ToolResult,
    CompressionStrategy, CompressionResult,
)
from .context_engine import ContextEngine
from .prompt_engine import PromptEngine
from .inference_engine import InferenceEngine
from .tool_engine import ToolEngine
from .phase_engine import PhaseEngine
from .memory_engine import MemoryEngine
from .metrics_engine import MetricsEngine
from .policy_engine import PolicyEngine

__all__ = [
    "ContextEngine", "PromptEngine", "InferenceEngine", "ToolEngine",
    "PhaseEngine", "MemoryEngine", "MetricsEngine", "PolicyEngine",
    "Message", "TokenUsage", "InferenceMetrics", "ToolCall", "ToolResult",
    "CompressionStrategy", "CompressionResult",
]
