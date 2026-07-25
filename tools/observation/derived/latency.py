"""tools/observation/derived/latency.py — Metric 1: Execution Latency。

Pure Function: 输入 Frozen RuntimeEvent 列表 + task_id，输出延迟毫秒（float | None）。
无副作用，无 I/O，无 Runtime 状态修改。
"""
from __future__ import annotations

from typing import List, Optional

from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType


_TERMINAL_EVENTS = {
    RuntimeEventType.TASK_COMPLETED,
    RuntimeEventType.TASK_FAILED,
    RuntimeEventType.TASK_CANCELLED,
}


def execution_latency_ms(
    events: List[RuntimeEvent],
    task_id: str,
) -> Optional[float]:
    """计算 task 的执行延迟（毫秒）。

    算法：
    1. 找到该 task_id 的首个 TASK_STARTED 事件 timestamp = started_ts
    2. 找到该 task_id 的首个 terminal event (TASK_COMPLETED / TASK_FAILED / TASK_CANCELLED) timestamp = terminal_ts
    3. 若两者都存在：latency_ms = (terminal_ts - started_ts) * 1000

    Returns:
        延迟毫秒，若无完整 start/terminal 返回 None
    """
    if not events or not task_id:
        return None

    started_ts: Optional[float] = None
    terminal_ts: Optional[float] = None

    for event in events:
        if event.task_id != task_id:
            continue
        if event.type == RuntimeEventType.TASK_STARTED and started_ts is None:
            started_ts = event.timestamp
        elif event.type in _TERMINAL_EVENTS and terminal_ts is None:
            terminal_ts = event.timestamp

    if started_ts is None or terminal_ts is None:
        return None
    if terminal_ts < started_ts:
        # 异常: terminal 在 start 之前
        return None

    return (terminal_ts - started_ts) * 1000.0
