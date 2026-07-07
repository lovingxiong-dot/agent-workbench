"""agent_workbench/adapter.py — agent_workbench 专用的 Runtime Adapter。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 封装 LocalRuntimeAdapter，并将 UI 提交的任务转发给 AgentRuntime.orchestrate()，
  从而驱动 Orchestrator → PlannerLoop → Engine 的完整链路。
- 如果直接调用 AgentRuntime.submit()，会走 _echo_handler，不会经过 Orchestrator。
"""
from __future__ import annotations

from typing import Callable

from v6.runtime.adapter import LocalRuntimeAdapter
from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.runtime import AgentRuntime
from v6.runtime.task import Task


class DemoRuntimeAdapter(LocalRuntimeAdapter):
    """Demo Agent Runtime Adapter：使用 Orchestrator 驱动任务生命周期。"""

    def submit(self, ctx: RuntimeContext) -> str:
        """提交 RuntimeContext 到 Runtime，通过 Orchestrator 编排生命周期。"""
        from v6.runtime.enums import TraceEvent

        ctx.trace.add(
            node="adapter",
            action=TraceEvent.ADAPTER_SUBMIT,
            phase=ctx.phase,
            payload={"task_id": ctx.task_id, "session_id": ctx.session_id},
        )
        task = Task(
            task_id=ctx.task_id,
            session_id=ctx.session_id,
            type="chat",
            payload={"ctx": ctx},
        )
        return self._runtime.orchestrate(task)

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        """订阅 Runtime 事件。"""
        self._runtime.subscribe(event_type, callback)
