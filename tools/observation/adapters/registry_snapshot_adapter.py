"""tools/observation/adapters/registry_snapshot_adapter.py — Registry Snapshot Adapter。

Adapter 仅调用 public API（has_node / get / get_depth），不读内部 _nodes。
"""
from __future__ import annotations

from typing import Iterable, List

from v6.runtime.execution_registry import ExecutionRegistry

from tools.observation.derived.registry_footprint import registry_footprint
from tools.observation.reports.footprint_snapshot import FootprintSnapshot


def collect_footprint(
    registry: ExecutionRegistry,
    known_execution_ids: Iterable[str],
) -> FootprintSnapshot:
    """采集 Registry Footprint（不修改 Registry）。

    Args:
        registry: ExecutionRegistry 实例
        known_execution_ids: 调用方已知的 execution_id 集合
    Returns:
        FootprintSnapshot
    """
    return registry_footprint(registry, known_execution_ids)


def filter_active_ids(
    registry: ExecutionRegistry,
    known_execution_ids: Iterable[str],
) -> List[str]:
    """从已知 IDs 中过滤仍在 Registry 内的（has_node 为 True）。"""
    return [eid for eid in known_execution_ids if registry.has_node(eid)]
