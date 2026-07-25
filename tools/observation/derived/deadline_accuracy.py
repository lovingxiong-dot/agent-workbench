"""tools/observation/derived/deadline_accuracy.py — Metric 3: Deadline Accuracy。

Pure Function: 输入 events + metadata，输出 deadline.error_ms（float | None）。

正值表示超过 deadline（晚完成）；负值表示提前完成。
"""
from __future__ import annotations

from typing import List, Optional

from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType
from v6.runtime.execution_metadata import ExecutionMetadata


_TERMINAL_EVENTS = {
    RuntimeEventType.TASK_COMPLETED,
    RuntimeEventType.TASK_FAILED,
    RuntimeEventType.TASK_CANCELLED,
}


def deadline_error_ms(
    events: List[RuntimeEvent],
    metadata: ExecutionMetadata,
    task_id: str,
) -> Optional[float]:
    """计算 deadline 与实际完成时间的偏差（毫秒）。

    算法：
    - actual_ts = task_id 首个 terminal event timestamp
    - deadline_ts = metadata.deadline_at unix timestamp
    - delta_ms = (actual_ts - deadline_ts) * 1000

    Returns:
        偏差毫秒（正=晚完成，负=提前），若 metadata.deadline_at 为 None 或 task 无 terminal event 返回 None
    """
    if metadata is None or metadata.deadline_at is None:
        return None
    if not events or not task_id:
        return None

    actual_ts: Optional[float] = None
    for event in events:
        if event.task_id != task_id:
            continue
        if event.type in _TERMINAL_EVENTS:
            actual_ts = event.timestamp
            break

    if actual_ts is None:
        return None

    deadline_ts = metadata.deadline_at.timestamp()
    return (actual_ts - deadline_ts) * 1000.0
