"""tools/presentation/adapters/observation_to_view_model.py — Mapping Adapter。

单向数据流：ObservationReport (Phase 3.12) → ObservationViewModel (Phase 3.13)。

边界（ADR-017 Decision 7）：
- Adapter 不修改 ObservationReport
- Adapter 不持有 Runtime 引用
- Adapter 不订阅 EventBus 写事件
- Adapter 不调用 Runtime lifecycle
"""
from __future__ import annotations

from tools.observation.reports.observation_report import (
    ObservationReport,
    ObservationMetrics,
)
from tools.observation.reports.footprint_snapshot import FootprintSnapshot

from tools.presentation.view_models.observation_view_model import ObservationViewModel
from tools.presentation.view_models.runtime_status_view import RuntimeStatusView
from tools.presentation.view_models.performance_view import PerformanceView
from tools.presentation.view_models.resource_view import ResourceView
from tools.presentation.view_models.lifecycle_view import LifecycleView


def observation_to_view_model(
    report: ObservationReport,
) -> ObservationViewModel:
    """将 ObservationReport 映射为 ObservationViewModel（单向、不可变）。

    Args:
        report: Phase 3.12 frozen ObservationReport

    Returns:
        ObservationViewModel: Phase 3.13 frozen ViewModel
    """
    metrics = report.metrics or ObservationMetrics()
    footprint = report.registry_footprint

    # RuntimeStatus: 从 footprint + data_sources 派生
    runtime_status = _build_runtime_status(report, footprint)

    # Performance: latency + throughput
    performance = _build_performance(metrics)

    # Resource: footprint
    resource = _build_resource(footprint)

    # Lifecycle: cancellation + deadline
    lifecycle = _build_lifecycle(metrics)

    return ObservationViewModel(
        execution_id=report.execution_id,
        task_id=report.task_id,
        schema_version=report.schema_version,
        runtime_status=runtime_status,
        performance=performance,
        resource=resource,
        lifecycle=lifecycle,
        raw_report=report.to_dict(),
        observed_at=report.observed_at,
    )


# ── helpers（pure, no I/O） ───────────────────────────────────────


def _build_runtime_status(
    report: ObservationReport,
    footprint: FootprintSnapshot | None,
) -> RuntimeStatusView:
    active = footprint.active_entries if footprint is not None else 0
    terminal = footprint.terminal_entries if footprint is not None else 0
    total = footprint.entries if footprint is not None else 0
    return RuntimeStatusView(
        active_count=active,
        terminal_count=terminal,
        total_count=total,
        data_sources=dict(report.data_sources),
    )


def _build_performance(metrics: ObservationMetrics) -> PerformanceView:
    return PerformanceView(
        execution_latency_ms=metrics.execution_latency_ms,
        event_throughput=metrics.event_throughput,
        latency_known=metrics.execution_latency_ms is not None,
        throughput_known=metrics.event_throughput is not None,
    )


def _build_resource(footprint: FootprintSnapshot | None) -> ResourceView:
    if footprint is None:
        return ResourceView.empty()
    return ResourceView(
        entries=footprint.entries,
        active_entries=footprint.active_entries,
        terminal_entries=footprint.terminal_entries,
        max_depth=footprint.max_depth,
        memory_estimate_bytes=footprint.memory_estimate_bytes,
        footprint_known=True,
    )


def _build_lifecycle(metrics: ObservationMetrics) -> LifecycleView:
    return LifecycleView(
        cancellation_propagation_ms=metrics.cancellation_propagation_ms,
        deadline_error_ms=metrics.deadline_error_ms,
        cancellation_known=metrics.cancellation_propagation_ms is not None,
        deadline_known=metrics.deadline_error_ms is not None,
    )
