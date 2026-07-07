"""v6/runtime/engines/planner.py — Planner Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，演示 Planner 通过 EngineManager 编排 LLM / Tool。
未来职责：任务规划、阶段拆分、多 Engine 编排。

注意：Planner 通过构造函数注入 EngineManager，不通过 RuntimeContext 反向依赖 Runtime。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.base import BaseEngine
from v6.runtime.result import RuntimeResult

if TYPE_CHECKING:
    from v6.runtime.engine_manager import EngineManager


class PlannerEngine(BaseEngine):
    """Planner Engine：负责任务规划与 Engine 编排。"""

    name = "planner"
    capabilities = ["orchestration"]

    def __init__(self, manager: Optional["EngineManager"] = None) -> None:
        super().__init__()
        self._manager = manager

    def execute(self, ctx: RuntimeContext) -> Any:
        """占位实现：编排 LLM 与 Tool，验证 Runtime Kernel 链路。"""
        self._state = EngineState.RUNNING
        try:
            if self._manager is None:
                return self._placeholder_result(ctx)

            # 规划阶段：先调用 LLM 生成计划（占位）
            ctx.request = {"phase": "plan", "input": ctx.request}
            llm_result = self._manager.execute("llm", ctx)

            # 执行阶段：调用 Tool（占位）
            ctx.request = {"phase": "execute", "plan": llm_result}
            tool_result = self._manager.execute("tool", ctx)

            result = RuntimeResult(status="placeholder")
            result.extra.update(
                {
                    "engine": self.name,
                    "llm": llm_result,
                    "tool": tool_result,
                }
            )
            return result
        finally:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.READY
