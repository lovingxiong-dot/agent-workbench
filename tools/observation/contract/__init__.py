"""tools/observation/contract/ — Phase 3.12 Observation Layer Contract (Schema-First)。

Phase 3.12 Batch 1: Observation Contract Schema (Frozen Contract v0.1)。

边界 (ADR-016 Decision 3):
- frozen dataclass（不可变）
- 不引用 Orchestrator / EngineManager / PlannerLoop
- 不修改 Runtime Kernel
- 不订阅 EventBus（由 Adapter 层处理）
- 不 import 任何 v6.runtime 写模块

设计原则:
- 5 类 ObservationType (Performance / Resource / Lifecycle / Event / Health)
- 3 维 ObservationScore (relevance / confidence / stability)
- 4 类 ObservationSource (human / agent / runtime / system)
- Mandatory Provenance
- Frozen schema_version = "observation.v0.1"

不同 tools/observation/{adapters,derived,reports,collectors}/：
- adapters: Frozen Input Adapters (read-only)
- derived: Pure Functions (Derived Metrics)
- reports: ObservationReport (EvidenceCollector 输出, 5 Derived Metrics)
- collectors: EvidenceCollector (Orchestration)
- contract: Schema-First Frozen Contract (ObservationArtifact + ObservationType + ObservationScore)

contract/ 是 Phase 3.12 Frozen 核心 schema，与 reports/ 平级但语义不同：
- reports/  = 内部 derived metrics 输出 (5 derived numbers)
- contract/ = 通用 ObservationArtifact 协议 (5 type + 3 score)
"""
from tools.observation.contract.observation_artifact import (
    OBSERVATION_SCHEMA_VERSION,
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)

__all__ = [
    "OBSERVATION_SCHEMA_VERSION",
    "ObservationArtifact",
    "ObservationScore",
    "ObservationSource",
    "ObservationType",
]
