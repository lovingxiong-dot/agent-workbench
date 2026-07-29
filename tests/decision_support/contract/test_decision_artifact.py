"""tests/decision_support/contract/test_decision_artifact.py — Phase 3.15 DecisionArtifact Tests.

Tests:
- Schema version (frozen)
- 4 main fields + auto fields
- DecisionOption: id, label, score [0.0, 1.0]
- Required fields validation
- Frozen dataclass
- to_dict serialization
- Forbidden fields (no execution/scheduling/LLM autonomous)
"""
from __future__ import annotations

import json

import pytest

from tools.decision_support.contract import (
    DECISION_ARTIFACT_SCHEMA_VERSION,
    DecisionArtifact,
    DecisionOption,
    DecisionStrategy,
)


def _make_option(
    option_id: str = "opt-001",
    label: str = "Option 1",
    score: float = 0.7,
) -> DecisionOption:
    """Helper: create test option."""
    return DecisionOption(id=option_id, label=label, score=score)


def _make_decision(
    decision_id: str = "decision-001",
    insight_reference: list = None,
    options: list = None,
    confidence: float = 0.7,
    strategy: DecisionStrategy = DecisionStrategy.BALANCED,
) -> DecisionArtifact:
    """Helper: create test decision."""
    if insight_reference is None:
        insight_reference = ["insight-001"]
    if options is None:
        options = [_make_option()]
    return DecisionArtifact(
        id=decision_id,
        insight_reference=insight_reference,
        options=options,
        confidence=confidence,
        strategy=strategy,
    )


# ============================================================
# Schema Version Tests
# ============================================================


def test_schema_version_is_decision_v0_1():
    """Contract Frozen: schema_version = 'decision.v0.1' (Phase 3.15)."""
    assert DECISION_ARTIFACT_SCHEMA_VERSION == "decision.v0.1"


# ============================================================
# DecisionStrategy Tests
# ============================================================


def test_decision_strategy_has_5_values():
    """Contract: 5 DecisionStrategy values (rule-based, NOT AI autonomous)."""
    assert len(DecisionStrategy) == 5
    assert DecisionStrategy.CONSERVATIVE.value == "conservative"
    assert DecisionStrategy.BALANCED.value == "balanced"
    assert DecisionStrategy.AGGRESSIVE.value == "aggressive"
    assert DecisionStrategy.DEFENSIVE.value == "defensive"
    assert DecisionStrategy.NEUTRAL.value == "neutral"


# ============================================================
# DecisionOption Tests
# ============================================================


def test_decision_option_minimal_required():
    """DecisionOption: id, label required."""
    option = _make_option()
    assert option.id == "opt-001"
    assert option.label == "Option 1"
    assert option.score == 0.7


def test_decision_option_default_score_zero():
    """DecisionOption: default score = 0.0."""
    option = DecisionOption(id="opt-002", label="Test")
    assert option.score == 0.0


def test_decision_option_default_rationale_empty():
    """DecisionOption: default rationale = empty string."""
    option = DecisionOption(id="opt-002", label="Test")
    assert option.rationale == ""


def test_decision_option_rejects_empty_id():
    """Validation: empty id raises ValueError."""
    with pytest.raises(ValueError, match="id must be non-empty"):
        DecisionOption(id="", label="Test")


def test_decision_option_rejects_empty_label():
    """Validation: empty label raises ValueError."""
    with pytest.raises(ValueError, match="label must be non-empty"):
        DecisionOption(id="opt-001", label="")


def test_decision_option_rejects_score_below_0():
    """Validation: score < 0 raises ValueError."""
    with pytest.raises(ValueError, match="score must be in"):
        DecisionOption(id="opt-001", label="Test", score=-0.1)


def test_decision_option_rejects_score_above_1():
    """Validation: score > 1 raises ValueError."""
    with pytest.raises(ValueError, match="score must be in"):
        DecisionOption(id="opt-001", label="Test", score=1.1)


@pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
def test_decision_option_accepts_boundary_score(score):
    """Validation: score at boundaries [0.0, 1.0] is valid."""
    option = DecisionOption(id="opt-bound", label="Test", score=score)
    assert option.score == score


def test_decision_option_is_frozen():
    """DecisionOption: is frozen (immutable)."""
    option = _make_option()
    with pytest.raises((AttributeError, Exception)):
        option.id = "modified"  # type: ignore


# ============================================================
# DecisionArtifact Tests
# ============================================================


def test_decision_minimal_required():
    """DecisionArtifact: minimal required fields."""
    decision = _make_decision()
    assert decision.id == "decision-001"
    assert decision.insight_reference == ["insight-001"]
    assert len(decision.options) == 1
    assert decision.confidence == 0.7
    assert decision.strategy == DecisionStrategy.BALANCED
    assert decision.schema_version == "decision.v0.1"


def test_decision_default_rationale_metadata_empty():
    """DecisionArtifact: default rationale_metadata = {}."""
    decision = _make_decision()
    assert decision.rationale_metadata == {}


def test_decision_default_constraints_reference_empty():
    """DecisionArtifact: default constraints_reference = {}."""
    decision = _make_decision()
    assert decision.constraints_reference == {}


def test_decision_with_rationale_metadata():
    """DecisionArtifact: rationale_metadata can be populated."""
    decision = DecisionArtifact(
        id="decision-meta",
        insight_reference=["insight-001"],
        options=[_make_option()],
        confidence=0.8,
        rationale_metadata={
            "rule_based": True,
            "decision_basis": "anomaly detected",
            "evaluation_criteria": ["risk", "reliability", "cost"],
        },
    )
    assert decision.rationale_metadata["rule_based"] is True
    assert decision.rationale_metadata["decision_basis"] == "anomaly detected"


def test_decision_with_constraints_reference():
    """DecisionArtifact: constraints_reference can be populated."""
    decision = DecisionArtifact(
        id="decision-constraint",
        insight_reference=["insight-001"],
        options=[_make_option()],
        confidence=0.8,
        constraints_reference={
            "budget_max": 1000,
            "time_max_ms": 5000,
            "risk_tolerance": "low",
        },
    )
    assert decision.constraints_reference["budget_max"] == 1000


def test_decision_with_multiple_options():
    """DecisionArtifact: supports multiple options."""
    options = [
        _make_option(option_id="opt-a", label="Option A"),
        _make_option(option_id="opt-b", label="Option B"),
        _make_option(option_id="opt-c", label="Option C"),
    ]
    decision = _make_decision(options=options)
    assert len(decision.options) == 3


def test_decision_with_multiple_insight_references():
    """DecisionArtifact: supports multiple insight references."""
    decision = _make_decision(insight_reference=["insight-a", "insight-b", "insight-c"])
    assert len(decision.insight_reference) == 3


def test_decision_is_frozen():
    """DecisionArtifact: is frozen (immutable)."""
    decision = _make_decision()
    with pytest.raises((AttributeError, Exception)):
        decision.id = "modified"  # type: ignore


def test_decision_equality_by_value():
    """DecisionArtifact: equality by value (frozen dataclass)."""
    d1 = _make_decision(decision_id="decision-eq")
    d2 = _make_decision(decision_id="decision-eq")
    d3 = _make_decision(decision_id="decision-diff")
    assert d1 == d2
    assert d1 != d3


# ============================================================
# Validation Tests
# ============================================================


def test_decision_rejects_empty_id():
    """Validation: empty id raises ValueError."""
    with pytest.raises(ValueError, match="id must be non-empty"):
        DecisionArtifact(
            id="",
            insight_reference=["insight-001"],
            options=[_make_option()],
            confidence=0.5,
        )


def test_decision_rejects_empty_insight_reference():
    """Validation: empty insight_reference raises ValueError."""
    with pytest.raises(ValueError, match="insight_reference must be non-empty"):
        DecisionArtifact(
            id="decision-001",
            insight_reference=[],
            options=[_make_option()],
            confidence=0.5,
        )


def test_decision_rejects_empty_options():
    """Validation: empty options raises ValueError."""
    with pytest.raises(ValueError, match="options must be non-empty"):
        DecisionArtifact(
            id="decision-001",
            insight_reference=["insight-001"],
            options=[],
            confidence=0.5,
        )


def test_decision_rejects_confidence_below_0():
    """Validation: confidence < 0 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        DecisionArtifact(
            id="decision-001",
            insight_reference=["insight-001"],
            options=[_make_option()],
            confidence=-0.1,
        )


def test_decision_rejects_confidence_above_1():
    """Validation: confidence > 1 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        DecisionArtifact(
            id="decision-001",
            insight_reference=["insight-001"],
            options=[_make_option()],
            confidence=1.1,
        )


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_decision_accepts_boundary_confidence(confidence):
    """Validation: confidence at boundaries [0.0, 1.0] is valid."""
    decision = DecisionArtifact(
        id="decision-bound",
        insight_reference=["insight-001"],
        options=[_make_option()],
        confidence=confidence,
    )
    assert decision.confidence == confidence


# ============================================================
# Serialization Tests
# ============================================================


def test_decision_to_dict_basic():
    """to_dict(): basic structure with all fields."""
    options = [
        DecisionOption(id="opt-a", label="Option A", score=0.8),
        DecisionOption(id="opt-b", label="Option B", score=0.6),
    ]
    decision = DecisionArtifact(
        id="decision-dict",
        insight_reference=["insight-001", "insight-002"],
        options=options,
        strategy=DecisionStrategy.BALANCED,
        confidence=0.85,
        rationale_metadata={"rule_based": True},
        constraints_reference={"budget_max": 1000},
    )
    result = decision.to_dict()
    assert result["id"] == "decision-dict"
    assert result["insight_reference"] == ["insight-001", "insight-002"]
    assert len(result["options"]) == 2
    assert result["strategy"] == "balanced"
    assert result["confidence"] == 0.85
    assert result["schema_version"] == "decision.v0.1"


def test_decision_to_dict_is_json_serializable():
    """to_dict(): JSON-serializable."""
    decision = _make_decision()
    serialized = json.dumps(decision.to_dict())
    deserialized = json.loads(serialized)
    assert deserialized["id"] == decision.id
    assert deserialized["strategy"] == decision.strategy.value


# ============================================================
# Forbidden Fields (Boundary Compliance)
# ============================================================


def test_decision_has_no_execution_fields():
    """Boundary: NO Execution fields (execute, schedule, dispatch, run)."""
    decision = _make_decision()
    forbidden_attrs = ["execute", "execution", "schedule", "dispatch", "run", "trigger"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_task_mutation_fields():
    """Boundary: NO Task mutation fields (submit, update, cancel)."""
    decision = _make_decision()
    forbidden_attrs = ["submit", "update", "cancel", "mutate", "modify"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_memory_write_fields():
    """Boundary: NO Memory write fields (write, persist, save)."""
    decision = _make_decision()
    forbidden_attrs = ["write", "persist", "save", "store", "memory_write"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_capability_routing_fields():
    """Boundary: NO Capability routing fields (route, capability, executor)."""
    decision = _make_decision()
    forbidden_attrs = ["route", "capability", "executor", "router", "action_executor"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_llm_autonomous_fields():
    """Boundary: NO LLM autonomous decision fields (llm, ai_decision, autonomous)."""
    decision = _make_decision()
    forbidden_attrs = [
        "llm_decision", "ai_decision", "autonomous",
        "model_decision", "gpt_decision",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_planner_fields():
    """Boundary: NO Planner fields (plan, planner, workflow)."""
    decision = _make_decision()
    forbidden_attrs = ["plan", "planner", "workflow", "agent_planner", "workflow_engine"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_runtime_fields():
    """Boundary: NO Runtime fields (runtime, session, engine, event)."""
    decision = _make_decision()
    forbidden_attrs = ["runtime", "session", "engine", "orchestrator", "event"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


def test_decision_has_no_ui_fields():
    """Boundary: NO UI fields (renderer, widget, panel)."""
    decision = _make_decision()
    forbidden_attrs = ["renderer", "widget", "panel", "theme", "layout"]
    for attr in forbidden_attrs:
        assert not hasattr(decision, attr), f"DecisionArtifact should not have {attr!r}"


# ============================================================
# Parametrized Tests
# ============================================================


@pytest.mark.parametrize("strategy", list(DecisionStrategy))
def test_all_5_strategies_constructable(strategy):
    """Contract: All 5 DecisionStrategy values construct valid decisions."""
    decision = DecisionArtifact(
        id=f"decision-{strategy.value}",
        insight_reference=["insight-001"],
        options=[_make_option()],
        confidence=0.5,
        strategy=strategy,
    )
    assert decision.strategy == strategy