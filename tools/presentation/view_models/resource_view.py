"""tools/presentation/view_models/resource_view.py — ResourceView。

Read-only 数据投影：registry footprint。
数据源：ObservationReport.registry_footprint。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResourceView:
    """Resource 占用投影（Read-only）。

    - entries: 总 execution 节点数
    - active_entries: 活跃节点数
    - terminal_entries: 已终态节点数
    - max_depth: 最深执行树深度
    - memory_estimate_bytes: 内存占用估算
    - footprint_known: footprint 是否被采集
    """

    entries: int
    active_entries: int
    terminal_entries: int
    max_depth: int
    memory_estimate_bytes: int
    footprint_known: bool

    @classmethod
    def empty(cls) -> "ResourceView":
        """Footprint 未采集时的 fallback。"""
        return cls(
            entries=0,
            active_entries=0,
            terminal_entries=0,
            max_depth=-1,
            memory_estimate_bytes=0,
            footprint_known=False,
        )
