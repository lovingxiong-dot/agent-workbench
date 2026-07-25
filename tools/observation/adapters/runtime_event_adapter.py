"""tools/observation/adapters/runtime_event_adapter.py — RuntimeEvent 流 Adapter。

约束：
- 仅通过现有 EventBus public API 收集事件
- 调用方负责管理 callback 生命周期
- 不修改 EventBus 内部状态
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, List, Optional

from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType


@dataclass
class RuntimeEventCapture:
    """轻量环形缓冲收集 RuntimeEvent（仅订阅者持有）。
    
    不属于 Metrics / Monitoring 类基础设施。
    仅为 Phase 3.12-A Observation 提供被动消费能力。
    """
    max_size: int = 10_000
    _events: Deque[RuntimeEvent] = None  # type: ignore[assignment]
    _task_filter: Optional[str] = None

    def __post_init__(self) -> None:
        # frozen=False dataclass 默认 mutable；显式初始化
        self._events = deque(maxlen=self.max_size)

    def set_task_filter(self, task_id: Optional[str]) -> None:
        """设置 task 过滤（None = 不过滤）。"""
        self._task_filter = task_id

    def callback(self, event: RuntimeEvent) -> None:
        """EventBus 订阅回调（用作 bus.subscribe() 的 handler）。

        不抛异常（订阅者抛异常会污染 EventBus dispatch loop）。
        """
        if self._task_filter is not None and event.task_id != self._task_filter:
            return
        self._events.append(event)

    def snapshot(self) -> List[RuntimeEvent]:
        """返回当前缓冲的事件列表副本。

        一次性快照，避免 caller 修改影响后续 caller。
        """
        return list(self._events)

    def filter(self, predicate: Callable[[RuntimeEvent], bool]) -> List[RuntimeEvent]:
        """按 predicate 过滤事件列表。"""
        return [e for e in self._events if predicate(e)]

    def filter_by_task(self, task_id: str) -> List[RuntimeEvent]:
        """按 task_id 过滤。"""
        return [e for e in self._events if e.task_id == task_id]

    def clear(self) -> None:
        """清空缓冲。"""
        self._events.clear()


def make_event_capture_callback(
    capture: RuntimeEventCapture,
) -> Callable[[RuntimeEvent], None]:
    """工厂函数：生成 capture.callback 闭包（便于 EventBus.subscribe）。"""
    return capture.callback
