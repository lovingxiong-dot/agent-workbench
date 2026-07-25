"""tools/observation/adapters/execution_metadata_adapter.py — ExecutionMetadata Adapter。

仅通过已知 execution_id + ExecutionRegistry public API 获取 ExecutionNode。
"""
from __future__ import annotations

from typing import Optional

from v6.runtime.execution_registry import ExecutionRegistry, ExecutionNode


def collect_metadata(
    registry: ExecutionRegistry,
    execution_id: str,
) -> Optional[ExecutionNode]:
    """通过 execution_id 获取 ExecutionNode（若存在）。

    Returns:
        ExecutionNode 或 None（不存在 / 已 cleanup）
    """
    if registry is None or not execution_id:
        return None
    return registry.get(execution_id)
