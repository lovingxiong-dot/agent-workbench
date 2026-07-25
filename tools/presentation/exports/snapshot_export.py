"""tools/presentation/exports/snapshot_export.py — Snapshot Export。

将 ObservationViewModel 序列化为 Snapshot（持久化）。
格式：JSON Lines（可追加、便于 Snapshot 序列）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from tools.presentation.view_models.observation_view_model import ObservationViewModel


def export_snapshot(
    view_model: ObservationViewModel,
    path: Union[str, Path, None] = None,
) -> str:
    """导出 ObservationViewModel 为 Snapshot 格式（JSON Lines）。

    Args:
        view_model: Phase 3.13 frozen ViewModel
        path: 可选文件路径；提供时以 append 模式追加到文件

    Returns:
        Snapshot JSON Lines 单行字符串
    """
    payload = {
        "schema_version": view_model.schema_version,
        "execution_id": view_model.execution_id,
        "task_id": view_model.task_id,
        "observed_at": view_model.observed_at,
        "summary": {
            "active_count": view_model.runtime_status.active_count,
            "terminal_count": view_model.runtime_status.terminal_count,
            "latency_ms": view_model.performance.execution_latency_ms,
            "cancellation_ms": view_model.lifecycle.cancellation_propagation_ms,
            "deadline_error_ms": view_model.lifecycle.deadline_error_ms,
        },
    }
    line = json.dumps(payload, ensure_ascii=False)
    if path is not None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return line
