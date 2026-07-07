"""v6/runtime/engines/base.py — Engine 基础契约。

设计来源：V6.5 Runtime Foundation Layer Step 4。

核心原则：
- BaseEngine 提供统一状态机与默认生命周期实现，所有业务 Engine 继承它。
- Engine 空壳阶段不接入 OpenAI / LangChain / MCP / 向量库等具体实现。
- execute() 返回 RuntimeResult placeholder，验证 Runtime Kernel 链路。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.result import RuntimeResult

if TYPE_CHECKING:
    from v6.runtime.event_bus import EventBus


class BaseEngine:
    """Engine 抽象基类。

    子类只需设置 `name` 并可选重写生命周期/执行方法。
    若通过 `set_event_bus` 注入 EventBus，Engine 会在生命周期关键点发布标准事件，
    而不是直接调用 Trace 或其他 Engine。
    """

    name: str = "base"

    def __init__(self) -> None:
        self._state = EngineState.CREATED
        self._event_bus: Optional["EventBus"] = None

    @property
    def state(self) -> EngineState:
        """Engine 当前生命周期状态。"""
        return self._state

    def set_event_bus(self, event_bus: Optional["EventBus"]) -> None:
        """注入 Runtime Event Bus；Engine 通过它发布事件，不直接调用 Trace。"""
        self._event_bus = event_bus

    def _emit(
        self,
        event_type: str,
        payload: dict,
        ctx: RuntimeContext,
    ) -> None:
        """发布 RuntimeEvent；EventBus 未注入时静默跳过。"""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            event_type=event_type,
            payload=payload,
            task_id=ctx.task_id,
            source=f"engine:{self.name}",
            phase=ctx.phase,
        )

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
        self._emit(RuntimeEventType.ENGINE_STARTED, {}, ctx)
        try:
            result = self._placeholder_result(ctx)
            self._emit(
                RuntimeEventType.ENGINE_COMPLETED,
                {"status": result.status},
                ctx,
            )
            return result
        except Exception as exc:
            self._emit(
                RuntimeEventType.ENGINE_FAILED,
                {"error": str(exc)},
                ctx,
            )
            raise
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
