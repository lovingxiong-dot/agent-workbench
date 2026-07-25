"""tools/presentation/adapter/ — Phase 3.13 Step 2: Presentation Adapter.

Pure function: ObservationArtifact → ObservationViewModel.

Rules:
- pure function
- deterministic
- stateless
- no EventBus
- no storage
- no cache
"""
from tools.presentation.adapter.observation_presentation_adapter import (
    ObservationPresentationAdapter,
)

__all__ = ["ObservationPresentationAdapter"]
