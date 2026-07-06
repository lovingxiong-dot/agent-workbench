"""v6/runtime/engines/inference.py — InferenceEngine：LLM 调用、流式输出、重试降级。

设计来源：V4 agent_engine/engines/inference_engine.py（提取核心逻辑）。

职责：读取 ctx.messages / ctx.model / ctx.metadata，写回 ctx.messages 和
      ctx.metadata['response'] / ctx.metadata['inference_metrics']。
"""
from __future__ import annotations

import asyncio
import time
from typing import List, Optional

from v6.runtime.engines.interfaces import (
    ChatMessage,
    IInferenceEngine,
    InferenceMetrics,
    TokenUsage,
)


_DEFAULT_RETRY_COUNT = 2
_DEFAULT_RETRY_BACKOFF_BASE = 2.0
_DEFAULT_FALLBACK_MODEL: Optional[str] = None


class InferenceEngine(IInferenceEngine):
    """推理引擎：封装 LLMRegistry，提供 invoke / stream / 指标上报。"""

    def __init__(self, policy_engine=None, metrics_engine=None, llm_registry=None) -> None:
        self.policy = policy_engine
        self.metrics = metrics_engine
        self.registry = llm_registry

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """调用 LLM，把 assistant 消息追加到 ctx.messages。"""
        model_id = ctx.model or ctx.metadata.get("model", "")
        if not model_id:
            model_id = "deepseek-pro"

        temperature = ctx.metadata.get("temperature", 0.7)
        max_tokens = ctx.metadata.get("max_tokens")
        timeout = ctx.metadata.get("timeout", 90.0)
        cancel_event = ctx.metadata.get("cancel_event")

        content, metrics = await self.invoke(
            messages=ctx.messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            cancel_event=cancel_event,
        )

        if content:
            ctx.messages.append(ChatMessage(role="assistant", content=content))

        ctx.metadata["response"] = content
        ctx.metadata["inference_metrics"] = metrics
        return ctx

    async def invoke(
        self,
        messages: List[ChatMessage],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 90.0,
        cancel_event=None,
    ) -> tuple[str, InferenceMetrics]:
        """非流式调用，带重试和降级。"""
        start = time.monotonic()
        retry_count = self._get_retry_count()
        backoff_base = self._get_backoff_base()
        last_error: Optional[str] = None

        for attempt in range(retry_count + 1):
            if cancel_event and cancel_event.is_set():
                metrics = InferenceMetrics(
                    model_id=model_id,
                    success=False,
                    error_code="cancelled",
                    total_ms=int((time.monotonic() - start) * 1000),
                )
                return ("", metrics)

            try:
                llm = self._get_llm_instance(model_id, temperature, max_tokens, timeout)
                lc_messages = [m.to_langchain() for m in messages]
                result = await asyncio.wait_for(llm.ainvoke(lc_messages), timeout=timeout)
                content = self._extract_content(result)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                token_usage = self._extract_token_usage(result)

                metrics = InferenceMetrics(
                    model_id=model_id,
                    success=True,
                    total_ms=elapsed_ms,
                    token_usage=token_usage,
                )
                self.report_metrics(metrics)
                return (content, metrics)

            except asyncio.TimeoutError:
                last_error = "timeout"
            except asyncio.CancelledError:
                metrics = InferenceMetrics(
                    model_id=model_id,
                    success=False,
                    error_code="cancelled",
                    total_ms=int((time.monotonic() - start) * 1000),
                )
                return ("", metrics)
            except Exception as e:
                last_error = str(e)[:200]

            if attempt < retry_count:
                delay = backoff_base ** attempt
                await asyncio.sleep(delay)

        fallback = self._get_fallback_model(model_id)
        if fallback and fallback != model_id:
            try:
                llm = self._get_llm_instance(fallback, temperature, max_tokens, timeout)
                lc_messages = [m.to_langchain() for m in messages]
                result = await asyncio.wait_for(llm.ainvoke(lc_messages), timeout=timeout)
                content = self._extract_content(result)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                token_usage = self._extract_token_usage(result)

                metrics = InferenceMetrics(
                    model_id=fallback,
                    success=True,
                    total_ms=elapsed_ms,
                    token_usage=token_usage,
                )
                self.report_metrics(metrics)
                return (content, metrics)
            except Exception:
                pass

        elapsed_ms = int((time.monotonic() - start) * 1000)
        metrics = InferenceMetrics(
            model_id=model_id,
            success=False,
            error_code=last_error or "all_retries_exhausted",
            total_ms=elapsed_ms,
        )
        self.report_metrics(metrics)
        return ("", metrics)

    def report_metrics(self, metrics: InferenceMetrics) -> None:
        """【闭环】上报推理指标到 MetricsEngine。"""
        if not self.metrics:
            return
        try:
            self.metrics.record(
                "inference", "invoke_total_ms", metrics.total_ms,
                {"model_id": metrics.model_id, "success": metrics.success}
            )
            self.metrics.record(
                "inference", "invoke_ttft_ms", metrics.ttft_ms,
                {"model_id": metrics.model_id}
            )
            self.metrics.record(
                "inference", "invoke_input_tokens", metrics.token_usage.input_tokens,
                {"model_id": metrics.model_id}
            )
            self.metrics.record(
                "inference", "invoke_output_tokens", metrics.token_usage.output_tokens,
                {"model_id": metrics.model_id}
            )
            self.metrics.record(
                "inference", "invoke_success",
                1 if metrics.success else 0,
                {"model_id": metrics.model_id}
            )
        except Exception:
            pass

    def _get_llm_instance(
        self,
        model_id: str,
        temperature: float,
        max_tokens: Optional[int],
        timeout: float,
    ):
        """从 LLMRegistry 获取 LLM 实例并配置参数。"""
        if self.registry is None:
            raise RuntimeError("LLMRegistry not configured")
        llm = self.registry.get_llm(model_id)
        if temperature is not None:
            llm.temperature = temperature
        if max_tokens is not None:
            llm.max_tokens = max_tokens
        if timeout is not None:
            llm.request_timeout = timeout
        return llm

    def _get_retry_count(self) -> int:
        if self.policy:
            try:
                return int(self.policy.get("inference.retry_count", _DEFAULT_RETRY_COUNT))
            except Exception:
                pass
        return _DEFAULT_RETRY_COUNT

    def _get_backoff_base(self) -> float:
        if self.policy:
            try:
                return float(self.policy.get("inference.backoff_base", _DEFAULT_RETRY_BACKOFF_BASE))
            except Exception:
                pass
        return _DEFAULT_RETRY_BACKOFF_BASE

    def _get_fallback_model(self, model_id: str) -> Optional[str]:
        if self.policy:
            try:
                return self.policy.get("inference.fallback_model", None)
            except Exception:
                pass
        return _DEFAULT_FALLBACK_MODEL

    @staticmethod
    def _extract_content(result) -> str:
        """从 LLM 返回结果中提取文本内容。"""
        try:
            if hasattr(result, "content"):
                return result.content or ""
            if isinstance(result, dict):
                return result.get("content", "")
            return str(result)
        except Exception:
            return ""

    @staticmethod
    def _extract_token_usage(result) -> TokenUsage:
        """从 LLM 返回结果中提取 token 用量。"""
        try:
            if hasattr(result, "response_metadata"):
                meta = result.response_metadata or {}
                usage = meta.get("token_usage", {}) or {}
                return TokenUsage(
                    input_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    output_tokens=int(usage.get("completion_tokens", 0) or 0),
                )
            if hasattr(result, "usage_metadata"):
                meta = result.usage_metadata or {}
                return TokenUsage(
                    input_tokens=int(meta.get("input_tokens", 0) or 0),
                    output_tokens=int(meta.get("output_tokens", 0) or 0),
                )
        except Exception:
            pass
        return TokenUsage()
