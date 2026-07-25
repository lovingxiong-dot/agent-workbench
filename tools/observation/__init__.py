"""tools/observation/ — Phase 3.12-A Runtime Observation Tool。

核心原则：
- Observation 是 Runtime 的"镜子"，不是 Runtime 的"器官"
- 仅消费 Frozen Artifact（RuntimeEvent / RuntimeTrace / ExecutionMetadata / Registry Snapshot）
- 禁止 import Runtime 写模块（Orchestrator / EngineManager / PlannerLoop）
- 禁止 import v6.9.6 Capability Frozen 模块
- Pure Function discipline: derived/ 模块下函数无副作用
"""
from tools.observation.reports.observation_report import (
    OBSERVATION_SCHEMA_VERSION,
    ObservationMetrics,
    ObservationReport,
)
from tools.observation.reports.footprint_snapshot import FootprintSnapshot
from tools.observation.collectors.evidence_collector import EvidenceCollector

__all__ = [
    "OBSERVATION_SCHEMA_VERSION",
    "ObservationMetrics",
    "ObservationReport",
    "FootprintSnapshot",
    "EvidenceCollector",
]  # 保持简单导出
