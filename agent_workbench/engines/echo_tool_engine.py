"""agent_workbench/engines/echo_tool_engine.py — 本地占位 Tool Engine。

设计约束：
- 仅用于 V6.8.0-alpha Baseline Validation，验证 Framework Core 能否承载 Tool 调用链路。
- 不引入 MCP / 外部工具注册表。
- 属于 agent_workbench 产品层，不属于 v6-core / v6-service。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.base import BaseEngine
from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.result import RuntimeResult


class EchoToolEngine(BaseEngine):
    """占位 Tool Engine：根据 ctx.request 执行一个本地模拟工具。"""

    name = "tool"
    capabilities = ["tool_execution"]

    def execute(self, ctx: RuntimeContext) -> Any:
        """执行 ctx.request 中指定的工具。"""
        self._state = EngineState.RUNNING
        self._emit(RuntimeEventType.ENGINE_STARTED, {}, ctx)
        try:
            tool_request = ctx.metadata.get("tool_request") or ctx.request or {}
            tool_name = tool_request.get("tool", "echo")
            args = tool_request.get("args", {})
            ctx.trace.add(
                node=f"engine:{self.name}",
                action=TraceEvent.ENGINE_INPUT_READ,
                phase=ctx.phase,
                payload={"tool": tool_name, "args": args},
            )

            result = self._run_tool(tool_name, args)
            ctx.result.status = "completed"
            ctx.result.extra["tool_result"] = result

            self._emit(
                RuntimeEventType.ENGINE_COMPLETED,
                {"status": "completed", "tool": tool_name, "result": result},
                ctx,
            )
            return RuntimeResult(status="completed", extra={"tool": tool_name, "result": result})
        except Exception as exc:
            self._emit(RuntimeEventType.ENGINE_FAILED, {"error": str(exc)}, ctx)
            raise
        finally:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.READY

    @staticmethod
    def _run_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
        """本地模拟工具执行。"""
        if name == "get_time":
            return {"time": datetime.now().isoformat()}
        if name == "echo":
            return {"echo": args.get("text", "")}
        return {"error": f"unknown tool: {name}"}
