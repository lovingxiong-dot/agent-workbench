"""tools/insight/consumer/insight_consumer.py — Phase 3.14 Step 3: Insight Consumer.

Read-only consumption example.

Allowed (user spec):
- InsightArtifact -> consumer output (to_dict / JSON serialization)

Forbidden (user spec):
- Insight -> Decision (Phase 3.15 separate)
- Insight -> Memory (Phase 3.16 separate)
- Consumer -> Runtime
- Consumer -> Observation Store
- Consumer -> EventBus
- LLM / AI Summary generation
"""
from __future__ import annotations

import json
from typing import Any, Dict

from tools.insight.contract import (
    INSIGHT_ARTIFACT_SCHEMA_VERSION,
    InsightArtifact,
)


class InsightConsumer:
    """Read-only consumer: InsightArtifact -> consumer output.

    关键约束 (user spec):
    - consume valid model
    - reject invalid schema
    - no mutation
    - no EventBus
    - no Observation Store
    - no Runtime
    - NO Decision (Insight != Decision)
    - NO Memory (Insight != Memory)

    Strict NOT in scope (Phase 3.14):
    - LLM / AI Summary
    - Memory / Persistence
    - Decision / Recommendation / Action / Planning
    - Runtime event handling
    - UI / Renderer
    """

    def produce(self, insight: InsightArtifact) -> Dict[str, Any]:
        """Produce consumer output (read-only) from insight.

        Args:
            insight: InsightArtifact (frozen, from Adapter)

        Returns:
            Dict: insight output (JSON-serializable)

        Raises:
            ValueError: if schema_version is invalid (consumer rejects invalid)
        """
        self._validate_schema(insight)
        return insight.to_dict()

    def produce_json(self, insight: InsightArtifact) -> str:
        """Produce JSON-serialized consumer output.

        Args:
            insight: InsightArtifact (frozen)

        Returns:
            str: JSON-serialized insight output
        """
        self._validate_schema(insight)
        return json.dumps(insight.to_dict())

    @staticmethod
    def _validate_schema(insight: InsightArtifact) -> None:
        """Validate insight schema version (read-only check)."""
        if insight.schema_version != INSIGHT_ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"Invalid schema version: {insight.schema_version!r} "
                f"(expected {INSIGHT_ARTIFACT_SCHEMA_VERSION!r})"
            )