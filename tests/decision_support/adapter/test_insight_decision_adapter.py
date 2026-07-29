"""tests/decision_support/adapter/test_insight_decision_adapter.py — Phase 3.15 Step 2 Tests.

Tests:
- insight mapping (InsightArtifact -> DecisionArtifact)
- strategy selection (rule-based)
- option generation (rule-based)
- confidence derivation
- rationale + constraints metadata
- pure function + stateless
- boundary compliance (no execution/LLM/etc)
"""
from __future__ import annotations

import pytest

from tools.decision_support.adapter import InsightDecisionAdapter
from tools.decision_support.contract import (
    DecisionArtifact,
    DecisionStrategy,
)
from tools.insight.contract import (
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)


def _make_insight(
    insight_id: str = "insight-001",
    pattern: InsightPattern = InsightPattern.PATTERN,
    classification: InsightClassification = InsightClassification.INFO,
    confidence: float = 0.8,
    observation_reference: list = None,
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


@pytest.fixture
def adapter() -> InsightDecisionAdapter:
    """Standard adapter instance."""
    return InsightDecisionAdapter()


# ============================================================
# Basic Mapping Tests
# ============================================================


def test_adapt_returns_decision_artifact(adapter):
    """adapt() returns DecisionArtifact."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert isinstance(decision, DecisionArtifact)


def test_adapt_id_includes_insight_id(adapter):
    """adapt(): decision id = '{prefix}-{insight.id}'."""
    insight = _make_insight(insight_id="insight-xyz")
    decision = adapter.adapt(insight)
    assert decision.id == "decision-insight-xyz"


def test_adapt_insight_reference_includes_observation(adapter):
    """adapt(): insight_reference = insight.observation_reference."""
    insight = _make_insight(observation_reference=["obs-a", "obs-b"])
    decision = adapter.adapt(insight)
    assert decision.insight_reference == ["obs-a", "obs-b"]


def test_adapt_generates_at_least_one_option(adapter):
    """adapt(): generates at least one DecisionOption."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert len(decision.options) >= 1


# ============================================================
# Strategy Selection Tests (Rule-based, NOT AI autonomous)
# ============================================================


def test_adapt_selects_conservative_for_critical(adapter):
    """Strategy: CRITICAL classification -> CONSERVATIVE."""
    insight = _make_insight(classification=InsightClassification.CRITICAL)
    decision = adapter.adapt(insight)
    assert decision.strategy == DecisionStrategy.CONSERVATIVE


def test_adapt_selects_conservative_for_anomaly(adapter):
    """Strategy: ANOMALY classification -> CONSERVATIVE."""
    insight = _make_insight(classification=InsightClassification.ANOMALY)
    decision = adapter.adapt(insight)
    assert decision.strategy == DecisionStrategy.CONSERVATIVE


def test_adapt_selects_defensive_for_warning(adapter):
    """Strategy: WARNING classification -> DEFENSIVE."""
    insight = _make_insight(classification=InsightClassification.WARNING)
    decision = adapter.adapt(insight)
    assert decision.strategy == DecisionStrategy.DEFENSIVE


def test_adapt_selects_balanced_for_trend(adapter):
    """Strategy: TREND classification -> BALANCED."""
    insight = _make_insight(classification=InsightClassification.TREND)
    decision = adapter.adapt(insight)
    assert decision.strategy == DecisionStrategy.BALANCED


def test_adapt_selects_neutral_for_info(adapter):
    """Strategy: INFO classification -> NEUTRAL."""
    insight = _make_insight(classification=InsightClassification.INFO)
    decision = adapter.adapt(insight)
    assert decision.strategy == DecisionStrategy.NEUTRAL


# ============================================================
# Option Generation Tests (Rule-based, NOT LLM)
# ============================================================


def test_adapt_generates_anomaly_options(adapter):
    """Options: ANOMALY pattern -> investigate/mitigate/accept."""
    insight = _make_insight(pattern=InsightPattern.ANOMALY)
    decision = adapter.adapt(insight)
    option_ids = [opt.id for opt in decision.options]
    assert "opt-investigate" in option_ids
    assert "opt-mitigate" in option_ids
    assert "opt-accept" in option_ids


def test_adapt_generates_threshold_options(adapter):
    """Options: THRESHOLD pattern -> review/adjust/escalate."""
    insight = _make_insight(pattern=InsightPattern.THRESHOLD)
    decision = adapter.adapt(insight)
    option_ids = [opt.id for opt in decision.options]
    assert "opt-review" in option_ids
    assert "opt-adjust" in option_ids
    assert "opt-escalate" in option_ids


def test_adapt_generates_correlation_options(adapter):
    """Options: CORRELATION pattern -> link/verify."""
    insight = _make_insight(pattern=InsightPattern.CORRELATION)
    decision = adapter.adapt(insight)
    option_ids = [opt.id for opt in decision.options]
    assert "opt-link" in option_ids
    assert "opt-verify" in option_ids


def test_adapt_generates_trend_options(adapter):
    """Options: TREND pattern -> monitor/predict."""
    insight = _make_insight(pattern=InsightPattern.TREND)
    decision = adapter.adapt(insight)
    option_ids = [opt.id for opt in decision.options]
    assert "opt-monitor" in option_ids
    assert "opt-predict" in option_ids


def test_adapt_generates_default_options(adapter):
    """Options: PATTERN pattern -> default option."""
    insight = _make_insight(pattern=InsightPattern.PATTERN)
    decision = adapter.adapt(insight)
    option_ids = [opt.id for opt in decision.options]
    assert "opt-default" in option_ids


def test_adapt_options_have_valid_scores(adapter):
    """Options: all option scores in [0.0, 1.0]."""
    for pattern in InsightPattern:
        insight = _make_insight(pattern=pattern)
        decision = adapter.adapt(insight)
        for opt in decision.options:
            assert 0.0 <= opt.score <= 1.0


def test_adapt_options_have_rationale(adapter):
    """Options: all options have non-empty rationale."""
    insight = _make_insight(pattern=InsightPattern.ANOMALY)
    decision = adapter.adapt(insight)
    for opt in decision.options:
        assert opt.rationale  # Non-empty


# ============================================================
# Confidence Derivation Tests
# ============================================================


def test_adapt_confidence_derived_from_insight(adapter):
    """Confidence: derived from insight.confidence * 0.9 (rule-based)."""
    insight = _make_insight(confidence=0.8)
    decision = adapter.adapt(insight)
    expected = round(0.8 * 0.9, 4)
    assert decision.confidence == expected


def test_adapt_confidence_in_valid_range(adapter):
    """Confidence: always in [0.0, 1.0]."""
    for conf in [0.0, 0.5, 0.9, 1.0]:
        insight = _make_insight(confidence=conf)
        decision = adapter.adapt(insight)
        assert 0.0 <= decision.confidence <= 1.0


# ============================================================
# Rationale + Constraints Tests
# ============================================================


def test_adapt_rationale_includes_source_info(adapter):
    """Rationale: includes source insight pattern/classification."""
    insight = _make_insight(
        insight_id="insight-meta",
        pattern=InsightPattern.ANOMALY,
        classification=InsightClassification.CRITICAL,
    )
    decision = adapter.adapt(insight)
    assert decision.rationale_metadata["source_insight_pattern"] == "anomaly"
    assert decision.rationale_metadata["source_insight_classification"] == "critical"
    assert decision.rationale_metadata["source_id"] == "insight-meta"


def test_adapt_rationale_marked_rule_based(adapter):
    """Rationale: explicitly marked as rule_based=True (NOT AI autonomous)."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert decision.rationale_metadata["rule_based"] is True


def test_adapt_constraints_no_autonomous_execution(adapter):
    """Constraints: includes no_autonomous_execution=True."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert decision.constraints_reference["no_autonomous_execution"] is True


def test_adapt_constraints_no_memory_write(adapter):
    """Constraints: includes no_memory_write=True."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert decision.constraints_reference["no_memory_write"] is True


def test_adapt_constraints_decision_layer_only(adapter):
    """Constraints: includes decision_layer_only=True."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert decision.constraints_reference["decision_layer_only"] is True


# ============================================================
# Schema Version Tests
# ============================================================


def test_adapt_output_uses_decision_schema_version(adapter):
    """Output: uses frozen 'decision.v0.1'."""
    insight = _make_insight()
    decision = adapter.adapt(insight)
    assert decision.schema_version == "decision.v0.1"


# ============================================================
# Pure Function + Stateless Tests
# ============================================================


def test_adapt_is_pure_function(adapter):
    """adapt() is pure: same insight -> same decision structure."""
    insight = _make_insight(insight_id="insight-pure")
    d1 = adapter.adapt(insight)
    d2 = adapter.adapt(insight)
    assert d1.id == d2.id
    assert d1.strategy == d2.strategy
    assert len(d1.options) == len(d2.options)
    assert d1.confidence == d2.confidence
    assert d1.insight_reference == d2.insight_reference


def test_adapter_is_stateless(adapter):
    """Adapter is stateless: multiple instances produce same output."""
    a1 = InsightDecisionAdapter()
    a2 = InsightDecisionAdapter()
    insight = _make_insight()
    d1 = a1.adapt(insight)
    d2 = a2.adapt(insight)
    assert d1 == d2


# ============================================================
# Boundary Compliance Tests
# ============================================================


def test_adapter_has_no_eventbus_reference(adapter):
    """Boundary: NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_storage_methods(adapter):
    """Boundary: NO storage methods."""
    forbidden_methods = ["save", "load", "cache", "persist", "flush", "sync"]
    for method in forbidden_methods:
        assert not hasattr(adapter, method), f"Adapter should not have {method!r}"


def test_adapter_has_no_execution_methods(adapter):
    """Boundary: NO execution methods (Decision != Execution)."""
    forbidden_methods = ["execute", "run", "trigger", "schedule", "dispatch"]
    for method in forbidden_methods:
        assert not hasattr(adapter, method), f"Adapter should not have {method!r}"


def test_adapter_has_no_llm_dependency(adapter):
    """Boundary: NO LLM/AI dependency."""
    forbidden_attrs = ["llm", "openai", "anthropic", "claude", "gpt", "language_model"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_memory_dependency(adapter):
    """Boundary: NO Memory dependency."""
    forbidden_attrs = ["memory", "vector_store", "embedding", "retrieval"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_capability_routing(adapter):
    """Boundary: NO Capability routing."""
    forbidden_attrs = ["route", "capability", "executor", "router"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_planner_dependency(adapter):
    """Boundary: NO Planner/Workflow dependency."""
    forbidden_attrs = ["plan", "planner", "workflow", "workflow_engine", "agent_planner"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_runtime_dependency(adapter):
    """Boundary: NO Runtime dependency."""
    forbidden_attrs = ["runtime", "session", "engine", "orchestrator"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_subscribe_method(adapter):
    """Boundary: Adapter has no subscribe() method."""
    assert not hasattr(adapter, "subscribe")
    assert not hasattr(adapter, "register")
    assert not hasattr(adapter, "publish")