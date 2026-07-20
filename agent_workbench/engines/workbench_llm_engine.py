"""agent_workbench/engines/workbench_llm_engine.py — Workbench LLM Engine。

职责：
- 继承 BaseEngine，通过 RuntimeContext 与 Runtime 交互。
- 调用 ModelModule 的 provider 生成回复。
- 不直接依赖具体 LLM 实现。
"""
from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from v6.runtime.engine_state import EngineState
from v6.runtime.engines.base import BaseEngine
from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.result import RuntimeResult

if TYPE_CHECKING:
    from v6.runtime.context import RuntimeContext
    from agent_workbench.runtime.modules.model_module import ModelModule


class WorkbenchLLMEngine(BaseEngine):
    """Workbench 专用 LLM Engine。"""

    name = "llm"
    capabilities = ["text_generation", "image_generation"]

    def __init__(self, model_module: "ModelModule") -> None:
        super().__init__()
        self._model_module = model_module

    def execute(self, ctx: "RuntimeContext") -> Any:
        """使用 ModelModule 流式生成回复，并通过 EventBus 推送分层 Trace 事件。"""
        self._state = EngineState.RUNNING
        execution_start = time.time()
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

            self._emit(
                RuntimeEventType.EXECUTION_STARTED,
                {"engine": self.name, "capability": "text_generation"},
                ctx,
            )

            provider_info = self._model_module.get_active_provider_info()
            provider_info.setdefault("service", "chat.completions")
            self._emit(
                RuntimeEventType.PROVIDER_SELECTED,
                provider_info,
                ctx,
            )

            messages = [{"role": m.role, "content": m.content} for m in ctx.messages]

            # 合并 Session 历史消息（多轮对话上下文）
            session_history = ctx.metadata.get("session_history", [])
            if session_history:
                history_messages = [
                    {"role": h["role"], "content": h["content"]}
                    for h in session_history
                    if h.get("role") and h.get("content")
                ]
                # 去重：历史消息 + 当前消息（避免重复）
                seen = {json.dumps(m, sort_keys=True, ensure_ascii=False) for m in history_messages}
                current = [m for m in messages if json.dumps(m, sort_keys=True, ensure_ascii=False) not in seen]
                messages = history_messages + current

            request_metadata = {
                "messages_count": len(messages),
                "tools": [],
                "system": None,
                "temperature": self._model_module._sampling.get("temperature", 0.7),
                "max_tokens": self._model_module._sampling.get("max_tokens", 2048),
                "stream": True,
                "json_mode": False,
                "reasoning": False,
            }
            self._emit(
                RuntimeEventType.REQUEST_SENT,
                request_metadata,
                ctx,
            )

            response_parts: list[str] = []
            self._emit(RuntimeEventType.AI_START, {"phase": ""}, ctx)

            first_token = True
            sequence = 0
            for chunk in self._model_module.chat_stream(messages):
                sequence += 1
                now = time.time()
                if first_token:
                    self._emit(
                        RuntimeEventType.FIRST_TOKEN,
                        {"elapsed_ms": (now - execution_start) * 1000},
                        ctx,
                    )
                    first_token = False
                response_parts.append(chunk)
                self._emit(
                    RuntimeEventType.AI_CHUNK,
                    {"text": chunk, "phase": ""},
                    ctx,
                )
                self._emit(
                    RuntimeEventType.CHUNK_RECEIVED,
                    {"sequence": sequence, "chunk_length": len(chunk)},
                    ctx,
                )

            response = "".join(response_parts)
            self._emit(RuntimeEventType.STREAM_FINISHED, {"chunks": sequence}, ctx)
            self._emit(RuntimeEventType.AI_END, {"response": response}, ctx)

            ctx.add_message("assistant", response)
            ctx.result.status = "completed"
            ctx.result.extra["response"] = response

            self._emit(
                RuntimeEventType.EXECUTION_FINISHED,
                {"status": "completed", "response_length": len(response)},
                ctx,
            )
            self._emit(
                RuntimeEventType.ENGINE_COMPLETED,
                {"status": "completed", "response": response},
                ctx,
            )
            return RuntimeResult(status="completed", answer=response)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            ctx.result.set_error(error_msg)
            ctx.result.extra["error_type"] = type(exc).__name__
            ctx.result.extra["error_message"] = str(exc)
            self._emit(
                RuntimeEventType.EXECUTION_FINISHED,
                {"status": "failed", "error": error_msg},
                ctx,
            )
            self._emit(RuntimeEventType.ENGINE_FAILED, {"error": error_msg}, ctx)
            raise
        finally:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.READY
