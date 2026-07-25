"""tools/observation/derived/cancellation_propagation.py — Metric 2: Cancellation Propagation Latency。

Pure Function: 输入 TASK_CANCELLED RuntimeEvent，输出传播延迟毫秒（float | None）。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType


def cancellation_propagation_ms(
    cancel_event: RuntimeEvent,
) -> Optional[float]:
    """计算 cancel 从发起（initiated_at）到 TASK_CANCELLED 发布的延迟。

    payload 结构（Phase 3.11-D v0.3 冻结）：
    {
      "propagation_type": "user_request" | "parent_cancelled" | "deadline_exceeded",
      "origin_execution_id": str,
      "chain": List[str],
      "reason": str,
      "initiated_at": ISO8601 字符串
    }

    算法：
    - 解析 payload.initiated_at 为 datetime
    - 转换 initiated_at 为 unix timestamp
    - delta_ms = (event.timestamp - initiated_at) * 1000

    Returns:
        传播延迟（毫秒），若 payload 缺 initiated_at 或解析失败返回 None
    """
    if cancel_event is None:
        return None
    if cancel_event.type != RuntimeEventType.TASK_CANCELLED:
        return None
    if not isinstance(cancel_event.payload, dict):
        return None

    initiated_at_raw = cancel_event.payload.get("initiated_at")
    if not isinstance(initiated_at_raw, str):
        return None
    if not initiated_at_raw:
        return None

    try:
        initiated_dt = datetime.fromisoformat(initiated_at_raw)
    except ValueError:
        return None

    # 确保 timezone-aware 转换
    if initiated_dt.tzinfo is None:
        initiated_dt = initiated_dt.replace(tzinfo=timezone.utc)

    initiated_ts = initiated_dt.timestamp()
    return (cancel_event.timestamp - initiated_ts) * 1000.0
