"""v6/runtime/event_bus.py — 异步事件总线。

使用独立线程运行 asyncio 事件循环，所有订阅者都在该线程被回调。
设计来源：docs/v6/SPEC.md 第 4 节。
"""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class RuntimeEvent:
    """运行时事件对象。"""

    type: str
    payload: dict
    task_id: str
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """异步事件总线：支持多订阅者、异步/同步回调。"""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._queue: asyncio.Queue[RuntimeEvent | None] | None = None
        self._subscribers: dict[str, list[Callable[[RuntimeEvent], None]]] = {}
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

    def publish(self, event_type: str, payload: dict, task_id: str = "") -> None:
        """发布事件；若总线未启动则静默丢弃。"""
        with self._lock:
            if not self._running:
                return
            loop = self._loop
            queue = self._queue
        if not loop or not queue:
            return
        event = RuntimeEvent(type=event_type, payload=payload, task_id=task_id)
        loop.call_soon_threadsafe(queue.put_nowait, event)

    emit = publish  # 兼容旧调用

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

    async def _dispatch(self, event: RuntimeEvent) -> None:
        """调用该事件类型的所有订阅者。"""
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
