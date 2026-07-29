"""tools/decision_support/contract/decision_artifact.py — Phase 3.15 DecisionArtifact Frozen Contract.

Decision Support = "What should we consider" (NOT "what to do now").

Frozen fields (4 main):
- options (List[DecisionOption], required): decision options
- rationale_metadata (Dict, default): decision rationale (NOT LLM narrative)
- confidence (float, required): [0.0, 1.0] confidence score
- constraints_reference (Dict, default): reference to constraints (NOT execution)

Auto-fields:
- id (str, required): unique decision id
- insight_reference (List[str], required): source InsightArtifact IDs
- created_at (float, default): creation timestamp
- schema_version (str, default): frozen schema version

Strict NOT in scope (Phase 3.15):
- ❌ execute / schedule / capability routing
- ❌ task mutation / memory write
- ❌ LLM autonomous decision
- ❌ ActionExecutor / AgentPlanner / WorkflowEngine

Contract boundary (ADR-019):
- decision options layer (NOT action executor)
- pure data contract
- no execution dependency
- no scheduling dependency
- no LLM autonomous decision
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


DECISION_ARTIFACT_SCHEMA_VERSION = "decision.v0.1"


class DecisionStrategy(str, Enum):
    """5 类 Decision Strategy (rule-based, NOT AI autonomous)."""

    CONSERVATIVE = "conservative"  # 风险最小
    BALANCED = "balanced"  # 平衡
    AGGRESSIVE = "aggressive"  # 最大化收益
    DEFENSIVE = "defensive"  # 保护资源
    NEUTRAL = "neutral"  # 不主动行动


@dataclass(frozen=True)
class DecisionOption:
    """A single decision option (NOT an action).

    Fields (frozen):
    - id (str, required): unique option id
    - label (str, required): display label
    - score (float, default): [0.0, 1.0] option score
    - rationale (str, default): explanation (NOT LLM narrative)
    """

    id: str
    label: str
    score: float = 0.0
    rationale: str = ""

    def __post_init__(self) -> None:
        """Validate DecisionOption fields."""
        if not self.id:
            raise ValueError("DecisionOption.id must be non-empty")
        if not self.label:
            raise ValueError("DecisionOption.label must be non-empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"DecisionOption.score must be in [0.0, 1.0], got {self.score}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-friendly)."""
        return {
            "id": self.id,
            "label": self.label,
            "score": self.score,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class DecisionArtifact:
    """Phase 3.15 Decision Support Frozen Contract.

    4 main fields (Frozen):
    - options (List[DecisionOption], required): decision options (NOT actions)
    - rationale_metadata (Dict, default): decision rationale (NOT LLM narrative)
    - confidence (float, required): [0.0, 1.0] confidence score
    - constraints_reference (Dict, default): reference to constraints (NOT execution)

    Auto-fields:
    - id (str, required): unique decision id
    - insight_reference (List[str], required): source InsightArtifact IDs
    - strategy (DecisionStrategy, default): decision strategy
    - created_at (float, default): creation timestamp
    - schema_version (str, default): frozen schema version

    关键约束:
    - frozen dataclass (immutable)
    - no execution dependency
    - no scheduling dependency
    - no LLM autonomous decision
    - rule-based strategy only (NOT AI autonomous)
    """

    id: str
    insight_reference: List[str]
    options: List[DecisionOption]
    confidence: float
    rationale_metadata: Dict[str, Any] = field(default_factory=dict)
    constraints_reference: Dict[str, Any] = field(default_factory=dict)
    strategy: DecisionStrategy = DecisionStrategy.BALANCED
    created_at: float = field(default_factory=time.time)
    schema_version: str = DECISION_ARTIFACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate required fields (Mandatory Contract)."""
        if not self.id:
            raise ValueError("DecisionArtifact.id must be non-empty")
        if not self.insight_reference:
            raise ValueError(
                "DecisionArtifact.insight_reference must be non-empty "
                "(decision must reference at least one insight)"
            )
        if not self.options:
            raise ValueError(
                "DecisionArtifact.options must be non-empty "
                "(at least one option required)"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"DecisionArtifact.confidence must be in [0.0, 1.0], "
                f"got {self.confidence}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-friendly)."""
        return {
            "id": self.id,
            "insight_reference": list(self.insight_reference),
            "options": [opt.to_dict() for opt in self.options],
            "strategy": self.strategy.value,
            "confidence": self.confidence,
            "rationale_metadata": dict(self.rationale_metadata),
            "constraints_reference": dict(self.constraints_reference),
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }