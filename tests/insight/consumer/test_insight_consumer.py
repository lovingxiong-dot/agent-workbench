"""tests/insight/consumer/test_insight_consumer.py — Phase 3.14 Step 3 Consumer Tests.

Tests (user spec):
- consume valid model
- reject invalid schema
- no mutation
"""
from __future__ import annotations

import json

import pytest

from tools.insight.adapter import ObservationInsightAdapter
from tools.insight.consumer import InsightConsumer
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


def _make_artifact() -> ObservationArtifact:
    """Helper: standard test artifact."""
    return ObservationArtifact(
        id="obs-001",
        observation_type=ObservationType.PERFORMANCE,
        content={"event_type": "task.completed", "phase": "inference"},
        score=ObservationScore(relevance=0.9, confidence=0.9, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        task_id="",  # No task_id (no correlation)
    )


def _make_insight() -> InsightArtifact:
    """Helper: standard test insight (from Adapter)."""
    adapter = ObservationInsightAdapter()
    return adapter.adapt(_make_artifact())


@pytest.fixture
def consumer() -> InsightConsumer:
    """Standard consumer instance."""
    return InsightConsumer()


# ============================================================
# Basic Produce Tests
# ============================================================


def test_produce_returns_dict(consumer):
    """produce(): returns dict (insight output)."""
    insight = _make_insight()
    output = consumer.produce(insight)
    assert isinstance(output, dict)


def test_produce_output_has_all_fields(consumer):
    """produce(): output has all 8 fields from insight."""
    insight = _make_insight()
    output = consumer.produce(insight)
    expected_fields = {
        "id", "observation_reference", "pattern", "classification",
        "confidence", "explanation_metadata", "created_at", "schema_version",
    }
    assert set(output.keys()) == expected_fields


def test_produce_does_not_mutate_insight(consumer):
    """produce(): does NOT mutate insight (read-only)."""
    insight = _make_insight()
    original_id = insight.id
    original_pattern = insight.pattern
    consumer.produce(insight)
    assert insight.id == original_id
    assert insight.pattern == original_pattern


# ============================================================
# JSON Serialization Tests
# ============================================================


def test_produce_json_returns_string(consumer):
    """produce_json(): returns JSON string."""
    insight = _make_insight()
    output = consumer.produce_json(insight)
    assert isinstance(output, str)


def test_produce_json_is_parseable(consumer):
    """produce_json(): output is valid JSON."""
    insight = _make_insight()
    output = consumer.produce_json(insight)
    parsed = json.loads(output)
    assert parsed["id"] == insight.id
    assert parsed["pattern"] == insight.pattern.value


def test_produce_json_round_trip(consumer):
    """produce_json(): round-trip preserves all fields."""
    insight = _make_insight()
    json_str = consumer.produce_json(insight)
    parsed = json.loads(json_str)
    assert parsed["observation_reference"] == insight.observation_reference
    assert parsed["classification"] == insight.classification.value
    assert parsed["confidence"] == insight.confidence


# ============================================================
# Schema Validation Tests
# ============================================================


def test_produce_rejects_invalid_schema_version(consumer):
    """produce(): rejects insight with invalid schema_version."""
    invalid_insight = InsightArtifact(
        id="insight-invalid",
        observation_reference=["obs-001"],
        pattern=InsightPattern.PATTERN,
        classification=InsightClassification.INFO,
        confidence=0.5,
    )
    object.__setattr__(invalid_insight, "schema_version", "invalid.v999.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce(invalid_insight)


def test_produce_json_rejects_invalid_schema_version(consumer):
    """produce_json(): rejects insight with invalid schema_version."""
    invalid_insight = InsightArtifact(
        id="insight-invalid",
        observation_reference=["obs-001"],
        pattern=InsightPattern.PATTERN,
        classification=InsightClassification.INFO,
        confidence=0.5,
    )
    object.__setattr__(invalid_insight, "schema_version", "old.v0.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce_json(invalid_insight)


# ============================================================
# Pure Function Tests
# ============================================================


def test_produce_is_pure_function(consumer):
    """produce() is pure: same insight -> same output."""
    insight = _make_insight()
    output1 = consumer.produce(insight)
    output2 = consumer.produce(insight)
    assert output1 == output2


def test_consumer_is_stateless(consumer):
    """Consumer is stateless: multiple instances produce same output."""
    c1 = InsightConsumer()
    c2 = InsightConsumer()
    insight = _make_insight()
    assert c1.produce(insight) == c2.produce(insight)


# ============================================================
# Boundary Compliance Tests (Forbidden Couplings)
# ============================================================


def test_consumer_has_no_eventbus_reference(consumer):
    """Boundary: Consumer has NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_observation_store_reference(consumer):
    """Boundary: Consumer has NO Observation Store (Registry) reference."""
    forbidden_attrs = ["registry", "store", "repository", "database", "cache"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_runtime_reference(consumer):
    """Boundary: Consumer has NO Runtime reference."""
    forbidden_attrs = [
        "runtime", "event", "session", "engine", "orchestrator",
        "task", "execution",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_decision_reference(consumer):
    """Boundary: Consumer has NO Decision reference (Insight != Decision)."""
    forbidden_attrs = [
        "decision", "recommendation", "action", "plan", "planner",
        "next_step", "advice",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_memory_reference(consumer):
    """Boundary: Consumer has NO Memory reference (Insight != Memory)."""
    forbidden_attrs = ["memory", "vector_store", "embedding", "retrieval", "persistent"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_llm_reference(consumer):
    """Boundary: Consumer has NO LLM/AI reference."""
    forbidden_attrs = ["llm", "openai", "anthropic", "claude", "gpt", "language_model"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_subscribe_method(consumer):
    """Boundary: Consumer has no subscribe() method."""
    assert not hasattr(consumer, "subscribe")
    assert not hasattr(consumer, "register")
    assert not hasattr(consumer, "publish")


def test_consumer_has_no_storage_methods(consumer):
    """Boundary: Consumer has no storage methods."""
    forbidden_methods = ["save", "load", "persist", "flush", "sync", "cache"]
    for method in forbidden_methods:
        assert not hasattr(consumer, method), f"Consumer should not have {method!r}"


def test_consumer_has_no_observation_dependency(consumer):
    """Boundary: Consumer does NOT depend on ObservationArtifact (only Insight)."""
    import inspect
    source = inspect.getsource(consumer.produce)
    assert "ObservationArtifact" not in source, "Consumer should not reference ObservationArtifact"