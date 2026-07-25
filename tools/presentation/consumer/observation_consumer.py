"""tools/presentation/consumer/observation_consumer.py — Phase 3.13 Step 3: Presentation Consumer.

Read-only consumption example.

Allowed (user spec):
- ObservationViewModel → presentation output (to_dict / JSON serialization)

Forbidden (user spec):
- Consumer → Runtime
- Consumer → Observation Store
- Consumer → EventBus

Scope (minimal):
- Single output method: produce() returns dict
- Schema validation: reject invalid view model
- No state, no subscription, no mutation
"""
from __future__ import annotations

import json
from typing import Any, Dict

from tools.presentation.contract import (
    OBSERVATION_VIEW_MODEL_SCHEMA_VERSION,
    ObservationViewModel,
)


class ObservationConsumer:
    """Read-only consumer: ObservationViewModel → presentation output.

    关键约束 (user spec):
    - consume valid model
    - reject invalid schema
    - no mutation
    - no EventBus
    - no Observation Store
    - no Runtime

    Strict NOT in scope (Phase 3.13):
    - ❌ EventBus subscription
    - ❌ Runtime event handling
    - ❌ Observation Store (Registry) access
    - ❌ Storage / Persistence
    - ❌ AI / Insight / Summary generation
    - ❌ UI / Renderer / Widget
    """

    def produce(self, view_model: ObservationViewModel) -> Dict[str, Any]:
        """Produce presentation output (read-only) from view model.

        Args:
            view_model: ObservationViewModel (frozen, from Adapter)

        Returns:
            Dict: presentation-ready payload (JSON-serializable)

        Raises:
            ValueError: if schema_version is invalid (consumer rejects invalid)

        Note:
            Pure function: same view_model → same output.
            No side effects, no I/O, no state.
        """
        self._validate_schema(view_model)
        return view_model.to_dict()

    def produce_json(self, view_model: ObservationViewModel) -> str:
        """Produce JSON-serialized presentation output.

        Args:
            view_model: ObservationViewModel (frozen)

        Returns:
            str: JSON-serialized presentation payload

        Raises:
            ValueError: if schema_version is invalid
        """
        self._validate_schema(view_model)
        return json.dumps(view_model.to_dict())

    @staticmethod
    def _validate_schema(view_model: ObservationViewModel) -> None:
        """Validate view model schema version (read-only check).

        Rejects invalid schema (consumer safety).
        """
        if view_model.schema_version != OBSERVATION_VIEW_MODEL_SCHEMA_VERSION:
            raise ValueError(
                f"Invalid schema version: {view_model.schema_version!r} "
                f"(expected {OBSERVATION_VIEW_MODEL_SCHEMA_VERSION!r})"
            )
