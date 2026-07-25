"""tools/presentation/exports/json_export.py — JSON Export。

将 ObservationViewModel 序列化为 JSON 字符串（或写入文件）。

边界（ADR-017 Decision 9）：
- 输出遵守 observation.v0.1 schema
- 不修改 schema；不增删字段
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from tools.presentation.view_models.observation_view_model import ObservationViewModel


def export_json(
    view_model: ObservationViewModel,
    indent: int = 2,
    path: Union[str, Path, None] = None,
) -> str:
    """导出 ObservationViewModel 为 JSON 格式。

    Args:
        view_model: Phase 3.13 frozen ViewModel
        indent: JSON indent（默认 2）
        path: 可选文件路径；提供时写入文件

    Returns:
        JSON 字符串
    """
    payload = _view_model_to_dict(view_model)
    json_str = json.dumps(payload, indent=indent, ensure_ascii=False)
    if path is not None:
        Path(path).write_text(json_str, encoding="utf-8")
    return json_str


def _view_model_to_dict(vm: ObservationViewModel) -> dict:
    return {
        "schema_version": vm.schema_version,
        "execution_id": vm.execution_id,
        "task_id": vm.task_id,
        "observed_at": vm.observed_at,
        "runtime_status": {
            "active_count": vm.runtime_status.active_count,
            "terminal_count": vm.runtime_status.terminal_count,
            "total_count": vm.runtime_status.total_count,
            "data_sources": vm.runtime_status.data_sources,
        },
        "performance": {
            "execution_latency_ms": vm.performance.execution_latency_ms,
            "event_throughput": vm.performance.event_throughput,
        },
        "resource": {
            "entries": vm.resource.entries,
            "active_entries": vm.resource.active_entries,
            "terminal_entries": vm.resource.terminal_entries,
            "max_depth": vm.resource.max_depth,
            "memory_estimate_bytes": vm.resource.memory_estimate_bytes,
            "footprint_known": vm.resource.footprint_known,
        },
        "lifecycle": {
            "cancellation_propagation_ms": vm.lifecycle.cancellation_propagation_ms,
            "deadline_error_ms": vm.lifecycle.deadline_error_ms,
        },
        "raw_report": vm.raw_report,
    }
