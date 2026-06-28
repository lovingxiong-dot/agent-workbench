"""
MetricsCollector — 轻量级单轮/会话级指标收集器

设计原则：
- 不依赖 Qt，可在 AgentWorker 线程内安全使用
- 所有计时基于 time.perf_counter()，不创建额外线程
- 仅做运行时统计，持久化由调用方负责
- 异常安全：任何指标计算失败都不应中断主流程
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TurnMetrics:
    """单次 LLM 推理回合的指标"""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    ttft_ms: int = 0       # Time To First Token (ms)
    total_ms: int = 0      # 总生成时间 (ms)

    def format_brief(self) -> str:
        """用户指定的气泡下方显示格式：33546tok/34ms"""
        return f"{self.total_tokens}tok/{self.total_ms}ms"

    def format_detail(self) -> str:
        """日志中输出的详细统计信息"""
        return (
            f"TTFT={self.ttft_ms}ms | "
            f"Total={self.total_ms}ms | "
            f"Tokens={self.input_tokens}+{self.output_tokens}={self.total_tokens}"
        )


class MetricsCollector:
    """收集单次请求及当前会话累计的 token/时间指标"""

    def __init__(self):
        self._session_tokens = 0
        self._session_ms = 0
        self._turn_count = 0
        self._start_at = 0.0
        self._first_token_at = 0.0

    # ── 单轮生命周期 ─────────────────────────────────────

    def start_turn(self) -> None:
        """在发起 LLM 调用前调用"""
        self._start_at = time.perf_counter()
        self._first_token_at = 0.0

    def mark_first_token(self) -> None:
        """在收到第一个流式 chunk 时调用"""
        if not self._first_token_at and self._start_at:
            self._first_token_at = time.perf_counter()

    def finish_turn(self, input_tokens: int = 0, output_tokens: int = 0) -> TurnMetrics:
        """在收到最终 response 后调用，返回本次指标"""
        now = time.perf_counter()
        total_ms = int((now - self._start_at) * 1000) if self._start_at else 0
        if self._first_token_at and self._start_at:
            ttft_ms = int((self._first_token_at - self._start_at) * 1000)
        else:
            # 非流式或首 token 未触发：总耗时即 TTFT
            ttft_ms = total_ms

        total_tokens = max(0, input_tokens) + max(0, output_tokens)
        metrics = TurnMetrics(
            input_tokens=max(0, input_tokens),
            output_tokens=max(0, output_tokens),
            total_tokens=total_tokens,
            ttft_ms=ttft_ms,
            total_ms=total_ms,
        )

        # 累计到当前会话
        self._session_tokens += total_tokens
        self._session_ms += total_ms
        self._turn_count += 1

        return metrics

    # ── 会话级统计 ───────────────────────────────────────

    def reset_session(self) -> None:
        """切换会话时调用"""
        self._session_tokens = 0
        self._session_ms = 0
        self._turn_count = 0
        self._start_at = 0.0
        self._first_token_at = 0.0

    def session_totals(self) -> dict:
        """返回当前会话累计指标"""
        return {
            "turns": self._turn_count,
            "tokens": self._session_tokens,
            "ms": self._session_ms,
        }

    # ── 静态格式化 ───────────────────────────────────────

    @staticmethod
    def format(metrics: TurnMetrics) -> str:
        """兼容外部直接格式化 TurnMetrics"""
        return metrics.format_brief()
