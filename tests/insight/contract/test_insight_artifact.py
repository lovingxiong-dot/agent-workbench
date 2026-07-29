"""tests/insight/contract/test_insight_artifact.py — Phase 3.14 InsightArtifact Tests.

Tests:
- Schema version (frozen)
- 5 fields (observation_reference / pattern / classification / confidence / explanation_metadata)
- Required fields validation
- Confidence bounds [0.0, 1.0]
- Frozen dataclass
- to_dict serialization
- Forbidden fields (no memory/decision/AI narrative)
"""
from __future__ import annotations

import json

import pytest

from tools.insight.contract import (
    INSIGHT_ARTIFACT_SCHEMA_VERSION,
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)


def _make_insight(
    insight_id: str = "insight-001",
    observation_reference: list = None,
    pattern: InsightPattern = InsightPattern.PATTERN,
    classification: InsightClassification = InsightClassification.INFO,
    confidence: float = 0.8,
) -> InsightArtifact:
    """Helper: create test insight."""
    if observation_reference is None:
        observation_reference = ["obs-001"]
    return InsightArtifact(
        id=insight_id,
        observation_reference=observation_reference,
        pattern=pattern,
        classification=classification,
        confidence=confidence,
    )


# ============================================================
# Schema Version Tests
# ============================================================


def test_schema_version_is_insight_v0_1():
    """Contract Frozen: schema_version = 'insight.v0.1' (Phase 3.14)."""
    assert INSIGHT_ARTIFACT_SCHEMA_VERSION == "insight.v0.1"


# ============================================================
# Enum Tests
# ============================================================


def test_insight_pattern_has_5_values():
    """Contract: 5 InsightPattern values (rule-based, NOT AI)."""
    assert len(InsightPattern) == 5
    assert InsightPattern.ANOMALY.value == "anomaly"
    assert InsightPattern.CORRELATION.value == "correlation"
    assert InsightPattern.TREND.value == "trend"
    assert InsightPattern.THRESHOLD.value == "threshold"
    assert InsightPattern.PATTERN.value == "pattern"


def test_insight_classification_has_5_values():
    """Contract: 5 InsightClassification values."""
    assert len(InsightClassification) == 5
    assert InsightClassification.INFO.value == "info"
    assert InsightClassification.WARNING.value == "warning"
    assert InsightClassification.CRITICAL.value == "critical"
    assert InsightClassification.ANOMALY.value == "anomaly"
    assert InsightClassification.TREND.value == "trend"


# ============================================================
# InsightArtifact Tests
# ============================================================


def test_insight_minimal_required():
    """Contract: 5 required fields construct a valid insight."""
    insight = _make_insight()
    assert insight.id == "insight-001"
    assert insight.observation_reference == ["obs-001"]
    assert insight.pattern == InsightPattern.PATTERN
    assert insight.classification == InsightClassification.INFO
    assert insight.confidence == 0.8
    assert insight.schema_version == "insight.v0.1"


def test_insight_default_explanation_metadata_empty_dict():
    """Contract: explanation_metadata default = {}."""
    insight = _make_insight()
    assert insight.explanation_metadata == {}


def test_insight_with_explanation_metadata():
    """Contract: explanation_metadata can be populated."""
    insight = InsightArtifact(
        id="insight-meta",
        observation_reference=["obs-x"],
        pattern=InsightPattern.ANOMALY,
        classification=InsightClassification.WARNING,
        confidence=0.9,
        explanation_metadata={
            "observation_count": 5,
            "severity": "high",
            "context": "runtime latency spike",
        },
    )
    assert insight.explanation_metadata["observation_count"] == 5


def test_insight_multiple_observation_references():
    """Contract: observation_reference supports multiple IDs."""
    insight = InsightArtifact(
        id="insight-corr",
        observation_reference=["obs-001", "obs-002", "obs-003"],
        pattern=InsightPattern.CORRELATION,
        classification=InsightClassification.INFO,
        confidence=0.7,
    )
    assert len(insight.observation_reference) == 3


def test_insight_is_frozen():
    """Contract: InsightArtifact is frozen (immutable)."""
    insight = _make_insight()
    with pytest.raises((AttributeError, Exception)):
        insight.id = "modified"  # type: ignore


def test_insight_equality_by_value():
    """Contract: equality by value (frozen dataclass)."""
    i1 = _make_insight(insight_id="insight-eq")
    i2 = _make_insight(insight_id="insight-eq")
    i3 = _make_insight(insight_id="insight-diff")
    assert i1 == i2
    assert i1 != i3


# ============================================================
# Validation Tests
# ============================================================


def test_insight_rejects_empty_id():
    """Validation: empty id raises ValueError."""
    with pytest.raises(ValueError, match="id must be non-empty"):
        InsightArtifact(
            id="",
            observation_reference=["obs-001"],
            pattern=InsightPattern.PATTERN,
            classification=InsightClassification.INFO,
            confidence=0.5,
        )


def test_insight_rejects_empty_observation_reference():
    """Validation: empty observation_reference raises ValueError."""
    with pytest.raises(ValueError, match="observation_reference must be non-empty"):
        InsightArtifact(
            id="insight-001",
            observation_reference=[],
            pattern=InsightPattern.PATTERN,
            classification=InsightClassification.INFO,
            confidence=0.5,
        )


def test_insight_rejects_confidence_below_0():
    """Validation: confidence < 0 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        InsightArtifact(
            id="insight-001",
            observation_reference=["obs-001"],
            pattern=InsightPattern.PATTERN,
            classification=InsightClassification.INFO,
            confidence=-0.1,
        )


def test_insight_rejects_confidence_above_1():
    """Validation: confidence > 1 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        InsightArtifact(
            id="insight-001",
            observation_reference=["obs-001"],
            pattern=InsightPattern.PATTERN,
            classification=InsightClassification.INFO,
            confidence=1.1,
        )


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_insight_accepts_boundary_confidence(confidence):
    """Validation: confidence at boundaries [0.0, 1.0] is valid."""
    insight = InsightArtifact(
        id="insight-bound",
        observation_reference=["obs-001"],
        pattern=InsightPattern.PATTERN,
        classification=InsightClassification.INFO,
        confidence=confidence,
    )
    assert insight.confidence == confidence


# ============================================================
# Serialization Tests
# ============================================================


def test_to_dict_basic():
    """to_dict(): basic structure with all fields."""
    insight = InsightArtifact(
        id="insight-dict",
        observation_reference=["obs-a", "obs-b"],
        pattern=InsightPattern.THRESHOLD,
        classification=InsightClassification.CRITICAL,
        confidence=0.95,
        explanation_metadata={"threshold": "100ms", "actual": "150ms"},
    )
    result = insight.to_dict()
    assert result["id"] == "insight-dict"
    assert result["observation_reference"] == ["obs-a", "obs-b"]
    assert result["pattern"] == "threshold"
    assert result["classification"] == "critical"
    assert result["confidence"] == 0.95
    assert result["schema_version"] == "insight.v0.1"


def test_to_dict_is_json_serializable():
    """to_dict(): JSON-serializable."""
    insight = _make_insight()
    serialized = json.dumps(insight.to_dict())
    deserialized = json.loads(serialized)
    assert deserialized["id"] == insight.id
    assert deserialized["pattern"] == insight.pattern.value


# ============================================================
# Forbidden Fields (Boundary Compliance)
# ============================================================


def test_insight_has_no_memory_fields():
    """Boundary: NO Memory fields (persistent, store, retention)."""
    insight = _make_insight()
    forbidden_attrs = ["memory", "retention", "persistent", "ttl", "expires_at"]
    for attr in forbidden_attrs:
        assert not hasattr(insight, attr), f"InsightArtifact should not have {attr!r}"


def test_insight_has_no_decision_fields():
    """Boundary: NO Decision fields (recommendation, action, planning)."""
    insight = _make_insight()
    forbidden_attrs = [
        "recommendation", "action", "decision", "plan",
        "next_step", "suggestion", "advice",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(insight, attr), f"InsightArtifact should not have {attr!r}"


def test_insight_has_no_ai_narrative_fields():
    """Boundary: NO AI narrative fields (summary, narrative, explanation_text)."""
    insight = _make_insight()
    forbidden_attrs = [
        "summary", "narrative", "explanation_text", "natural_language",
        "llm_response", "ai_summary",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(insight, attr), f"InsightArtifact should not have {attr!r}"


def test_insight_has_no_runtime_fields():
    """Boundary: NO Runtime fields (event, session, engine)."""
    insight = _make_insight()
    forbidden_attrs = ["runtime_event", "session", "engine", "orchestrator"]
    for attr in forbidden_attrs:
        assert not hasattr(insight, attr), f"InsightArtifact should not have {attr!r}"


def test_insight_has_no_ui_fields():
    """Boundary: NO UI fields (renderer, widget, panel)."""
    insight = _make_insight()
    forbidden_attrs = ["renderer", "widget", "panel", "theme", "layout"]
    for attr in forbidden_attrs:
        assert not hasattr(insight, attr), f"InsightArtifact should not have {attr!r}"


# ============================================================
# Parametrized Tests
# ============================================================


@pytest.mark.parametrize("pattern", list(InsightPattern))
def test_all_5_patterns_constructable(pattern):
    """Contract: All 5 InsightPattern values construct valid insights."""
    insight = InsightArtifact(
        id=f"insight-{pattern.value}",
        observation_reference=["obs-001"],
        pattern=pattern,
        classification=InsightClassification.INFO,
        confidence=0.5,
    )
    assert insight.pattern == pattern


@pytest.mark.parametrize("classification", list(InsightClassification))
def test_all_5_classifications_constructable(classification):
    """Contract: All 5 InsightClassification values construct valid insights."""
    insight = InsightArtifact(
        id=f"insight-{classification.value}",
        observation_reference=["obs-001"],
        pattern=InsightPattern.PATTERN,
        classification=classification,
        confidence=0.5,
    )
    assert insight.classification == classification