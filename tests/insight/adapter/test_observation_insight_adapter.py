"""tests/insight/adapter/test_observation_insight_adapter.py — Phase 3.14 Step 2 Tests.

Tests:
- artifact mapping (ObservationArtifact -> InsightArtifact)
- pattern detection (rule-based, NOT AI)
- classification (rule-based, NOT AI)
- confidence derivation
- explanation metadata
- schema version handling
- pure function (deterministic)
- stateless
- boundary compliance (no AI/LLM/Memory/Decision)
"""
from __future__ import annotations

import pytest

from tools.insight.adapter import ObservationInsightAdapter
from tools.insight.contract import (
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)
from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)


def _make_artifact(
    artifact_id: str = "obs-001",
    observation_type: ObservationType = ObservationType.PERFORMANCE,
    confidence: float = 0.9,
    relevance: float = 0.9,
    content: dict = None,
    task_id: str = "task-1",
) -> ObservationArtifact:
    """Helper: create test artifact."""
    if content is None:
        content = {"event_type": "task.completed", "phase": "inference"}
    return ObservationArtifact(
        id=artifact_id,
        observation_type=observation_type,
        content=content,
        score=ObservationScore(
            relevance=relevance,
            confidence=confidence,
            stability=1.0,
        ),
        source=ObservationSource.RUNTIME,
        created_by="test",
        task_id=task_id,
    )


@pytest.fixture
def adapter() -> ObservationInsightAdapter:
    """Standard adapter instance."""
    return ObservationInsightAdapter()


# ============================================================
# Basic Mapping Tests
# ============================================================


def test_adapt_returns_insight_artifact(adapter):
    """adapt() returns InsightArtifact."""
    artifact = _make_artifact()
    insight = adapter.adapt(artifact)
    assert isinstance(insight, InsightArtifact)


def test_adapt_id_includes_artifact_id(adapter):
    """adapt(): insight id = '{prefix}-{artifact.id}'."""
    artifact = _make_artifact(artifact_id="obs-xyz")
    insight = adapter.adapt(artifact)
    assert insight.id == "insight-obs-xyz"


def test_adapt_accepts_custom_id_prefix(adapter):
    """adapt(): custom id_prefix."""
    artifact = _make_artifact()
    insight = adapter.adapt(artifact, id_prefix="myapp")
    assert insight.id.startswith("myapp-")


def test_adapt_observation_reference_includes_artifact_id(adapter):
    """adapt(): observation_reference = [artifact.id]."""
    artifact = _make_artifact(artifact_id="obs-ref")
    insight = adapter.adapt(artifact)
    assert insight.observation_reference == ["obs-ref"]


# ============================================================
# Pattern Detection Tests (Rule-based, NOT AI)
# ============================================================


def test_adapt_detects_anomaly_pattern_for_failed_event(adapter):
    """Pattern: failed/error event type -> ANOMALY."""
    artifact = _make_artifact(
        observation_type=ObservationType.EVENT,
        content={"event_type": "task.failed", "error": "timeout"},
    )
    insight = adapter.adapt(artifact)
    assert insight.pattern == InsightPattern.ANOMALY


def test_adapt_detects_threshold_pattern_for_low_confidence(adapter):
    """Pattern: confidence < 0.4 -> THRESHOLD."""
    artifact = _make_artifact(confidence=0.3)
    insight = adapter.adapt(artifact)
    assert insight.pattern == InsightPattern.THRESHOLD


def test_adapt_detects_correlation_pattern_for_task_id(adapter):
    """Pattern: has task_id -> CORRELATION."""
    artifact = _make_artifact(task_id="task-abc")
    insight = adapter.adapt(artifact)
    assert insight.pattern == InsightPattern.CORRELATION


def test_adapt_detects_trend_pattern_for_performance(adapter):
    """Pattern: PERFORMANCE + high confidence + NO task_id -> TREND."""
    artifact = _make_artifact(
        observation_type=ObservationType.PERFORMANCE,
        confidence=0.9,
        task_id="",  # No task_id (correlation takes priority otherwise)
    )
    insight = adapter.adapt(artifact)
    assert insight.pattern == InsightPattern.TREND


def test_adapt_default_pattern(adapter):
    """Pattern: default fallback -> PATTERN."""
    artifact = _make_artifact(
        observation_type=ObservationType.LIFECYCLE,
        confidence=0.9,
        task_id="",
    )
    insight = adapter.adapt(artifact)
    assert insight.pattern == InsightPattern.PATTERN


# ============================================================
# Classification Tests (Rule-based, NOT AI)
# ============================================================


def test_adapt_classifies_critical_for_low_confidence(adapter):
    """Classification: confidence < 0.4 -> CRITICAL."""
    artifact = _make_artifact(confidence=0.3)
    insight = adapter.adapt(artifact)
    assert insight.classification == InsightClassification.CRITICAL


def test_adapt_classifies_anomaly_for_anomaly_pattern(adapter):
    """Classification: ANOMALY pattern -> ANOMALY."""
    artifact = _make_artifact(
        observation_type=ObservationType.EVENT,
        content={"event_type": "task.failed"},
        confidence=0.9,
    )
    insight = adapter.adapt(artifact)
    assert insight.classification == InsightClassification.ANOMALY


def test_adapt_classifies_trend_for_trend_pattern(adapter):
    """Classification: TREND pattern -> TREND."""
    artifact = _make_artifact(
        observation_type=ObservationType.PERFORMANCE,
        confidence=0.9,
        task_id="",  # No task_id (correlation takes priority otherwise)
    )
    insight = adapter.adapt(artifact)
    assert insight.classification == InsightClassification.TREND


def test_adapt_classifies_warning_for_medium_confidence(adapter):
    """Classification: 0.4 <= confidence < 0.7 -> WARNING."""
    artifact = _make_artifact(
        observation_type=ObservationType.LIFECYCLE,
        confidence=0.5,
        task_id="",
    )
    insight = adapter.adapt(artifact)
    assert insight.classification == InsightClassification.WARNING


def test_adapt_classifies_info_for_high_confidence(adapter):
    """Classification: high confidence -> INFO."""
    artifact = _make_artifact(
        observation_type=ObservationType.LIFECYCLE,
        confidence=0.95,
        task_id="",
    )
    insight = adapter.adapt(artifact)
    assert insight.classification == InsightClassification.INFO


# ============================================================
# Confidence Derivation Tests
# ============================================================


def test_adapt_confidence_derived_from_scores(adapter):
    """Confidence: derived from relevance * 0.5 + confidence * 0.5."""
    artifact = _make_artifact(relevance=0.8, confidence=0.8)
    insight = adapter.adapt(artifact)
    expected = round(0.8 * 0.5 + 0.8 * 0.5, 4)
    assert insight.confidence == expected


def test_adapt_confidence_in_valid_range(adapter):
    """Confidence: always in [0.0, 1.0]."""
    for relevance in [0.0, 0.5, 1.0]:
        for confidence in [0.0, 0.5, 1.0]:
            artifact = _make_artifact(relevance=relevance, confidence=confidence)
            insight = adapter.adapt(artifact)
            assert 0.0 <= insight.confidence <= 1.0


# ============================================================
# Explanation Metadata Tests
# ============================================================


def test_adapt_explanation_metadata_includes_source_info(adapter):
    """Metadata: includes source_schema_version, source_id, source_type."""
    artifact = _make_artifact(artifact_id="obs-meta")
    insight = adapter.adapt(artifact)
    metadata = insight.explanation_metadata
    assert metadata["source_schema_version"] == "observation.v0.1"
    assert metadata["source_id"] == "obs-meta"
    assert metadata["source_observation_type"] == "performance"


def test_adapt_explanation_metadata_includes_pattern(adapter):
    """Metadata: includes detected_pattern."""
    artifact = _make_artifact(
        observation_type=ObservationType.PERFORMANCE,
        confidence=0.9,
        task_id="",  # No task_id (otherwise correlation)
    )
    insight = adapter.adapt(artifact)
    assert insight.explanation_metadata["detected_pattern"] == "trend"


def test_adapt_explanation_metadata_marked_rule_based(adapter):
    """Metadata: explicitly marked as rule_based=True (NOT AI)."""
    artifact = _make_artifact()
    insight = adapter.adapt(artifact)
    assert insight.explanation_metadata["rule_based"] is True


def test_adapt_explanation_metadata_includes_task_id_when_present(adapter):
    """Metadata: includes source_task_id when artifact has task_id."""
    artifact = _make_artifact(task_id="task-xyz")
    insight = adapter.adapt(artifact)
    assert insight.explanation_metadata["source_task_id"] == "task-xyz"


def test_adapt_explanation_metadata_includes_event_type(adapter):
    """Metadata: includes source_event_type when content has event_type."""
    artifact = _make_artifact(content={"event_type": "task.completed", "phase": "inference"})
    insight = adapter.adapt(artifact)
    assert insight.explanation_metadata["source_event_type"] == "task.completed"


# ============================================================
# Schema Version Tests
# ============================================================


def test_adapt_output_uses_insight_schema_version(adapter):
    """Output: uses frozen 'insight.v0.1'."""
    artifact = _make_artifact()
    insight = adapter.adapt(artifact)
    assert insight.schema_version == "insight.v0.1"


# ============================================================
# Pure Function Tests (Deterministic + Stateless)
# ============================================================


def test_adapt_is_pure_function(adapter):
    """adapt() is pure: same artifact -> same insight structure."""
    artifact = _make_artifact(artifact_id="obs-pure")
    i1 = adapter.adapt(artifact)
    i2 = adapter.adapt(artifact)
    assert i1.id == i2.id
    assert i1.pattern == i2.pattern
    assert i1.classification == i2.classification
    assert i1.confidence == i2.confidence
    assert i1.observation_reference == i2.observation_reference
    assert i1.schema_version == i2.schema_version


def test_adapter_is_stateless(adapter):
    """Adapter is stateless: multiple instances produce same output."""
    a1 = ObservationInsightAdapter()
    a2 = ObservationInsightAdapter()
    artifact = _make_artifact()
    i1 = a1.adapt(artifact)
    i2 = a2.adapt(artifact)
    assert i1 == i2


# ============================================================
# Boundary Compliance Tests
# ============================================================


def test_adapter_has_no_eventbus_reference(adapter):
    """Boundary: Adapter has NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_storage_methods(adapter):
    """Boundary: Adapter has NO storage methods (cache, save, load)."""
    forbidden_methods = ["save", "load", "cache", "persist", "flush", "sync"]
    for method in forbidden_methods:
        assert not hasattr(adapter, method), f"Adapter should not have {method!r}"


def test_adapter_has_no_llm_dependency(adapter):
    """Boundary: Adapter has NO LLM/AI dependency."""
    forbidden_attrs = [
        "llm", "openai", "anthropic", "claude", "gpt",
        "language_model", "model", "ml_model",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_memory_dependency(adapter):
    """Boundary: Adapter has NO Memory dependency."""
    forbidden_attrs = ["memory", "vector_store", "embedding", "retrieval"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_decision_dependency(adapter):
    """Boundary: Adapter has NO Decision/Recommendation dependency."""
    forbidden_attrs = ["decision", "recommendation", "action", "plan", "planner"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_runtime_dependency(adapter):
    """Boundary: Adapter has no Runtime dependency."""
    forbidden_attrs = ["runtime", "event", "session", "engine", "orchestrator"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_ui_dependency(adapter):
    """Boundary: Adapter has no UI dependency."""
    forbidden_attrs = ["renderer", "widget", "panel", "theme", "layout"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_subscribe_method(adapter):
    """Boundary: Adapter has no subscribe() method."""
    assert not hasattr(adapter, "subscribe")
    assert not hasattr(adapter, "register")
    assert not hasattr(adapter, "publish")