"""tools/presentation/contract/ — Phase 3.13 Presentation Contract Schema (Frozen).

Phase 3.13 Step 1: ObservationViewModel Frozen Contract.

边界 (ADR-017):
- platform-agnostic (NOT UI Model)
- No runtime dependency
- No UI dependency
- No event bus
- No storage

Strict NOT in scope:
- ❌ Renderer / Widget / Layout / Panel / Theme / Style
- ❌ Storage / Persistence / Memory / Embedding
- ❌ Insight / AI Summary
- ❌ EventBus new channel
"""
from tools.presentation.contract.observation_view_model import (
    OBSERVATION_VIEW_MODEL_SCHEMA_VERSION,
    ObservationViewModel,
    PresentationCategory,
    PresentationSeverity,
    PresentationSource,
)

__all__ = [
    "OBSERVATION_VIEW_MODEL_SCHEMA_VERSION",
    "ObservationViewModel",
    "PresentationCategory",
    "PresentationSeverity",
    "PresentationSource",
]
