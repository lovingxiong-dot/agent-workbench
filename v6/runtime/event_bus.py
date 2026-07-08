"""v6/runtime/event_bus.py — Runtime 内部神经系统（communication backbone）。

职责：
- 为 Task → AgentRuntime → EngineManager → Engine/Service/Adapter 提供异步事件通信。
- 所有事件统一使用 `RuntimeEvent` Schema，携带 `task_id` / `source` / `trace_id` / `phase`，
  确保 Trace 可关联、可回放。
- 提供按 `task_id` 路由的 Trace Hook，使 RuntimeTrace 成为事件的订阅者，而非由 Engine 直接调用。
- 保留原有同步 `publish` / `emit` API，同时新增异步 `dispatch` API 供 Runtime 内部使用。

设计来源：V6.5 Runtime Foundation Layer Step 5.1。
"""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable

from v6.runtime.enums import TRACE_EVENT_LEVEL, TRACE_EVENT_PARENT_LEVEL, TraceEvent

if TYPE_CHECKING:
    from v6.runtime.trace import RuntimeTrace


class RuntimeEventType(str, Enum):
    """Runtime 标准事件类型。

    使用 str 枚举保证与现有字符串 API 兼容，同时提供统一命名。
    """

    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    CAPABILITY_RESOLVED = "capability.resolved"

    MANAGER_INTENT_CLASSIFIED = "manager.intent.classified"
    MANAGER_CAPABILITY_SELECTED = "manager.capability.selected"
    MANAGER_CHAIN_STEP_STARTED = "manager.chain.step.started"

    CAPABILITY_CHAIN_STEP_STARTED = "capability.chain.step.started"

    DECISION_PLANNED = "decision.planned"

    ENGINE_SELECTED = "engine.selected"
    ENGINE_STARTED = "engine.started"
    ENGINE_COMPLETED = "engine.completed"
    ENGINE_FAILED = "engine.failed"

    # Provider / Service / Model 选择事件为可选；不同 Engine 按需发射，Trace Viewer 自动处理缺失。
    PROVIDER_SELECTED = "provider.selected"
    SERVICE_SELECTED = "service.selected"
    MODEL_SELECTED = "model.selected"

    REQUEST_SENT = "request.sent"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_PROGRESS = "execution.progress"
    EXECUTION_FINISHED = "execution.finished"

    FIRST_TOKEN = "first.token"
    CHUNK_RECEIVED = "chunk.received"
    STREAM_FINISHED = "stream.finished"

    SERVICE_STARTED_LEGACY = "service.started"
    SERVICE_COMPLETED = "service.completed"
    SERVICE_FAILED = "service.failed"

    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    ADAPTER_RECEIVED = "adapter.received"
    ADAPTER_SENT = "adapter.sent"

    USER_MESSAGE = "user_message"
    AI_START = "ai_start"
    AI_CHUNK = "ai_chunk"
    AI_END = "ai_end"
    ERROR = "error"


# RuntimeEventType -> TraceEvent 映射。
# 未映射的事件不会被 Trace Hook 自动写入 RuntimeTrace（仍可由调用方显式写入）。
_RUNTIME_EVENT_TO_TRACE: dict[str, TraceEvent] = {
    RuntimeEventType.TASK_STARTED: TraceEvent.TASK_START,
    RuntimeEventType.TASK_COMPLETED: TraceEvent.TASK_FINISH,
    RuntimeEventType.TASK_FAILED: TraceEvent.TASK_ERROR,
    RuntimeEventType.CAPABILITY_RESOLVED: TraceEvent.CAPABILITY_RESOLVED,
    RuntimeEventType.ENGINE_SELECTED: TraceEvent.ENGINE_SELECTED,
    RuntimeEventType.ENGINE_STARTED: TraceEvent.ENGINE_START,
    RuntimeEventType.ENGINE_COMPLETED: TraceEvent.ENGINE_END,
    RuntimeEventType.ENGINE_FAILED: TraceEvent.ENGINE_END,
    RuntimeEventType.SERVICE_SELECTED: TraceEvent.SERVICE_SELECTED,
    RuntimeEventType.PROVIDER_SELECTED: TraceEvent.PROVIDER_SELECTED,
    RuntimeEventType.MODEL_SELECTED: TraceEvent.MODEL_SELECTED,
    RuntimeEventType.REQUEST_SENT: TraceEvent.REQUEST_SENT,
    RuntimeEventType.EXECUTION_STARTED: TraceEvent.EXECUTION_STARTED,
    RuntimeEventType.EXECUTION_PROGRESS: TraceEvent.EXECUTION_PROGRESS,
    RuntimeEventType.EXECUTION_FINISHED: TraceEvent.EXECUTION_FINISHED,
    RuntimeEventType.FIRST_TOKEN: TraceEvent.FIRST_TOKEN,
    RuntimeEventType.CHUNK_RECEIVED: TraceEvent.CHUNK_RECEIVED,
    RuntimeEventType.STREAM_FINISHED: TraceEvent.STREAM_FINISHED,
}


@dataclass
class RuntimeEvent:
    """运行时事件对象。

    字段说明：
    - type: 事件类型，建议使用 RuntimeEventType 枚举值。
    - payload: 事件载荷，必须是可序列化的 dict。
    - task_id: 所属 Runtime Task，用于 Trace 关联与路由。
    - source: 事件来源，例如 "engine:llm" / "service:chat" / "adapter:ui"。
    - trace_id: 可选 Trace 关联 ID。
    - phase: 可选 Runtime Phase，例如 "plan" / "inference" / "tool"。
    - timestamp: 事件发生时间戳。
    """

    type: str
    payload: dict
    task_id: str
    source: str = ""
    trace_id: str = ""
    phase: str = ""
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Runtime Event Bus：异步事件总线，支持多订阅者、异步/同步回调、Trace Hook。"""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._queue: asyncio.Queue[RuntimeEvent | None] | None = None
        self._subscribers: dict[str, list[Callable[[RuntimeEvent], None]]] = {}
        self._trace_hooks: dict[str, "RuntimeTrace"] = {}
        # 每个 task_id 维护一个层级 -> step_id 映射，用于 Trace Hook 自动推断 parent_id。
        self._trace_contexts: dict[str, dict[str, str]] = {}
        self._running = False
        self._lock = threading.Lock()
        self._ready = threading.Event()

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        """订阅指定类型事件。"""
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> bool:
        """取消订阅；返回是否成功移除。"""
        with self._lock:
            listeners = self._subscribers.get(event_type, [])
            if callback in listeners:
                listeners.remove(callback)
                return True
            return False

    def add_trace_hook(self, task_id: str, trace: "RuntimeTrace") -> None:
        """为指定 task_id 注册 Trace Hook。

        事件分发时，若事件携带相同 task_id，会自动写入该 RuntimeTrace。
        """  # noqa: D205
        with self._lock:
            self._trace_hooks[task_id] = trace

    def remove_trace_hook(self, task_id: str) -> bool:
        """移除指定 task_id 的 Trace Hook。"""
        with self._lock:
            return self._trace_hooks.pop(task_id, None) is not None

    def publish(
        self,
        event_type: str,
        payload: dict,
        task_id: str = "",
        source: str = "",
        trace_id: str = "",
        phase: str = "",
    ) -> None:
        """同步发布事件；若总线未启动则静默丢弃。

        保留原有 API 签名并扩展可选字段，供 Engine / Service / Adapter 使用。
        """  # noqa: D205
        with self._lock:
            if not self._running:
                return
            loop = self._loop
            queue = self._queue
        if not loop or not queue:
            return
        event = RuntimeEvent(
            type=event_type,
            payload=payload,
            task_id=task_id,
            source=source,
            trace_id=trace_id,
            phase=phase,
        )
        # Trace Hook 同步写入，保证事件顺序与发布顺序一致，避免异步队列导致的乱序/丢失。
        self._write_trace_hook(event)
        loop.call_soon_threadsafe(queue.put_nowait, event)

    emit = publish  # 兼容旧调用

    async def dispatch(self, event: RuntimeEvent) -> None:
        """异步分发单个 RuntimeEvent；调用方可 await 等待分发完成。

        适用于 Runtime 内部需要精确控制事件时机的场景。
        """  # noqa: D205
        await self._dispatch(event)

    def start(self) -> None:
        """启动事件分发线程，等待事件循环与队列就绪。"""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._ready.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        self._ready.wait(timeout=5.0)

    def stop(self) -> None:
        """停止事件分发线程。"""
        with self._lock:
            if not self._running:
                return
            self._running = False
            loop = self._loop
            queue = self._queue
        if loop and queue:
            loop.call_soon_threadsafe(queue.put_nowait, None)
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._loop = None
        self._queue = None
        self._trace_hooks.clear()
        self._ready.clear()

    def _run_loop(self) -> None:
        """在后台线程中运行 asyncio 事件循环。"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._queue = asyncio.Queue()
        self._ready.set()
        try:
            self._loop.run_until_complete(self._dispatch_loop())
        finally:
            self._loop.close()

    async def _dispatch_loop(self) -> None:
        """持续从队列取出事件并分发给订阅者。"""
        while self._running:
            event = await self._queue.get()
            if event is None:
                break
            await self._dispatch(event)

    def _write_trace_hook(self, event: RuntimeEvent) -> None:
        """将事件同步写入对应 Trace Hook（publish 调用线程内执行）。"""
        with self._lock:
            trace = self._trace_hooks.get(event.task_id)
        if trace is None:
            return
        try:
            trace_action = _RUNTIME_EVENT_TO_TRACE.get(event.type)
            if trace_action is None:
                return
            level = TRACE_EVENT_LEVEL.get(trace_action, "runtime")
            parent_level = TRACE_EVENT_PARENT_LEVEL.get(level)
            context = self._trace_contexts.setdefault(event.task_id, {})
            parent_id = context.get(parent_level, "") if parent_level else ""
            status = event.payload.get("status", "success")
            if event.type == RuntimeEventType.ENGINE_FAILED.value:
                status = "failed"
            elif event.type == RuntimeEventType.TASK_FAILED.value:
                status = "failed"
            step = trace.add(
                phase=event.phase or level,
                node=event.source or "event_bus",
                action=trace_action,
                payload=event.payload,
                parent_id=parent_id,
                status=status,
            )
            context[level] = step.step_id
        except Exception:  # pragma: no cover - defensive
            traceback.print_exc()

    async def _dispatch(self, event: RuntimeEvent) -> None:
        """调用该事件类型的所有订阅者；Trace Hook 已在 publish 阶段同步写入。"""
        with self._lock:
            callbacks = list(self._subscribers.get(event.type, []))
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception:  # pragma: no cover - defensive
                traceback.print_exc()
