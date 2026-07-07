"""agent_workbench/engines/workbench_tool_engine.py — Workbench Tool Engine。

职责：
- 继承 BaseEngine，通过 RuntimeContext 与 Runtime 交互。
- 调用 ToolModule 的 ToolRegistry 执行工具。
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from v6.runtime.engine_state import EngineState
from v6.runtime.engines.base import BaseEngine
from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.result import RuntimeResult

if TYPE_CHECKING:
    from v6.runtime.context import RuntimeContext
    from agent_workbench.runtime.modules.tool_module import ToolModule


class WorkbenchToolEngine(BaseEngine):
    """Workbench 专用 Tool Engine。"""

    name = "tool"
    capabilities = ["tool_execution"]

    def __init__(self, tool_module: "ToolModule") -> None:
        super().__init__()
        self._tool_module = tool_module

    def execute(self, ctx: "RuntimeContext") -> Any:
        """执行工具调用。"""
        self._state = EngineState.RUNNING
        self._emit(RuntimeEventType.ENGINE_STARTED, {}, ctx)
        try:
            tool_request = ctx.metadata.get("tool_request") or {}
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

    def _run_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """本地工具执行。"""
        registry = self._tool_module.registry
        tool = registry.get(name)
        if tool is not None and tool.handler is not None and tool.enabled:
            return {"result": tool.handler(args)}

        # 内置默认实现
        if name == "get_time":
            return {"time": datetime.now().isoformat()}
        if name == "echo":
            return {"echo": args.get("text", "")}
        return {"error": f"unknown or disabled tool: {name}"}
