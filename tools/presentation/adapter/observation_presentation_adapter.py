"""tools/presentation/adapter/observation_presentation_adapter.py — Phase 3.13 Step 2: Presentation Adapter.

Pure function: ObservationArtifact → ObservationViewModel.

Rules (user spec):
- pure function
- deterministic
- stateless
- no EventBus
- no storage
- no cache
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from tools.observation.contract import (
    ObservationArtifact,
    ObservationSource,
    ObservationType,
)
from tools.presentation.contract import (
    ObservationViewModel,
    PresentationCategory,
    PresentationSeverity,
    PresentationSource,
)

if TYPE_CHECKING:
    pass  # No runtime dependency on v6.runtime or v6.observation


# ============================================================
# Mapping Tables (Pure Data)
# ============================================================

_OBSERVATION_TYPE_TO_CATEGORY: dict = {
    ObservationType.PERFORMANCE: PresentationCategory.PERFORMANCE,
    ObservationType.RESOURCE: PresentationCategory.RESOURCE,
    ObservationType.LIFECYCLE: PresentationCategory.LIFECYCLE,
    ObservationType.EVENT: PresentationCategory.EVENT,
    ObservationType.HEALTH: PresentationCategory.HEALTH,
}

_OBSERVATION_SOURCE_TO_PRESENTATION: dict = {
    ObservationSource.HUMAN: PresentationSource.HUMAN,
    ObservationSource.AGENT: PresentationSource.AGENT,
    ObservationSource.RUNTIME: PresentationSource.RUNTIME,
    ObservationSource.SYSTEM: PresentationSource.SYSTEM,
}

# Severity inference from score (deterministic, rule-based, no AI)
# Thresholds defined inline in _derive_severity for clarity


class ObservationPresentationAdapter:
    """Pure function: ObservationArtifact → ObservationViewModel.

    关键约束 (user spec):
    - pure function (same input → same output, no side effects)
    - deterministic (no random IDs in default flow; id may be generated from artifact.id)
    - stateless (no instance state)
    - no EventBus (read-only consumer of artifact)
    - no storage (no caching, no persistence)
    - no cache

    Strict NOT in scope:
    - ❌ Renderer / Widget / Layout
    - ❌ Storage / Memory
    - ❌ AI / Insight / Summary generation
    - ❌ EventBus subscription
    """

    def adapt(
        self,
        artifact: ObservationArtifact,
        id_prefix: str = "vm",
    ) -> ObservationViewModel:
        """Convert an ObservationArtifact into a frozen ObservationViewModel.

        Args:
            artifact: ObservationArtifact from Phase 3.12
            id_prefix: Prefix for view model id (default "vm")

        Returns:
            ObservationViewModel: frozen display-ready contract

        Note:
            Pure function: no side effects, no I/O, no state.
            Deterministic: same artifact → same view model (id derived from artifact.id).
        """
        return ObservationViewModel(
            id=f"{id_prefix}-{artifact.id}",
            title=self._derive_title(artifact),
            summary=self._derive_summary(artifact),
            category=self._map_category(artifact.observation_type),
            severity=self._derive_severity(artifact),
            source=self._map_source(artifact.source),
            timestamp=artifact.created_at,
            metrics=self._extract_metrics(artifact),
            metadata=self._extract_metadata(artifact),
        )

    @staticmethod
    def _derive_title(artifact: ObservationArtifact) -> str:
        """Derive display-ready title from artifact.

        Pure function: deterministic from artifact fields.
        """
        category_label = artifact.observation_type.value.capitalize()
        if artifact.task_id:
            return f"{category_label} · {artifact.task_id}"
        return f"{category_label} Observation"

    @staticmethod
    def _derive_summary(artifact: ObservationArtifact) -> str:
        """Derive display-ready summary from artifact content.

        Pure function: deterministic extraction.
        """
        if isinstance(artifact.content, dict):
            event_type = artifact.content.get("event_type", "")
            if event_type:
                return f"Event: {event_type}"
        return f"Source={artifact.source.value} Score={artifact.score.confidence:.2f}"

    @staticmethod
    def _map_category(observation_type: ObservationType) -> PresentationCategory:
        """Map ObservationType → PresentationCategory (1:1)."""
        return _OBSERVATION_TYPE_TO_CATEGORY[observation_type]

    @staticmethod
    def _map_source(source: ObservationSource) -> PresentationSource:
        """Map ObservationSource → PresentationSource (1:1)."""
        return _OBSERVATION_SOURCE_TO_PRESENTATION[source]

    @staticmethod
    def _derive_severity(artifact: ObservationArtifact) -> PresentationSeverity:
        """Derive severity from confidence score (rule-based, no AI).

        Thresholds (ascending confidence → descending severity):
        - confidence < 0.4 → CRITICAL (unreliable)
        - 0.4 <= confidence < 0.7 → ERROR
        - 0.7 <= confidence < 1.0 → WARNING
        - confidence == 1.0 → INFO (fully reliable)

        Implementation: if-else chain (clearer than loop).
        """
        confidence = artifact.score.confidence
        if confidence < 0.4:
            return PresentationSeverity.CRITICAL
        if confidence < 0.7:
            return PresentationSeverity.ERROR
        if confidence < 1.0:
            return PresentationSeverity.WARNING
        return PresentationSeverity.INFO

    @staticmethod
    def _extract_metrics(artifact: ObservationArtifact) -> dict:
        """Extract display-ready metrics from artifact content.

        Pure function: deterministic extraction (no I/O, no transformation).
        """
        if isinstance(artifact.content, dict):
            payload = artifact.content.get("payload")
            if isinstance(payload, dict):
                return dict(payload)
        return {}

    @staticmethod
    def _extract_metadata(artifact: ObservationArtifact) -> dict:
        """Extract source metadata from artifact (preserved as-is).

        Pure function: deterministic passthrough.
        """
        metadata: dict = {
            "source_schema_version": artifact.schema_version,
            "source_id": artifact.id,
            "source_type": artifact.observation_type.value,
        }
        if isinstance(artifact.content, dict):
            # Pass through non-payload fields as metadata
            for key, value in artifact.content.items():
                if key != "payload":
                    metadata[key] = value
        return metadata
