"""tools/presentation/view_models/performance_view.py — PerformanceView。

Read-only 数据投影：duration / throughput。
数据源：ObservationReport.metrics（latency / throughput）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PerformanceView:
    """Performance 指标投影（Read-only）。

    - execution_latency_ms: 任务执行延迟（毫秒）
    - event_throughput: 事件吞吐量（events/sec）
    - latency_known: latency 是否可计算
    - throughput_known: throughput 是否可计算
    """

    execution_latency_ms: Optional[float]
    event_throughput: Optional[float]
    latency_known: bool
    throughput_known: bool
