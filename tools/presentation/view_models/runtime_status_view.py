"""tools/presentation/view_models/runtime_status_view.py — RuntimeStatusView。

Read-only 数据投影：active / completed / failed counts。
数据源：ObservationReport.data_sources + FootprintSnapshot。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeStatusView:
    """Runtime 状态投影（Read-only）。

    - active_count: 当前活跃 execution 数
    - terminal_count: 已 terminal execution 数
    - total_count: 总 execution 数
    - data_sources: 哪些 Frozen 数据源被消费（来自 ObservationReport.data_sources）
    """

    active_count: int
    terminal_count: int
    total_count: int
    data_sources: dict
