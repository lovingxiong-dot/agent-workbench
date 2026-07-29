"""tests/decision_support/consumer/test_decision_support_consumer.py — Phase 3.15 Step 3 Consumer Tests.

Tests:
- consume valid decision model
- reject invalid schema
- no mutation
- boundary compliance (no execution/memory/LLM)
"""
from __future__ import annotations

import json

import pytest

from tools.decision_support.adapter import InsightDecisionAdapter
from tools.decision_support.consumer import DecisionSupportConsumer
from tools.decision_support.contract import (
    DecisionArtifact,
    DecisionOption,
    DecisionStrategy,
)
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


def _make_insight() -> InsightArtifact:
    """Helper: standard test insight (from Phase 3.14)."""
    artifact = ObservationArtifact(
        id="obs-001",
        observation_type=ObservationType.PERFORMANCE,
        content={"event_type": "task.completed", "phase": "inference"},
        score=ObservationScore(relevance=0.9, confidence=0.9, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        task_id="",
    )
    return ObservationInsightAdapter().adapt(artifact)


def _make_decision() -> DecisionArtifact:
    """Helper: standard test decision (from Phase 3.15 Adapter)."""
    return InsightDecisionAdapter().adapt(_make_insight())


@pytest.fixture
def consumer() -> DecisionSupportConsumer:
    """Standard consumer instance."""
    return DecisionSupportConsumer()


# ============================================================
# Basic Produce Tests
# ============================================================


def test_produce_returns_dict(consumer):
    """produce(): returns dict (decision output)."""
    decision = _make_decision()
    output = consumer.produce(decision)
    assert isinstance(output, dict)


def test_produce_output_has_all_fields(consumer):
    """produce(): output has all 9 fields from decision."""
    decision = _make_decision()
    output = consumer.produce(decision)
    expected_fields = {
        "id", "insight_reference", "options", "strategy",
        "confidence", "rationale_metadata", "constraints_reference",
        "created_at", "schema_version",
    }
    assert set(output.keys()) == expected_fields


def test_produce_does_not_mutate_decision(consumer):
    """produce(): does NOT mutate decision (read-only)."""
    decision = _make_decision()
    original_id = decision.id
    original_strategy = decision.strategy
    consumer.produce(decision)
    assert decision.id == original_id
    assert decision.strategy == original_strategy


# ============================================================
# JSON Serialization Tests
# ============================================================


def test_produce_json_returns_string(consumer):
    """produce_json(): returns JSON string."""
    decision = _make_decision()
    output = consumer.produce_json(decision)
    assert isinstance(output, str)


def test_produce_json_is_parseable(consumer):
    """produce_json(): output is valid JSON."""
    decision = _make_decision()
    output = consumer.produce_json(decision)
    parsed = json.loads(output)
    assert parsed["id"] == decision.id
    assert parsed["strategy"] == decision.strategy.value


def test_produce_json_round_trip(consumer):
    """produce_json(): round-trip preserves all fields."""
    decision = _make_decision()
    json_str = consumer.produce_json(decision)
    parsed = json.loads(json_str)
    assert parsed["insight_reference"] == decision.insight_reference
    assert parsed["confidence"] == decision.confidence
    assert len(parsed["options"]) == len(decision.options)


# ============================================================
# Schema Validation Tests
# ============================================================


def test_produce_rejects_invalid_schema_version(consumer):
    """produce(): rejects decision with invalid schema_version."""
    invalid_decision = DecisionArtifact(
        id="decision-invalid",
        insight_reference=["insight-001"],
        options=[DecisionOption(id="opt-001", label="Test")],
        confidence=0.5,
    )
    object.__setattr__(invalid_decision, "schema_version", "invalid.v999.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce(invalid_decision)


def test_produce_json_rejects_invalid_schema_version(consumer):
    """produce_json(): rejects decision with invalid schema_version."""
    invalid_decision = DecisionArtifact(
        id="decision-invalid",
        insight_reference=["insight-001"],
        options=[DecisionOption(id="opt-001", label="Test")],
        confidence=0.5,
    )
    object.__setattr__(invalid_decision, "schema_version", "old.v0.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce_json(invalid_decision)


# ============================================================
# Pure Function Tests
# ============================================================


def test_produce_is_pure_function(consumer):
    """produce() is pure: same decision -> same output."""
    decision = _make_decision()
    output1 = consumer.produce(decision)
    output2 = consumer.produce(decision)
    assert output1 == output2


def test_consumer_is_stateless(consumer):
    """Consumer is stateless: multiple instances produce same output."""
    c1 = DecisionSupportConsumer()
    c2 = DecisionSupportConsumer()
    decision = _make_decision()
    assert c1.produce(decision) == c2.produce(decision)


# ============================================================
# Boundary Compliance Tests (Forbidden Couplings)
# ============================================================


def test_consumer_has_no_eventbus_reference(consumer):
    """Boundary: NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_insight_store_reference(consumer):
    """Boundary: NO Insight Store reference."""
    forbidden_attrs = ["insight_registry", "insight_store", "repository", "database", "cache"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_runtime_reference(consumer):
    """Boundary: NO Runtime reference."""
    forbidden_attrs = [
        "runtime", "event", "session", "engine", "orchestrator",
        "task", "execution",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_execution_reference(consumer):
    """Boundary: NO Execution reference (Decision != ActionExecutor)."""
    forbidden_attrs = [
        "execute", "executor", "action_executor", "run", "trigger",
        "schedule", "dispatch", "submit",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_memory_reference(consumer):
    """Boundary: NO Memory write reference."""
    forbidden_attrs = ["memory_write", "persist", "save", "store", "embed"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_llm_reference(consumer):
    """Boundary: NO LLM/AI autonomous reference."""
    forbidden_attrs = ["llm", "openai", "anthropic", "claude", "gpt", "language_model"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_planner_reference(consumer):
    """Boundary: NO Planner/Workflow reference."""
    forbidden_attrs = ["planner", "workflow", "plan", "agent_planner"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_subscribe_method(consumer):
    """Boundary: NO subscribe/register/publish methods."""
    assert not hasattr(consumer, "subscribe")
    assert not hasattr(consumer, "register")
    assert not hasattr(consumer, "publish")


def test_consumer_has_no_storage_methods(consumer):
    """Boundary: NO storage methods."""
    forbidden_methods = ["save", "load", "persist", "flush", "sync", "cache"]
    for method in forbidden_methods:
        assert not hasattr(consumer, method), f"Consumer should not have {method!r}"


def test_consumer_has_no_insight_dependency(consumer):
    """Boundary: Consumer does NOT depend on InsightArtifact (only Decision)."""
    import inspect
    source = inspect.getsource(consumer.produce)
    assert "InsightArtifact" not in source, "Consumer should not reference InsightArtifact"