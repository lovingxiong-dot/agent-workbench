"""agent_workbench/engines/workbench_llm_engine.py — Workbench LLM Engine。

职责：
- 继承 BaseEngine，通过 RuntimeContext 与 Runtime 交互。
- 调用 ModelModule 的 provider 生成回复。
- 不直接依赖具体 LLM 实现。
"""
from __future__ import annotations

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
    capabilities = ["text_generation"]

    def __init__(self, model_module: "ModelModule") -> None:
        super().__init__()
        self._model_module = model_module

    def execute(self, ctx: "RuntimeContext") -> Any:
        """使用 ModelModule 生成回复。"""
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

            messages = [{"role": m.role, "content": m.content} for m in ctx.messages]
            response = self._model_module.chat(messages)

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
