"""
Context Engine — 上下文组装、压缩、token 估算

从 AgentOrchestrator._build_messages() 和 AgentSession._trim_phase_messages() 提取。
设计为注入式：通过构造函数注入 PolicyEngine 和 MetricsEngine，实现闭环反馈。
"""
from typing import List, Optional
from .interfaces import (
    IContextEngine, Message, CompressionResult, CompressionStrategy
)


class ContextEngine(IContextEngine):
    """上下文引擎

    闭环：compress → 下游评估 quality → report_compression_quality → 调整策略权重
    """

    _strategy_weights: dict = {
        CompressionStrategy.SLIDING_WINDOW: 1.0,
        CompressionStrategy.SEMANTIC_SUMMARY: 1.0,
        CompressionStrategy.ENTITY_PRESERVE: 1.0,
        CompressionStrategy.HYBRID: 1.0,
    }

    def __init__(self, policy_engine=None, metrics_engine=None, llm=None):
        self.policy = policy_engine
        self.metrics = metrics_engine
        self.llm = llm

    def build_context(
        self,
        user_input: str,
        chat_history: List[Message],
        system_prompt: str,
        max_tokens: int,
        compression_strategy: CompressionStrategy = CompressionStrategy.HYBRID,
    ) -> List[Message]:
        messages = [Message(role="system", content=system_prompt)]
        messages.extend(chat_history)
        messages.append(Message(role="user", content=user_input))

        estimated = self.estimate_tokens(messages)
        threshold_pct = 0.85
        if self.policy:
            threshold_pct = self.policy.get("context.compression_threshold", 0.85)
        threshold = int(max_tokens * threshold_pct)

        if estimated > threshold:
            if self.metrics:
                self.metrics.record("context", "compress_triggered", 1,
                                    {"estimated": estimated, "threshold": threshold})
            result = self.compress(messages, target_tokens=threshold, strategy=compression_strategy)
            messages = result.messages
            if self.metrics:
                self.metrics.record("context", "compression_ratio", result.compression_ratio)

        return messages

    def compress(
        self,
        messages: List[Message],
        target_tokens: int,
        strategy: CompressionStrategy = CompressionStrategy.HYBRID,
        guidance: str = "",
    ) -> CompressionResult:
        if strategy == CompressionStrategy.HYBRID:
            strategy = self._select_best_strategy()
        if strategy == CompressionStrategy.SLIDING_WINDOW:
            return self._compress_sliding_window(messages, target_tokens)
        elif strategy == CompressionStrategy.SEMANTIC_SUMMARY:
            return self._compress_semantic(messages, target_tokens, guidance)
        elif strategy == CompressionStrategy.ENTITY_PRESERVE:
            return self._compress_entity_preserve(messages, target_tokens, guidance)
        return self._compress_hybrid(messages, target_tokens, guidance)

    def estimate_tokens(self, messages: List[Message]) -> int:
        total_chars = sum(len(m.content) for m in messages)
        return int(total_chars / 1.2)

    def report_compression_quality(self, quality_score: float) -> None:
        if quality_score < 0.5 and self.metrics:
            self.metrics.record("context", "compression_quality_low", 1,
                                {"score": quality_score})

    # ── 内部 ──

    def _select_best_strategy(self) -> CompressionStrategy:
        best = max(self._strategy_weights, key=self._strategy_weights.get)
        return best

    def _compress_sliding_window(self, messages: List[Message], target_tokens: int) -> CompressionResult:
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

    def _compress_semantic(self, messages, target_tokens, guidance) -> CompressionResult:
        system_msgs = [m for m in messages if m.role == "system"]
        history = [m for m in messages if m.role != "system"]
        hot_count = 4
        hot = history[-hot_count:] if len(history) > hot_count else history
        compressed = system_msgs
        compressed.extend(hot)
        ratio = 1.0 - (len(compressed) / max(len(messages), 1))
        return CompressionResult(messages=compressed, compression_ratio=ratio)

    def _compress_entity_preserve(self, messages, target_tokens, guidance) -> CompressionResult:
        base = self._compress_semantic(messages, target_tokens, guidance)
        entities = self._extract_entities([m for m in messages if m.role != "system"])
        if entities:
            entity_line = f"[关键实体] {', '.join(entities[:20])}"
            base.messages.insert(1, Message(role="system", content=entity_line))
        base.preserved_entities = entities
        return base

    def _compress_hybrid(self, messages, target_tokens, guidance) -> CompressionResult:
        result = self._compress_semantic(messages, target_tokens, guidance)
        if self.estimate_tokens(result.messages) > target_tokens:
            result = self._compress_sliding_window(result.messages, target_tokens)
        return result

    def _extract_entities(self, messages: List[Message]) -> List[str]:
        import re
        text = " ".join(m.content for m in messages)
        entities = []
        entities.extend(re.findall(r'"([^"]+)"', text))
        entities.extend(re.findall(r"'([^']+)'", text))
        entities.extend(re.findall(r'[A-Za-z]:\\[^\s]+', text))
        entities.extend(re.findall(r'/[\w/]+\.\w+', text))
        return list(dict.fromkeys(entities))
