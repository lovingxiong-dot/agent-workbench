"""tools/insight/adapter/observation_insight_adapter.py — Phase 3.14 Step 2: Insight Adapter.

Pure function: ObservationArtifact -> InsightArtifact.

Insight = 'What does it mean' (NOT AI summary, NOT decision).

Pattern detection: rule-based, deterministic, NO AI/ML/LLM.
Confidence: derived from ObservationScore (rule-based, NO LLM).

Rules (user spec):
- pure function
- stateless
- deterministic
- no storage
- no EventBus
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from tools.insight.contract import (
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)
from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationType,
)

if TYPE_CHECKING:
    pass  # No runtime dependency on v6.runtime or v6.presentation


# ============================================================
# Pattern Detection (Rule-based, Deterministic)
# ============================================================


def _detect_pattern(artifact: ObservationArtifact) -> InsightPattern:
    """Detect pattern from ObservationArtifact (rule-based).

    Pure function: deterministic from artifact fields.
    NO AI / ML / LLM.

    Detection order (priority):
    1. Failed event -> ANOMALY
    2. Low confidence -> THRESHOLD
    3. Has task_id -> CORRELATION (task link is most specific)
    4. Performance metrics -> TREND
    5. Default -> PATTERN
    """
    # Anomaly: failed events
    if artifact.observation_type == ObservationType.EVENT:
        content = artifact.content if isinstance(artifact.content, dict) else {}
        event_type = content.get("event_type", "")
        if "failed" in event_type or "error" in event_type:
            return InsightPattern.ANOMALY

    # Threshold: low-confidence or critical events
    if artifact.score.confidence < 0.4:
        return InsightPattern.THRESHOLD

    # Correlation: has task_id (linked observations)
    if artifact.task_id:
        return InsightPattern.CORRELATION

    # Trend: performance metrics (no task_id)
    if artifact.observation_type == ObservationType.PERFORMANCE:
        return InsightPattern.TREND

    # Default: pattern
    return InsightPattern.PATTERN


def _classify(artifact: ObservationArtifact, pattern: InsightPattern) -> InsightClassification:
    """Classify insight severity (rule-based, deterministic).

    NO AI / NO LLM.
    """
    # Critical: low confidence + anomaly pattern
    if artifact.score.confidence < 0.4:
        return InsightClassification.CRITICAL

    # Anomaly: anomaly pattern
    if pattern == InsightPattern.ANOMALY:
        return InsightClassification.ANOMALY

    # Trend: trend pattern
    if pattern == InsightPattern.TREND:
        return InsightClassification.TREND

    # Warning: medium confidence
    if artifact.score.confidence < 0.7:
        return InsightClassification.WARNING

    # Info: default
    return InsightClassification.INFO


def _derive_confidence(artifact: ObservationArtifact) -> float:
    """Derive insight confidence from ObservationScore (rule-based).

    NO AI / NO LLM.
    """
    # Use observation relevance as insight confidence (rule-based).
    return round(artifact.score.relevance * 0.5 + artifact.score.confidence * 0.5, 4)


def _build_explanation_metadata(artifact: ObservationArtifact, pattern: InsightPattern) -> dict:
    """Build display-ready metadata (NOT LLM narrative).

    Pure function: deterministic extraction.
    """
    metadata: dict = {
        "source_observation_type": artifact.observation_type.value,
        "source_schema_version": artifact.schema_version,
        "source_id": artifact.id,
        "detected_pattern": pattern.value,
        "rule_based": True,  # Explicitly mark as rule-based (NOT AI)
    }
    if artifact.task_id:
        metadata["source_task_id"] = artifact.task_id
    if isinstance(artifact.content, dict):
        event_type = artifact.content.get("event_type", "")
        if event_type:
            metadata["source_event_type"] = event_type
    return metadata


class ObservationInsightAdapter:
    """Pure function: ObservationArtifact -> InsightArtifact.

    关键约束 (user spec):
    - pure function (same input -> same output, no side effects)
    - stateless (no instance state)
    - deterministic (no random IDs in default flow)
    - no storage (no caching, no persistence)
    - no EventBus (read-only consumer of artifact)
    - rule-based pattern detection (NOT AI / ML / LLM)

    Strict NOT in scope:
    - AI / LLM / ML / natural language generation
    - Memory / Persistence
    - Decision / Recommendation / Action / Planning
    - Runtime event handling
    - UI / Renderer
    """

    def adapt(
        self,
        artifact: ObservationArtifact,
        id_prefix: str = "insight",
    ) -> InsightArtifact:
        """Convert an ObservationArtifact into a frozen InsightArtifact.

        Args:
            artifact: ObservationArtifact from Phase 3.12
            id_prefix: Prefix for insight id (default "insight")

        Returns:
            InsightArtifact: frozen structured understanding

        Note:
            Pure function: no side effects, no I/O, no state.
            Deterministic: same artifact -> same insight (id derived from artifact.id).
            Rule-based pattern detection (NOT AI / LLM).
        """
        pattern = _detect_pattern(artifact)
        classification = _classify(artifact, pattern)
        confidence = _derive_confidence(artifact)
        metadata = _build_explanation_metadata(artifact, pattern)

        return InsightArtifact(
            id=f"{id_prefix}-{artifact.id}",
            observation_reference=[artifact.id],
            pattern=pattern,
            classification=classification,
            confidence=confidence,
            explanation_metadata=metadata,
        )