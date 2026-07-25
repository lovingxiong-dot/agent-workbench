"""tools/presentation/view_models/lifecycle_view.py — LifecycleView。

Read-only 数据投影：cancellation / deadline。
数据源：ObservationReport.metrics（cancellation_propagation_ms / deadline_error_ms）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LifecycleView:
    """Lifecycle 指标投影（Read-only）。

    - cancellation_propagation_ms: cancel 传播延迟（毫秒）
    - deadline_error_ms: deadline 偏差（毫秒，正=晚完成）
    - cancellation_known: cancellation metric 是否可计算
    - deadline_known: deadline metric 是否可计算
    """

    cancellation_propagation_ms: Optional[float]
    deadline_error_ms: Optional[float]
    cancellation_known: bool
    deadline_known: bool
