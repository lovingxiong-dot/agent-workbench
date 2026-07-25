"""tools/observation/derived/event_throughput.py — Metric 4: Event Throughput。

Pure Function: 输入 events + 可选 window，输出 events/sec（float | None）。
"""
from __future__ import annotations

from typing import List, Optional

from v6.runtime.event_bus import RuntimeEvent


def event_throughput(
    events: List[RuntimeEvent],
    window_start: Optional[float] = None,
    window_end: Optional[float] = None,
) -> Optional[float]:
    """事件 throughput（每秒事件数）。

    算法：
    - 若未提供 window_start/window_end，使用 events 实际首尾 timestamp
    - 若提供了 window，则只计算 window 内的 events
    - window_seconds = end - start
    - rate = events_in_window / window_seconds
    - 避免除零: window_seconds <= 0 返回 None

    Returns:
        events/sec，若 events 为空或 window<=0 返回 None
    """
    if not events:
        return None

    if window_start is None:
        window_start = events[0].timestamp
    if window_end is None:
        window_end = events[-1].timestamp

    window_seconds = window_end - window_start
    if window_seconds <= 0:
        return None

    # 显式 window 时，过滤 window 内的 events
    in_window = [
        e for e in events
        if window_start <= e.timestamp <= window_end
    ]
    if not in_window:
        return None
    return len(in_window) / window_seconds
