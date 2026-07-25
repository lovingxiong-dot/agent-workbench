"""tools/observation/derived/registry_footprint.py — Metric 5: Registry Footprint Observation。

Pure Function: 通过外部传入的 known_execution_ids + has_node() 采集 FootprintSnapshot。
不修改 Registry，不读 Registry._nodes 内部（保留 ABI 稳定性）。
"""
from __future__ import annotations

import time
from typing import Iterable, List

from v6.runtime.execution_registry import ExecutionRegistry

from tools.observation.reports.footprint_snapshot import FootprintSnapshot


# 平均 ExecutionNode 内存占用估算（best-effort, bytes）
# Phase 3.11-D v0.3 ExecutionNode 字段: execution_id(36) + task_id(36) + parent_execution_id(8) + children_ids(8) + timestamps(24)
# 加 Python 对象 overhead 估算 200 字节每节点。
_EXECUTION_NODE_BYTES_ESTIMATE = 200


def registry_footprint(
    registry: ExecutionRegistry,
    known_execution_ids: Iterable[str],
) -> FootprintSnapshot:
    """采集 ExecutionRegistry 当前 Footprint（不修改 Registry）。

    通过 External known_execution_ids + public `has_node()` API。
    active vs terminal 通过 `get_node().terminated_at` 判定。

    注意：ExecutionRegistry 当前未提供 external ID 枚举 API。
    调用方负责提供 known_execution_ids（Phase 3.12-A 不引入 Registry Schema 演进）。

    Args:
        registry: ExecutionRegistry 实例
        known_execution_ids: 调用方已知的 execution_id 集合（来自 EventBus / Trace / Session 等）

    Returns:
        FootprintSnapshot（frozen dataclass）
    """
    ids: List[str] = list(known_execution_ids)
    entries = 0
    active_entries = 0
    terminal_entries = 0

    for eid in ids:
        if not registry.has_node(eid):
            continue
        entries += 1
        node = registry.get(eid)
        if node is None:
            continue
        if node.terminated_at is None:
            active_entries += 1
        else:
            terminal_entries += 1

    # max_depth: 通过 public get_depth() 计算（每个节点调用）
    max_depth = -1
    if ids:
        depths = []
        for eid in ids:
            if registry.has_node(eid):
                depths.append(registry.get_depth(eid))
        if depths:
            max_depth = max(depths)

    memory_estimate = entries * _EXECUTION_NODE_BYTES_ESTIMATE

    return FootprintSnapshot(
        entries=entries,
        active_entries=active_entries,
        terminal_entries=terminal_entries,
        max_depth=max_depth,
        memory_estimate_bytes=memory_estimate,
        sampled_at=time.time(),
        sample_window_ids=len(ids),
    )
