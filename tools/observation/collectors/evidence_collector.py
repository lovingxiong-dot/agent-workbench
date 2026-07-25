"""tools/observation/collectors/evidence_collector.py — EvidenceCollection orchestration。

EvidenceCollector 拼接 adapters → derived → report。
无 Runtime 引用，无 Worker 启动，无状态修改。
"""
from __future__ import annotations

import time
from datetime import timedelta
from typing import Iterable, List, Optional

from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.execution_registry import ExecutionRegistry
from v6.runtime.trace import RuntimeTrace

from tools.observation.adapters.execution_metadata_adapter import collect_metadata
from v6.runtime.execution_metadata import ExecutionMetadata
from tools.observation.adapters.registry_snapshot_adapter import (
    collect_footprint,
)
from tools.observation.adapters.runtime_event_adapter import RuntimeEventCapture
from tools.observation.adapters.trace_adapter import collect_trace_steps
from tools.observation.derived.cancellation_propagation import (
    cancellation_propagation_ms,
)
from tools.observation.derived.deadline_accuracy import deadline_error_ms
from tools.observation.derived.event_throughput import event_throughput
from tools.observation.derived.latency import execution_latency_ms
from tools.observation.reports.observation_report import (
    ObservationMetrics,
    ObservationReport,
)



class EvidenceCollector:
    """Phase 3.12-A Evidence Collector。

    输入来源（仅 Frozen Artifact）：
    - RuntimeEventCapture (订阅 EventBus)
    - RuntimeTrace (snapshot)
    - ExecutionRegistry (public API for snapshot)
    - ExecutionNode (通过 execution_id 获取)

    输出：
    - ObservationReport（frozen dataclass）

    不持有 Runtime lifecycle 引用（不 import Orchestrator）。
    不启动 Worker。
    不修改任何 Runtime 状态。
    """

    def __init__(
        self,
        runtime_event_capture: Optional[RuntimeEventCapture] = None,
        trace: Optional[RuntimeTrace] = None,
        registry: Optional[ExecutionRegistry] = None,
    ) -> None:
        self._event_capture = runtime_event_capture
        self._trace = trace
        self._registry = registry

    def collect_observation(
        self,
        execution_id: str,
        task_id: str,
        known_execution_ids: Optional[Iterable[str]] = None,
        window: Optional[timedelta] = None,
        metadata: Optional["ExecutionMetadata"] = None,
    ) -> ObservationReport:
        """采集单个 execution 的 Observation。

        Args:
            execution_id: 目标 Execution 唯一 ID
            task_id: 关联 Task ID（用于 latency metric）
            known_execution_ids: 可选，已知 execution_ids（用于 footprint 采样）
            window: 可选观察窗口
            metadata: 可选 ExecutionMetadata（用于 deadline metric；Registry 节点不含 deadline_at）
        """
        window_ms = (window.total_seconds() * 1000.0) if window else 0.0

        # ── 收集 Frozen Artifacts ──
        data_sources = {
            "runtime_events": False,
            "runtime_trace": False,
            "execution_metadata": False,
            "registry_snapshot": False,
        }

        events: List[RuntimeEvent] = []
        if self._event_capture is not None:
            events = self._event_capture.snapshot()
            data_sources["runtime_events"] = True

        trace_steps: list = []
        if self._trace is not None:
            trace_steps = collect_trace_steps(self._trace, execution_id)
            data_sources["runtime_trace"] = True

        # 标记事件来源（trace 计入 event_count 近似）
        trace_event_count = len(trace_steps)

        # 收集 ExecutionNode（不包含 deadline_at，仅用于 trace）
        node = None
        if self._registry is not None:
            node = collect_metadata(self._registry, execution_id)
            data_sources["execution_metadata"] = node is not None

        footprint = None
        if self._registry is not None and known_execution_ids is not None:
            footprint = collect_footprint(self._registry, known_execution_ids)
            data_sources["registry_snapshot"] = True

        # ── 计算 Derived Metrics ──
        latency = execution_latency_ms(events, task_id)

        cancellation_delay = None
        for event in events:
            if event.task_id == task_id:
                ms = cancellation_propagation_ms(event)
                if ms is not None:
                    cancellation_delay = ms
                    break

        # deadline_error: 必须显式传入 metadata（Registry 节点不含 deadline_at）
        deadline_error = None
        if metadata is not None and metadata.deadline_at is not None:
            deadline_error = deadline_error_ms(events, metadata, task_id)

        throughput = None
        if events:
            # Use events 实际首尾 timestamp（不依赖 now）。
            # window 仅作为 label（observation_window_ms），不影响 throughput 计算。
            throughput = event_throughput(events)

        metrics = ObservationMetrics(
            execution_latency_ms=latency,
            cancellation_propagation_ms=cancellation_delay,
            deadline_error_ms=deadline_error,
            event_throughput=throughput,
        )

        return ObservationReport(
            execution_id=execution_id,
            task_id=task_id,
            observed_at=time.time(),
            observation_window_ms=window_ms,
            metrics=metrics,
            registry_footprint=footprint,
            event_count=len(events),
            data_sources=data_sources,
        )
