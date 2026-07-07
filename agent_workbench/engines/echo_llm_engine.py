"""agent_workbench/engines/echo_llm_engine.py — 本地占位 LLM Engine。

设计约束：
- 仅用于 V6.8.0-alpha Baseline Validation，验证 Framework Core 能否承载 LLM 调用链路。
- 不引入 OpenAI / Gemini / 本地模型等真实推理依赖。
- 属于 agent_workbench 产品层，不属于 v6-core / v6-service。
"""
from __future__ import annotations

from typing import Any

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.base import BaseEngine
from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.result import RuntimeResult


class EchoLLMEngine(BaseEngine):
    """占位 LLM Engine：根据用户输入返回固定回声响应，模拟 text_generation 能力。"""

    name = "llm"
    capabilities = ["text_generation"]

    def execute(self, ctx: RuntimeContext) -> Any:
        """读取 ctx.messages 最后一条用户消息，返回回声回复。"""
        self._state = EngineState.RUNNING
        self._emit(RuntimeEventType.ENGINE_STARTED, {}, ctx)
        try:
            text = ""
            if ctx.messages:
                text = ctx.messages[-1].content
            ctx.trace.add(
                node=f"engine:{self.name}",
                action=TraceEvent.ENGINE_INPUT_READ,
                phase=ctx.phase,
                payload={"source": "ctx.messages", "length": len(text)},
            )

            response = self._generate(text)
            ctx.add_message("assistant", response)
            ctx.result.status = "completed"
            ctx.result.extra["response"] = response

            self._emit(
                RuntimeEventType.ENGINE_COMPLETED,
                {"status": "completed", "response": response},
                ctx,
            )
            return RuntimeResult(status="completed", answer=response)
        except Exception as exc:
            self._emit(RuntimeEventType.ENGINE_FAILED, {"error": str(exc)}, ctx)
            raise
        finally:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.READY

    @staticmethod
    def _generate(text: str) -> str:
        """占位生成逻辑：对已知关键词做简单分支，其余返回回声。"""
        lowered = text.lower().strip()
        if not lowered:
            return "你好，我是 demo agent，请输入内容。"
        if "time" in lowered or "时间" in lowered:
            from datetime import datetime
            return f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if "hello" in lowered or "你好" in lowered:
            return "你好！我是 V6 demo agent，Framework Core Baseline Validation 通过。"
        return f"收到：{text.replace(chr(10), ' ')}"
