"""tools/observation/contract/observation_artifact.py — Phase 3.12 ObservationArtifact Frozen Contract.

Phase 3.12 Batch 1: Observation Contract Schema (Schema-First).

Contract v0.1 (ADR-016):
- ObservationArtifact: frozen dataclass (immutable)
- ObservationType: 5 类 (Performance / Resource / Lifecycle / Event / Health)
- ObservationScore: 3 维 (relevance / confidence / stability)
- ObservationSource: 4 类 (human / agent / runtime / system)
- Mandatory Provenance (created_at, created_by)
- Frozen schema_version = "observation.v0.1"

边界 (ADR-016 Decision 3):
- frozen dataclass
- No Runtime mutation
- Read-Only Consumer
- No Orchestrator / EngineManager / PlannerLoop
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


OBSERVATION_SCHEMA_VERSION = "observation.v0.1"


class ObservationType(str, Enum):
    """5 类 Phase 3.12 Observation（ADR-016 Contract v0.1）。

    对应 Runtime 不同 facet：
    - PERFORMANCE: latency / throughput / response time
    - RESOURCE: memory / cpu / connections
    - LIFECYCLE: state transitions
    - EVENT: task events / errors
    - HEALTH: system health / errors
    """

    PERFORMANCE = "performance"
    RESOURCE = "resource"
    LIFECYCLE = "lifecycle"
    EVENT = "event"
    HEALTH = "health"


class ObservationSource(str, Enum):
    """4 类 Observation 来源（ADR-016 Contract v0.1）。"""

    HUMAN = "human"
    AGENT = "agent"
    RUNTIME = "runtime"
    SYSTEM = "system"


@dataclass(frozen=True)
class ObservationScore:
    """3 维 Observation 评分（ADR-016 Contract v0.1）。

    所有字段均为 0.0-1.0 范围。
    - relevance: 与当前任务关联度
    - confidence: 数据可信度
    - stability: 稳定性（如 Frozen Contract = 1.0）
    """

    relevance: float = 0.0
    confidence: float = 0.0
    stability: float = 0.0

    def __post_init__(self) -> None:
        """Validate score 维度范围 [0.0, 1.0]。"""
        for field_name in ("relevance", "confidence", "stability"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"ObservationScore.{field_name} must be in [0.0, 1.0], got {value}"
                )


@dataclass(frozen=True)
class ObservationArtifact:
    """Phase 3.12 Observation Layer Frozen Contract（ADR-016 v0.1）。

    关键约束：
    - frozen dataclass（不可变）
    - schema_version 标记（frozen = "observation.v0.1"）
    - Provenance 强制（created_at, created_by）
    - No Runtime lifecycle 引用（仅 metadata 字段）
    - 序列化安全（to_dict → JSON-friendly）

    设计意图：
    - contract/observation_artifact.py 是 Phase 3.12 Frozen Schema（Future Phase 3.13+ Presentation / Phase 3.14 Insight 通用）
    - reports/observation_report.py 是内部 EvidenceCollector 输出（5 Derived Metrics）
    - 两者并存，不冲突（reports/ 是 contract/ 的具体实现之一）
    """

    id: str
    observation_type: ObservationType
    content: Any
    score: ObservationScore
    source: ObservationSource
    created_at: float = field(default_factory=time.time)
    created_by: str = ""
    execution_id: str = ""
    task_id: str = ""
    schema_version: str = OBSERVATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate mandatory fields。"""
        if not self.id:
            raise ValueError("ObservationArtifact.id must be non-empty")
        if not self.created_by:
            raise ValueError("ObservationArtifact.created_by must be non-empty (Provenance)")

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 dict（JSON-friendly）。

        用于 Phase 3.13+ 持久化 / 跨模块传递。
        """
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "observation_type": self.observation_type.value,
            "source": self.source.value,
            "score": {
                "relevance": self.score.relevance,
                "confidence": self.score.confidence,
                "stability": self.score.stability,
            },
            "created_at": self.created_at,
            "created_by": self.created_by,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "content": self._serialize_content(self.content),
        }

    @staticmethod
    def _serialize_content(content: Any) -> Any:
        """Serialize content for JSON compatibility。

        - dict / list / tuple: deepcopy-safe pass-through
        - primitive (str / int / float / bool / None): as-is
        - 其他: str() fallback
        """
        if isinstance(content, (str, int, float, bool, type(None))):
            return content
        if isinstance(content, dict):
            return {k: ObservationArtifact._serialize_content(v) for k, v in content.items()}
        if isinstance(content, (list, tuple)):
            return [ObservationArtifact._serialize_content(item) for item in content]
        return str(content)
