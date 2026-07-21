"""
Inference Engine — LLM 调用、流式处理、重试与降级策略

实现 IInferenceEngine 接口，封装 LLMRegistry 进行实际的 LLM 调用，
支持重试退避、模型降级、流式取消和指标上报。
"""
import asyncio
import time
from typing import AsyncIterator, List, Optional

from .interfaces import IInferenceEngine, Message, InferenceMetrics, TokenUsage

# 默认配置
_DEFAULT_RETRY_COUNT = 2
_DEFAULT_RETRY_BACKOFF_BASE = 2.0
_DEFAULT_FALLBACK_MODEL = None  # 由策略引擎决定


class InferenceEngine(IInferenceEngine):
    """推理引擎

    封装 LLMRegistry，提供：
    - 非流式调用（invoke）：带可配置重试 + 指数退避 + 模型降级
    - 流式调用（stream）：支持 cancel_event 中途取消 + 指标采集
    - 指标上报（report_metrics）：写入 MetricsEngine 并更新模型权重
    """

    def __init__(self, policy_engine=None, metrics_engine=None, llm_registry=None):
        self.policy = policy_engine
        self.metrics = metrics_engine
        self.registry = llm_registry

    # ── IInferenceEngine 实现 ───────────────────────

    async def invoke(
        self,
        messages: List[Message],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 90.0,
        cancel_event=None,
    ) -> tuple[str, InferenceMetrics]:
        """非流式调用，带重试和降级

        重试策略：
        1. 从 policy_engine 获取 retry_count 和 backoff_base
        2. 每次失败后指数退避
        3. 全部重试耗尽后降级到 fallback model（若配置）
        """
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
                result = await asyncio.wait_for(
                    llm.ainvoke(lc_messages), timeout=timeout
                )
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

            # 指数退避
            if attempt < retry_count:
                delay = backoff_base ** attempt
                await asyncio.sleep(delay)

        # 全部重试耗尽，尝试降级
        fallback = self._get_fallback_model(model_id)
        if fallback and fallback != model_id:
            try:
                llm = self._get_llm_instance(fallback, temperature, max_tokens, timeout)
                lc_messages = [m.to_langchain() for m in messages]
                result = await asyncio.wait_for(
                    llm.ainvoke(lc_messages), timeout=timeout
                )
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

        # 彻底失败
        elapsed_ms = int((time.monotonic() - start) * 1000)
        metrics = InferenceMetrics(
            model_id=model_id,
            success=False,
            error_code=last_error or "all_retries_exhausted",
            total_ms=elapsed_ms,
        )
        self.report_metrics(metrics)
        return ("", metrics)

    async def stream(
        self,
        messages: List[Message],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 90.0,
        cancel_event=None,
    ) -> AsyncIterator[str]:
        """流式生成，支持取消和指标采集

        cancel_event 在每次 chunk 产出前轮询，一旦置位即停止产出。
        """

        async def _generator():
            start = time.monotonic()
            ttft_recorded = False
            ttft_ms = 0
            input_tokens = 0
            output_tokens = 0

            try:
                llm = self._get_llm_instance(model_id, temperature, max_tokens, timeout)
                lc_messages = [m.to_langchain() for m in messages]
                stream_task = asyncio.ensure_future(
                    self._collect_chunks(llm.astream(lc_messages), cancel_event, timeout)
                )

                while True:
                    if cancel_event and cancel_event.is_set():
                        stream_task.cancel()
                        break

                    try:
                        done, _ = await asyncio.wait(
                            [stream_task], timeout=0.1
                        )
                        if done:
                            chunks = stream_task.result()
                            for chunk in chunks:
                                if cancel_event and cancel_event.is_set():
                                    break
                                yield chunk
                            break
                    except asyncio.CancelledError:
                        break

                total_ms = int((time.monotonic() - start) * 1000)

                # 上报指标
                metrics = InferenceMetrics(
                    model_id=model_id,
                    success=not (cancel_event and cancel_event.is_set()),
                    error_code="cancelled" if (cancel_event and cancel_event.is_set()) else "",
                    ttft_ms=ttft_ms,
                    total_ms=total_ms,
                    token_usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
                )
                self.report_metrics(metrics)

            except Exception as e:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                metrics = InferenceMetrics(
                    model_id=model_id,
                    success=False,
                    error_code=str(e)[:200],
                    ttft_ms=ttft_ms,
                    total_ms=elapsed_ms,
                )
                self.report_metrics(metrics)
                # 不重新抛出，让消费者自然结束

        return _generator()

    def report_metrics(self, metrics: InferenceMetrics) -> None:
        """【闭环】上报推理指标到 MetricsEngine，更新模型权重"""
        if not self.metrics:
            return
        try:
            self.metrics.record("inference", "invoke_total_ms", metrics.total_ms,
                                {"model_id": metrics.model_id, "success": metrics.success})
            self.metrics.record("inference", "invoke_ttft_ms", metrics.ttft_ms,
                                {"model_id": metrics.model_id})
            self.metrics.record("inference", "invoke_input_tokens", metrics.token_usage.input_tokens,
                                {"model_id": metrics.model_id})
            self.metrics.record("inference", "invoke_output_tokens", metrics.token_usage.output_tokens,
                                {"model_id": metrics.model_id})
            self.metrics.record("inference", "invoke_success",
                                1 if metrics.success else 0,
                                {"model_id": metrics.model_id})
        except Exception:
            pass  # 指标上报失败不应阻塞主流程

    # ── 内部 ────────────────────────────────────────

    def _get_llm_instance(self, model_id: str, temperature: float,
                          max_tokens: Optional[int], timeout: float):
        """从 LLMRegistry 获取 LLM 实例并配置参数"""
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
        """从策略引擎读取重试次数"""
        if self.policy:
            try:
                return int(self.policy.get("inference.retry_count", _DEFAULT_RETRY_COUNT))
            except Exception:
                pass
        return _DEFAULT_RETRY_COUNT

    def _get_backoff_base(self) -> float:
        """从策略引擎读取退避基数"""
        if self.policy:
            try:
                return float(self.policy.get("inference.backoff_base", _DEFAULT_RETRY_BACKOFF_BASE))
            except Exception:
                pass
        return _DEFAULT_RETRY_BACKOFF_BASE

    def _get_fallback_model(self, model_id: str) -> Optional[str]:
        """从策略引擎读取降级模型"""
        if self.policy:
            try:
                return self.policy.get("inference.fallback_model", None)
            except Exception:
                pass
        return _DEFAULT_FALLBACK_MODEL

    @staticmethod
    def _extract_content(result) -> str:
        """从 LLM 返回结果中提取文本内容"""
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
        """从 LLM 返回结果中提取 token 用量"""
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

    @staticmethod
    async def _collect_chunks(stream, cancel_event, timeout: float) -> List[str]:
        """收集流式 chunk，支持取消"""
        chunks: List[str] = []
        try:
            async for chunk in stream:
                if cancel_event and cancel_event.is_set():
                    break
                text = ""
                if hasattr(chunk, "content"):
                    text = chunk.content or ""
                elif isinstance(chunk, dict):
                    text = chunk.get("content", "")
                elif isinstance(chunk, str):
                    text = chunk
                if text:
                    chunks.append(text)
        except Exception:
            pass
        return chunks
