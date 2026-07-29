"""tools/decision_support/adapter/insight_decision_adapter.py — Phase 3.15 Step 2: Decision Adapter.

Pure function: InsightArtifact -> DecisionArtifact.

Decision = 'What should we consider' (NOT 'what to do now').

Strategy selection: rule-based, deterministic, NO AI autonomous.
Option generation: rule-based, NO LLM decision-making.

Rules (user spec):
- pure function
- stateless
- deterministic
- no storage
- no EventBus
- no execution
- no scheduling
- no capability routing
- no task mutation
- no memory write
- no LLM autonomous decision
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from tools.decision_support.contract import (
    DecisionArtifact,
    DecisionOption,
    DecisionStrategy,
)
from tools.insight.contract import (
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)

if TYPE_CHECKING:
    pass  # No runtime dependency on v6.runtime or v6.insight


# ============================================================
# Strategy Selection (Rule-based, NOT AI autonomous)
# ============================================================


def _select_strategy(insight: InsightArtifact) -> DecisionStrategy:
    """Select decision strategy from insight (rule-based).

    Pure function: deterministic from insight fields.
    NO AI / NO LLM autonomous decision.
    """
    # Critical / Anomaly classification -> Conservative (risk-averse)
    if insight.classification in (
        InsightClassification.CRITICAL,
        InsightClassification.ANOMALY,
    ):
        return DecisionStrategy.CONSERVATIVE

    # Warning -> Defensive (protect resources)
    if insight.classification == InsightClassification.WARNING:
        return DecisionStrategy.DEFENSIVE

    # Trend -> Balanced
    if insight.classification == InsightClassification.TREND:
        return DecisionStrategy.BALANCED

    # Info -> Neutral (no urgent action)
    return DecisionStrategy.NEUTRAL


# ============================================================
# Option Generation (Rule-based, NO LLM)
# ============================================================


def _generate_options(insight: InsightArtifact) -> List[DecisionOption]:
    """Generate decision options from insight (rule-based).

    Pure function: deterministic from insight pattern/classification.
    NO LLM / NO AI autonomous generation.
    """
    options: List[DecisionOption] = []

    if insight.pattern == InsightPattern.ANOMALY:
        # Anomaly: investigate / mitigate / accept risk
        options.append(DecisionOption(
            id="opt-investigate",
            label="Investigate root cause",
            score=0.9,
            rationale="Anomaly detected, root cause investigation prioritized",
        ))
        options.append(DecisionOption(
            id="opt-mitigate",
            label="Apply mitigation",
            score=0.7,
            rationale="Apply known mitigation patterns",
        ))
        options.append(DecisionOption(
            id="opt-accept",
            label="Accept and monitor",
            score=0.3,
            rationale="Continue monitoring, no immediate action",
        ))

    elif insight.pattern == InsightPattern.THRESHOLD:
        # Threshold: review limits / adjust / escalate
        options.append(DecisionOption(
            id="opt-review",
            label="Review threshold limits",
            score=0.8,
            rationale="Threshold exceeded, review configuration",
        ))
        options.append(DecisionOption(
            id="opt-adjust",
            label="Adjust threshold",
            score=0.6,
            rationale="Adjust based on observed patterns",
        ))
        options.append(DecisionOption(
            id="opt-escalate",
            label="Escalate to operator",
            score=0.5,
            rationale="Escalate for human decision",
        ))

    elif insight.pattern == InsightPattern.CORRELATION:
        # Correlation: link analysis / verify / log
        options.append(DecisionOption(
            id="opt-link",
            label="Link related observations",
            score=0.8,
            rationale="Track correlated observations",
        ))
        options.append(DecisionOption(
            id="opt-verify",
            label="Verify correlation",
            score=0.7,
            rationale="Verify correlation validity",
        ))

    elif insight.pattern == InsightPattern.TREND:
        # Trend: monitor / predict / plan
        options.append(DecisionOption(
            id="opt-monitor",
            label="Continue monitoring",
            score=0.8,
            rationale="Track trend evolution",
        ))
        options.append(DecisionOption(
            id="opt-predict",
            label="Project forward",
            score=0.6,
            rationale="Predict future state",
        ))

    else:
        # Default (PATTERN)
        options.append(DecisionOption(
            id="opt-default",
            label="Continue current path",
            score=0.5,
            rationale="No specific action recommended",
        ))

    return options


def _derive_confidence(insight: InsightArtifact) -> float:
    """Derive decision confidence from insight confidence (rule-based)."""
    return round(insight.confidence * 0.9, 4)  # Slightly more conservative


def _build_rationale_metadata(insight: InsightArtifact, strategy: DecisionStrategy) -> dict:
    """Build rationale metadata (NOT LLM narrative)."""
    metadata: dict = {
        "source_insight_pattern": insight.pattern.value,
        "source_insight_classification": insight.classification.value,
        "source_schema_version": insight.schema_version,
        "source_id": insight.id,
        "selected_strategy": strategy.value,
        "rule_based": True,  # Explicitly NOT AI autonomous
    }
    return metadata


def _build_constraints_reference(insight: InsightArtifact) -> dict:
    """Build constraints reference (NOT execution constraints).

    Pure function: deterministic extraction.
    """
    constraints: dict = {
        "no_autonomous_execution": True,  # Explicit constraint
        "no_memory_write": True,
        "decision_layer_only": True,
    }
    return constraints


class InsightDecisionAdapter:
    """Pure function: InsightArtifact -> DecisionArtifact.

    关键约束 (user spec):
    - pure function (same input -> same output, no side effects)
    - stateless (no instance state)
    - deterministic (no random IDs)
    - no storage (no caching, no persistence)
    - no EventBus (read-only consumer of insight)
    - rule-based strategy selection (NOT AI autonomous)
    - rule-based option generation (NOT LLM)

    Strict NOT in scope (Phase 3.15):
    - execute / schedule / capability routing
    - task mutation / memory write
    - LLM autonomous decision
    - ActionExecutor / AgentPlanner / WorkflowEngine
    - Runtime event handling
    - UI / Renderer
    """

    def adapt(
        self,
        insight: InsightArtifact,
        id_prefix: str = "decision",
    ) -> DecisionArtifact:
        """Convert an InsightArtifact into a frozen DecisionArtifact.

        Args:
            insight: InsightArtifact from Phase 3.14
            id_prefix: Prefix for decision id (default "decision")

        Returns:
            DecisionArtifact: frozen decision options contract

        Note:
            Pure function: no side effects, no I/O, no state.
            Deterministic: same insight -> same decision.
            Rule-based strategy + option generation (NOT AI / LLM autonomous).
        """
        strategy = _select_strategy(insight)
        options = _generate_options(insight)
        confidence = _derive_confidence(insight)
        rationale = _build_rationale_metadata(insight, strategy)
        constraints = _build_constraints_reference(insight)

        return DecisionArtifact(
            id=f"{id_prefix}-{insight.id}",
            insight_reference=list(insight.observation_reference),
            options=options,
            strategy=strategy,
            confidence=confidence,
            rationale_metadata=rationale,
            constraints_reference=constraints,
        )