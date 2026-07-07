"""v6/runtime/engine_manager.py — Engine 生命周期管理器。

设计来源：V6.5 Runtime Foundation Layer Step 3。

核心原则：
- EngineManager 不实现业务，只管理 Engine 生命周期与调度入口。
- Engine 必须实现 `v6.runtime.engines.protocol.Engine` 协议。
- Engine 有独立状态机（EngineState），与 RuntimeState 分离。
- EngineManager.execute(name, ctx) 是 Runtime 调用 Engine 的统一入口：
  将请求写入 ctx.request，自动记录 TraceStep，调用 engine.execute(ctx)。
- EngineDescriptor 承载 Engine 元数据与依赖关系，为 Plugin Registry / Marketplace 预留扩展点。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.protocol import Engine, EngineDescriptor, EngineNotReadyError
from v6.runtime.enums import TraceEvent
from v6.runtime.trace import RuntimeTrace

if TYPE_CHECKING:
    from v6.runtime.event_bus import EventBus


class EngineManager:
    """Engine 生命周期管理器。

    维护 Engine 注册表、描述符与状态机，提供统一执行入口。
    若注入 EventBus，会把 EventBus 传给支持 `set_event_bus` 的 Engine，
    使 Engine 通过事件总线通信，而不是直接调用 Trace 或其他 Engine。
    """

    def __init__(
        self,
        trace: Optional[RuntimeTrace] = None,
        event_bus: Optional["EventBus"] = None,
    ) -> None:
        self._engines: Dict[str, Engine] = {}
        self._descriptors: Dict[str, EngineDescriptor] = {}
        self._states: Dict[str, EngineState] = {}
        self._trace: Optional[RuntimeTrace] = trace
        self._event_bus: Optional["EventBus"] = event_bus

    def set_trace(self, trace: Optional[RuntimeTrace]) -> None:
        """设置用于记录 Engine 执行轨迹的 RuntimeTrace。"""
        self._trace = trace

    def set_event_bus(self, event_bus: Optional["EventBus"]) -> None:
        """设置 Runtime Event Bus，并重新注入给所有已注册 Engine。"""
        self._event_bus = event_bus
        for engine in self._engines.values():
            self._wire_event_bus(engine)

    def _wire_event_bus(self, engine: Engine) -> None:
        """如果 Engine 支持，注入 EventBus。"""
        if self._event_bus is None:
            return
        setter = getattr(engine, "set_event_bus", None)
        if callable(setter):
            setter(self._event_bus)

    # ─────────────────────────────────────────────────────────
    # 注册与查询
    # ─────────────────────────────────────────────────────────

    def register(self, engine: Engine) -> None:
        """注册一个 Engine 实例。"""
        name = engine.name
        self._engines[name] = engine
        self._descriptors[name] = EngineDescriptor(
            name=name,
            instance=engine,
        )
        self._states[name] = EngineState.CREATED
        self._wire_event_bus(engine)

    def get(self, name: str) -> Optional[Engine]:
        """获取已注册的 Engine 实例。"""
        return self._engines.get(name)

    def has(self, name: str) -> bool:
        """判断 Engine 是否已注册。"""
        return name in self._engines

    def names(self) -> List[str]:
        """返回所有已注册 Engine 名称。"""
        return list(self._engines.keys())

    def descriptor(self, name: str) -> Optional[EngineDescriptor]:
        """返回 Engine 描述符。"""
        return self._descriptors.get(name)

    def state(self, name: str) -> Optional[EngineState]:
        """返回 Engine 当前状态。"""
        return self._states.get(name)

    def states(self) -> Dict[str, EngineState]:
        """返回所有 Engine 状态快照。"""
        return dict(self._states)

    def unregister(self, name: str) -> bool:
        """注销 Engine。"""
        if name in self._engines:
            del self._engines[name]
            del self._descriptors[name]
            del self._states[name]
            return True
        return False

    def clear(self) -> None:
        """清空所有 Engine。"""
        self._engines.clear()
        self._descriptors.clear()
        self._states.clear()

    # ─────────────────────────────────────────────────────────
    # 生命周期
    # ─────────────────────────────────────────────────────────

    def load(self, name: str) -> None:
        """加载 Engine 资源。"""
        engine = self._get_or_raise(name)
        self._transition(name, EngineState.LOADING)
        try:
            engine.load()
            self._transition(name, EngineState.LOADED)
        except Exception:
            self._transition(name, EngineState.ERROR)
            raise

    def initialize(self, name: str, ctx: RuntimeContext) -> None:
        """初始化 Engine，完成后进入 READY。"""
        engine = self._get_or_raise(name)
        self._ensure_state(name, {EngineState.LOADED, EngineState.STOPPED})
        self._transition(name, EngineState.INITIALIZING)
        try:
            engine.initialize(ctx)
            self._transition(name, EngineState.READY)
        except Exception:
            self._transition(name, EngineState.ERROR)
            raise

    def initialize_all(self, ctx: RuntimeContext) -> None:
        """加载并初始化所有已注册 Engine。"""
        for name in self.names():
            self.load(name)
            self.initialize(name, ctx)

    def health_check(self, name: str) -> EngineState:
        """执行 Engine 健康检查并更新状态。"""
        engine = self._get_or_raise(name)
        state = engine.health_check()
        self._transition(name, state)
        return state

    def health_check_all(self) -> Dict[str, EngineState]:
        """健康检查所有 Engine。"""
        return {name: self.health_check(name) for name in self.names()}

    def shutdown(self, name: str) -> None:
        """关闭 Engine。"""
        engine = self._get_or_raise(name)
        self._transition(name, EngineState.STOPPING)
        try:
            engine.shutdown()
            self._transition(name, EngineState.STOPPED)
        except Exception:
            self._transition(name, EngineState.ERROR)
            raise

    def shutdown_all(self) -> None:
        """关闭所有 Engine。"""
        for name in list(self.names()):
            self.shutdown(name)

    # ─────────────────────────────────────────────────────────
    # 执行入口
    # ─────────────────────────────────────────────────────────

    def execute(
        self,
        name: str,
        ctx: RuntimeContext,
    ) -> Any:
        """调用 Engine 执行，并自动记录 TraceStep。

        Args:
            name: Engine 名称。
            ctx: 当前 RuntimeContext；EngineManager 会把 ctx 传给 Engine.execute(ctx)。
        """
        engine = self._get_or_raise(name)
        self._ensure_state(name, {EngineState.READY, EngineState.RUNNING})
        self._transition(name, EngineState.RUNNING)
        try:
            request_type = type(ctx.request).__name__ if ctx.request is not None else "None"
            if self._trace is not None:
                with self._trace.timed_step(
                    node=f"engine:{name}",
                    action=TraceEvent.ENGINE_START,
                    payload={"request_type": request_type},
                ):
                    result = engine.execute(ctx)
            else:
                result = engine.execute(ctx)
            return result
        except Exception:
            self._transition(name, EngineState.ERROR)
            raise
        finally:
            if self.state(name) == EngineState.RUNNING:
                self._transition(name, EngineState.READY)

    # ─────────────────────────────────────────────────────────
    # 内部辅助
    # ─────────────────────────────────────────────────────────

    def _get_or_raise(self, name: str) -> Engine:
        if name not in self._engines:
            raise KeyError(f"Engine not registered: {name}")
        return self._engines[name]

    def _transition(self, name: str, state: EngineState) -> None:
        self._states[name] = state
        desc = self._descriptors.get(name)
        if desc is not None:
            desc.state = state

    def _ensure_state(self, name: str, allowed: Set[EngineState]) -> None:
        state = self._states.get(name)
        if state not in allowed:
            raise EngineNotReadyError(name, state, list(allowed))
