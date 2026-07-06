"""v6/runtime/engines/llm.py — LLM Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入任何真实 LLM 或推理框架。
未来职责：模型调用、流式输出、重试降级、token/耗时上报。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class LLMEngine(BaseEngine):
    """LLM Engine：负责大语言模型调用。"""

    name = "llm"
