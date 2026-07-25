"""tools/observation/reports/observation_report.py — ObservationReport schema。

Phase 3.12-A Observation 内部 schema，不进入 Runtime Contract。

生命周期：被 EvidenceCollector 生成，可被 stdout / 测试消费。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


OBSERVATION_SCHEMA_VERSION = "observation.v0.1"


@dataclass(frozen=True)
class ObservationMetrics:
    """5 类 Derived Metrics 的容器。

    所有字段均为 Optional[float] —— 任一 metric 在数据缺失时为 None。
    """

    execution_latency_ms: Optional[float] = None
    cancellation_propagation_ms: Optional[float] = None
    deadline_error_ms: Optional[float] = None
    event_throughput: Optional[float] = None


@dataclass(frozen=True)
class ObservationReport:
    """Observation 报告（Phase 3.12-A 输出产物）。

    关键约束：
    - frozen dataclass（不可变）
    - schema_version 标记版本
    - data_sources 标记消费了哪些 Frozen Artifact
    - to_dict() 可被 json.dumps() 序列化
    """

    execution_id: str
    task_id: str
    observed_at: float = field(default_factory=time.time)
    observation_window_ms: float = 0.0
    metrics: ObservationMetrics = field(
        default_factory=ObservationMetrics
    )
    registry_footprint: Optional["FootprintSnapshot"] = None
    event_count: int = 0
    data_sources: Dict[str, bool] = field(
        default_factory=lambda: {
            "runtime_events": False,
            "runtime_trace": False,
            "execution_metadata": False,
            "registry_snapshot": False,
        }
    )
    schema_version: str = OBSERVATION_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 dict（用于 JSON Lines 输出或测试 fixture）。"""
        from tools.observation.reports.footprint_snapshot import FootprintSnapshot
        return {
            "schema_version": self.schema_version,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "observed_at": self.observed_at,
            "observation_window_ms": self.observation_window_ms,
            "metrics": {
                "execution_latency_ms": self.metrics.execution_latency_ms,
                "cancellation_propagation_ms": self.metrics.cancellation_propagation_ms,
                "deadline_error_ms": self.metrics.deadline_error_ms,
                "event_throughput": self.metrics.event_throughput,
            },
            "registry_footprint": (
                self.registry_footprint.to_dict()
                if self.registry_footprint is not None
                else None
            ),
            "event_count": self.event_count,
            "data_sources": self.data_sources,
        }
