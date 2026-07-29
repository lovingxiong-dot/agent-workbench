"""tools/decision_support/consumer/decision_support_consumer.py — Phase 3.15 Step 3: Decision Consumer.

Read-only consumption example.

Allowed (user spec):
- DecisionArtifact -> consumer output (to_dict / JSON serialization)

Forbidden (user spec):
- Consumer -> Execution (NOT ActionExecutor)
- Consumer -> Memory (NOT memory write)
- Consumer -> Runtime
- Consumer -> Insight Store
- Consumer -> EventBus
- LLM / AI autonomous decision
"""
from __future__ import annotations

import json
from typing import Any, Dict

from tools.decision_support.contract import (
    DECISION_ARTIFACT_SCHEMA_VERSION,
    DecisionArtifact,
)


class DecisionSupportConsumer:
    """Read-only consumer: DecisionArtifact -> consumer output.

    关键约束 (user spec):
    - consume valid model
    - reject invalid schema
    - no mutation
    - no EventBus
    - no Insight Store
    - no Runtime
    - NO Execution (Decision != ActionExecutor)
    - NO Memory write
    - NO LLM autonomous decision

    Strict NOT in scope (Phase 3.15):
    - LLM / AI autonomous decision
    - Memory / Persistence
    - Execution / Scheduling / Capability routing
    - Runtime event handling
    - UI / Renderer
    """

    def produce(self, decision: DecisionArtifact) -> Dict[str, Any]:
        """Produce consumer output (read-only) from decision.

        Args:
            decision: DecisionArtifact (frozen, from Adapter)

        Returns:
            Dict: decision output (JSON-serializable)

        Raises:
            ValueError: if schema_version is invalid
        """
        self._validate_schema(decision)
        return decision.to_dict()

    def produce_json(self, decision: DecisionArtifact) -> str:
        """Produce JSON-serialized consumer output.

        Args:
            decision: DecisionArtifact (frozen)

        Returns:
            str: JSON-serialized decision output
        """
        self._validate_schema(decision)
        return json.dumps(decision.to_dict())

    @staticmethod
    def _validate_schema(decision: DecisionArtifact) -> None:
        """Validate decision schema version (read-only check)."""
        if decision.schema_version != DECISION_ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"Invalid schema version: {decision.schema_version!r} "
                f"(expected {DECISION_ARTIFACT_SCHEMA_VERSION!r})"
            )