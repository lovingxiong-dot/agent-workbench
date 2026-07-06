"""v6/runtime/engines/base.py — Engine 基础契约。

设计来源：V6.5 Runtime Foundation Layer Step 4。

核心原则：
- BaseEngine 提供统一状态机与默认生命周期实现，所有业务 Engine 继承它。
- Engine 空壳阶段不接入 OpenAI / LangChain / MCP / 向量库等具体实现。
- execute() 返回 RuntimeResult placeholder，验证 Runtime Kernel 链路。
"""
from __future__ import annotations

from typing import Any

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.result import RuntimeResult


class BaseEngine:
    """Engine 抽象基类。

    子类只需设置 `name` 并可选重写生命周期/执行方法。
    """

    name: str = "base"

    def __init__(self) -> None:
        self._state = EngineState.CREATED

    @property
    def state(self) -> EngineState:
        """Engine 当前生命周期状态。"""
        return self._state

    def load(self) -> None:
        """加载 Engine 资源。子类可重写。"""
        self._state = EngineState.LOADED

    def initialize(self, ctx: RuntimeContext) -> None:
        """初始化 Engine。子类可重写。"""
        self._state = EngineState.READY

    def health_check(self) -> EngineState:
        """健康检查。默认返回当前状态。"""
        return self._state

    def execute(self, ctx: RuntimeContext) -> Any:
        """执行 Engine 任务。子类必须重写以提供业务能力。"""
        self._state = EngineState.RUNNING
        try:
            return self._placeholder_result(ctx)
        finally:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.READY

    def shutdown(self) -> None:
        """释放 Engine 资源。子类可重写。"""
        self._state = EngineState.STOPPED

    def _placeholder_result(self, ctx: RuntimeContext) -> RuntimeResult:
        """返回 placeholder RuntimeResult，用于 Runtime Kernel 骨架验证。"""
        result = RuntimeResult(status="placeholder")
        result.extra.update(
            {
                "engine": self.name,
                "request_type": type(ctx.request).__name__ if ctx.request is not None else None,
            }
        )
        return result
