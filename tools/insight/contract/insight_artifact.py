"""tools/insight/contract/insight_artifact.py — Phase 3.14 InsightArtifact Frozen Contract.

Insight = "What does it mean" (NOT "what happened", NOT "what to do").

Frozen fields (5):
- observation_reference: Reference to source ObservationArtifact(s)
- pattern: Detected pattern (rule-based, deterministic, NOT AI)
- classification: InsightClassification enum (5 types)
- confidence: [0.0, 1.0] confidence score
- explanation_metadata: Display-ready metadata (NOT LLM narrative)

Strict NOT in scope (Phase 3.14):
- ❌ Memory / Persistence
- ❌ Decision / Recommendation / Action / Planning
- ❌ AI generated narrative / LLM summary / natural language report

Contract boundary (ADR-018):
- structured understanding layer
- pure data contract
- no runtime dependency
- no memory dependency
- no LLM dependency
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


INSIGHT_ARTIFACT_SCHEMA_VERSION = "insight.v0.1"


class InsightPattern(str, Enum):
    """5 类 Insight Pattern (rule-based, deterministic).

    NOT AI / NOT LLM. Rule-based classification only.
    """

    ANOMALY = "anomaly"  # 偏离预期
    CORRELATION = "correlation"  # 多 Observation 关联
    TREND = "trend"  # 时序变化
    THRESHOLD = "threshold"  # 阈值突破
    PATTERN = "pattern"  # 通用模式


class InsightClassification(str, Enum):
    """5 类 Insight Classification (mirrors InsightPattern + meta).

    Category indicates severity/type for downstream consumption.
    """

    INFO = "info"  # 一般性 insight
    WARNING = "warning"  # 需关注
    CRITICAL = "critical"  # 需立即关注
    ANOMALY = "anomaly"  # 异常事件
    TREND = "trend"  # 趋势变化


@dataclass(frozen=True)
class InsightArtifact:
    """Phase 3.14 Insight Frozen Contract (structured understanding layer).

    5 fields (Frozen):
    - observation_reference (List[str], required): source ObservationArtifact IDs
    - pattern (InsightPattern, required): rule-based pattern (NOT AI)
    - classification (InsightClassification, required): insight type
    - confidence (float, required): [0.0, 1.0] confidence score
    - explanation_metadata (Dict[str, Any], default): display-ready metadata
      (NOT LLM narrative, NOT AI summary)

    Auto-fields:
    - id (str, required): unique insight id
    - created_at (float, default): creation timestamp
    - schema_version (str, default): frozen schema version

    关键约束:
    - frozen dataclass (immutable)
    - no LLM dependency (no narrative generation)
    - no memory dependency (no persistence)
    - no decision (no recommendation / action)
    - rule-based pattern only (NOT AI)
    """

    id: str
    observation_reference: List[str]
    pattern: InsightPattern
    classification: InsightClassification
    confidence: float
    explanation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    schema_version: str = INSIGHT_ARTIFACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate required fields (Mandatory Contract)."""
        if not self.id:
            raise ValueError("InsightArtifact.id must be non-empty")
        if not self.observation_reference:
            raise ValueError(
                "InsightArtifact.observation_reference must be non-empty "
                "(insight must reference at least one observation)"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"InsightArtifact.confidence must be in [0.0, 1.0], "
                f"got {self.confidence}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-friendly)."""
        return {
            "id": self.id,
            "observation_reference": list(self.observation_reference),
            "pattern": self.pattern.value,
            "classification": self.classification.value,
            "confidence": self.confidence,
            "explanation_metadata": dict(self.explanation_metadata),
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }