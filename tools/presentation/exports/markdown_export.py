"""tools/presentation/exports/markdown_export.py — Markdown Export。

将 ObservationViewModel 序列化为 Markdown（人工阅读 / Debug）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from tools.presentation.view_models.observation_view_model import ObservationViewModel


def export_markdown(
    view_model: ObservationViewModel,
    path: Union[str, Path, None] = None,
) -> str:
    """导出 ObservationViewModel 为 Markdown 格式。

    Args:
        view_model: Phase 3.13 frozen ViewModel
        path: 可选文件路径；提供时写入文件

    Returns:
        Markdown 字符串
    """
    md = _render_markdown(view_model)
    if path is not None:
        Path(path).write_text(md, encoding="utf-8")
    return md


def _render_markdown(vm: ObservationViewModel) -> str:
    lines = [
        f"# Observation Report — {vm.execution_id}",
        "",
        f"- **Task ID**: `{vm.task_id}`",
        f"- **Schema Version**: `{vm.schema_version}`",
        f"- **Observed At**: `{vm.observed_at}`",
        "",
        "## Runtime Status",
        "",
        f"- **Active**: {vm.runtime_status.active_count}",
        f"- **Terminal**: {vm.runtime_status.terminal_count}",
        f"- **Total**: {vm.runtime_status.total_count}",
        "",
        "## Performance",
        "",
        f"- **Execution Latency (ms)**: {_format_optional(vm.performance.execution_latency_ms)}",
        f"- **Event Throughput (events/sec)**: {_format_optional(vm.performance.event_throughput)}",
        "",
        "## Resource",
        "",
        f"- **Entries**: {vm.resource.entries}",
        f"- **Active**: {vm.resource.active_entries}",
        f"- **Terminal**: {vm.resource.terminal_entries}",
        f"- **Max Depth**: {vm.resource.max_depth}",
        f"- **Memory Estimate (bytes)**: {vm.resource.memory_estimate_bytes}",
        f"- **Footprint Known**: {vm.resource.footprint_known}",
        "",
        "## Lifecycle",
        "",
        f"- **Cancellation Propagation (ms)**: {_format_optional(vm.lifecycle.cancellation_propagation_ms)}",
        f"- **Deadline Error (ms)**: {_format_optional(vm.lifecycle.deadline_error_ms)}",
        "",
        "## Data Sources",
        "",
    ]
    for name, available in vm.runtime_status.data_sources.items():
        marker = "✅" if available else "❌"
        lines.append(f"- {marker} `{name}`")
    lines.append("")
    return "\n".join(lines)


def _format_optional(value):
    return "n/a" if value is None else f"{value}"
