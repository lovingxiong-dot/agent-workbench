"""tools/presentation/view_models/observation_view_model.py — ObservationViewModel。

聚合 4 View（RuntimeStatus / Performance / Resource / Lifecycle）为一个可消费 ViewModel。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tools.observation.reports.observation_report import (
    ObservationReport,
    ObservationMetrics,
)
from tools.observation.reports.footprint_snapshot import FootprintSnapshot

from tools.presentation.view_models.runtime_status_view import RuntimeStatusView
from tools.presentation.view_models.performance_view import PerformanceView
from tools.presentation.view_models.resource_view import ResourceView
from tools.presentation.view_models.lifecycle_view import LifecycleView


@dataclass(frozen=True)
class ObservationViewModel:
    """Phase 3.13 Presentation 视图模型（frozen）。

    边界（ADR-017 Decision 6 / 7）：
    - 不可变（frozen dataclass）
    - 不持有 Runtime 引用
    - 不订阅 EventBus
    - 包含 raw_report 供 Export 使用
    """

    execution_id: str
    task_id: str
    schema_version: str
    runtime_status: RuntimeStatusView
    performance: PerformanceView
    resource: ResourceView
    lifecycle: LifecycleView
    raw_report: dict
    observed_at: float

    @property
    def has_metrics(self) -> bool:
        """是否有任何 derived metrics。"""
        return self.performance.latency_known or self.performance.throughput_known
