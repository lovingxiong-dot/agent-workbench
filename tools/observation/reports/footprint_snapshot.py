"""tools/observation/reports/footprint_snapshot.py — Registry Footprint Snapshot。

Phase 3.12-A Observation 内部产物。
不依赖 Frozen Runtime 模块（runtime types 在 derived/registry_footprint.py 中消费）。
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class FootprintSnapshot:
    """Registry 占用快照（仅观察，不修改 Registry）。

    字段：
    - entries: 总节点数
    - active_entries: 未 terminated 节点数
    - terminal_entries: terminated 但未 cleanup 节点数
    - max_depth: 最深 Execution Tree 深度
    - memory_estimate_bytes: 通过 ExecutionNode 估算占用（best-effort）
    - sampled_at: time.time() 采样时间
    - sample_window_ids: 已采样的 ID 数量（用于审计）
    """

    entries: int
    active_entries: int
    terminal_entries: int
    max_depth: int
    memory_estimate_bytes: int
    sampled_at: float
    sample_window_ids: int = 0

    def to_dict(self) -> dict:
        """序列化为 dict。"""
        return {
            "entries": self.entries,
            "active_entries": self.active_entries,
            "terminal_entries": self.terminal_entries,
            "max_depth": self.max_depth,
            "memory_estimate_bytes": self.memory_estimate_bytes,
            "sampled_at": self.sampled_at,
            "sample_window_ids": self.sample_window_ids,
        }
