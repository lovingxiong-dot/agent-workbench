"""v6/runtime/engines/context.py — ContextEngine：上下文组装、压缩、token 估算。

设计来源：V4 agent_engine/engines/context_engine.py（提取核心逻辑）。

职责：读取 ctx.metadata 中 user_input / chat_history / system_prompt / max_tokens /
      compression_strategy，写回 ctx.messages。
"""
from __future__ import annotations

import re
from typing import List

from v6.runtime.engines.interfaces import (
    ChatMessage,
    CompressionResult,
    CompressionStrategy,
    IContextEngine,
)


class ContextEngine(IContextEngine):
    """上下文引擎。

    闭环：compress → 下游评估 quality → report_compression_quality → 调整策略权重。
    """

    _strategy_weights: dict = {
        CompressionStrategy.SLIDING_WINDOW: 1.0,
        CompressionStrategy.SEMANTIC_SUMMARY: 1.0,
        CompressionStrategy.ENTITY_PRESERVE: 1.0,
        CompressionStrategy.HYBRID: 1.0,
    }

    def __init__(self, policy_engine=None, metrics_engine=None, llm=None) -> None:
        self.policy = policy_engine
        self.metrics = metrics_engine
        self.llm = llm

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """构建上下文并写回 ctx.messages。"""
        user_input = ctx.metadata.get("user_input", "")
        chat_history = ctx.metadata.get("chat_history", [])
        system_prompt = ctx.metadata.get("system_prompt", "")
        max_tokens = ctx.metadata.get("max_tokens", 8192)
        strategy = ctx.metadata.get(
            "compression_strategy", CompressionStrategy.HYBRID
        )

        ctx.messages = self.build_context(
            user_input=user_input,
            chat_history=chat_history,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            compression_strategy=strategy,
        )
        return ctx

    def build_context(
        self,
        user_input: str,
        chat_history: List[ChatMessage],
        system_prompt: str,
        max_tokens: int,
        compression_strategy: CompressionStrategy = CompressionStrategy.HYBRID,
    ) -> List[ChatMessage]:
        """构建上下文：组装 system + history + user，按需压缩。"""
        messages = [ChatMessage(role="system", content=system_prompt)]
        messages.extend(chat_history)
        messages.append(ChatMessage(role="user", content=user_input))

        estimated = self.estimate_tokens(messages)
        threshold_pct = 0.85
        if self.policy:
            threshold_pct = self.policy.get("context.compression_threshold", 0.85)
        threshold = int(max_tokens * threshold_pct)

        if estimated > threshold:
            if self.metrics:
                self.metrics.record(
                    "context",
                    "compress_triggered",
                    1,
                    {"estimated": estimated, "threshold": threshold},
                )
            result = self.compress(
                messages, target_tokens=threshold, strategy=compression_strategy
            )
            messages = result.messages
            if self.metrics:
                self.metrics.record(
                    "context", "compression_ratio", result.compression_ratio
                )

        return messages

    def compress(
        self,
        messages: List[ChatMessage],
        target_tokens: int,
        strategy: CompressionStrategy = CompressionStrategy.HYBRID,
        guidance: str = "",
    ) -> CompressionResult:
        """压缩消息列表到目标 token 数量。"""
        if strategy == CompressionStrategy.HYBRID:
            strategy = self._select_best_strategy()
        if strategy == CompressionStrategy.SLIDING_WINDOW:
            return self._compress_sliding_window(messages, target_tokens)
        elif strategy == CompressionStrategy.SEMANTIC_SUMMARY:
            return self._compress_semantic(messages, target_tokens, guidance)
        elif strategy == CompressionStrategy.ENTITY_PRESERVE:
            return self._compress_entity_preserve(messages, target_tokens, guidance)
        return self._compress_hybrid(messages, target_tokens, guidance)

    def estimate_tokens(self, messages: List[ChatMessage]) -> int:
        """估算 token 数量（字符数 / 1.2 经验值）。"""
        total_chars = sum(len(m.content) for m in messages)
        return int(total_chars / 1.2)

    def report_compression_quality(self, quality_score: float) -> None:
        """【闭环】接收压缩质量反馈。"""
        if quality_score < 0.5 and self.metrics:
            self.metrics.record(
                "context", "compression_quality_low", 1, {"score": quality_score}
            )

    def _select_best_strategy(self) -> CompressionStrategy:
        """选择当前权重最高的策略。"""
        best = max(self._strategy_weights, key=self._strategy_weights.get)
        return best

    def _compress_sliding_window(
        self, messages: List[ChatMessage], target_tokens: int
    ) -> CompressionResult:
        system_msgs = [m for m in messages if m.role == "system"]
        others = [m for m in messages if m.role != "system"]
        keep = 0
        for i in range(len(others), 0, -1):
            if self.estimate_tokens(system_msgs + others[-i:]) <= target_tokens:
                keep = i
                break
        compressed = system_msgs + others[-keep:] if keep > 0 else system_msgs
        ratio = 1.0 - (len(compressed) / max(len(messages), 1))
        return CompressionResult(messages=compressed, compression_ratio=ratio)

    def _compress_semantic(
        self, messages: List[ChatMessage], target_tokens: int, guidance: str
    ) -> CompressionResult:
        system_msgs = [m for m in messages if m.role == "system"]
        history = [m for m in messages if m.role != "system"]
        hot_count = 4
        hot = history[-hot_count:] if len(history) > hot_count else history
        compressed = list(system_msgs)
        compressed.extend(hot)
        ratio = 1.0 - (len(compressed) / max(len(messages), 1))
        return CompressionResult(messages=compressed, compression_ratio=ratio)

    def _compress_entity_preserve(
        self, messages: List[ChatMessage], target_tokens: int, guidance: str
    ) -> CompressionResult:
        base = self._compress_semantic(messages, target_tokens, guidance)
        entities = self._extract_entities([m for m in messages if m.role != "system"])
        if entities:
            entity_line = f"[关键实体] {', '.join(entities[:20])}"
            base.messages.insert(1, ChatMessage(role="system", content=entity_line))
        base.preserved_entities = entities
        return base

    def _compress_hybrid(
        self, messages: List[ChatMessage], target_tokens: int, guidance: str
    ) -> CompressionResult:
        result = self._compress_semantic(messages, target_tokens, guidance)
        if self.estimate_tokens(result.messages) > target_tokens:
            result = self._compress_sliding_window(result.messages, target_tokens)
        return result

    def _extract_entities(self, messages: List[ChatMessage]) -> List[str]:
        text = " ".join(m.content for m in messages)
        entities: List[str] = []
        entities.extend(re.findall(r'"([^"]+)"', text))
        entities.extend(re.findall(r"'([^']+)'", text))
        entities.extend(re.findall(r"[A-Za-z]:\\[^\s]+", text))
        entities.extend(re.findall(r"/[\w/]+\.\w+", text))
        return list(dict.fromkeys(entities))
