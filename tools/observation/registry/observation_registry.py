"""tools/observation/registry/observation_registry.py — Phase 3.12 Batch 3 Minimal Observation Registry.

In-memory store for ObservationArtifact.

Scope: 3 methods only (minimal).
- register(artifact) → None
- query_by_id(artifact_id) → Optional[ObservationArtifact]
- query_by_execution_id(execution_id) → List[ObservationArtifact]

NOT in scope (Phase 3.16+ Memory features):
- Persistence
- Schema registry
- Governance
- Aggregation
- TTL / cleanup
"""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.observation.contract import ObservationArtifact


class ObservationRegistry:
    """Minimal in-memory ObservationArtifact store.

    关键设计:
    - in-memory only (NOT persistent)
    - 3 methods only (minimal API)
    - thread-unsafe by design (Phase 3.13+ 同步层处理)
    - no schema registry
    - no governance
    - no aggregation
    """

    def __init__(self) -> None:
        """Initialize empty in-memory store."""
        self._by_id: Dict[str, ObservationArtifact] = {}
        self._by_execution: Dict[str, List[str]] = {}

    def register(self, artifact: ObservationArtifact) -> None:
        """Register an ObservationArtifact (stores by id and execution_id).

        Args:
            artifact: ObservationArtifact to store

        Note:
            - If artifact.id already exists, it is overwritten (idempotent re-register)
            - execution_id index updated for query_by_execution_id
            - NO persistence, NO schema validation
        """
        self._by_id[artifact.id] = artifact

        execution_id = artifact.execution_id
        if execution_id:
            if execution_id not in self._by_execution:
                self._by_execution[execution_id] = []
            if artifact.id not in self._by_execution[execution_id]:
                self._by_execution[execution_id].append(artifact.id)

    def query_by_id(self, artifact_id: str) -> Optional[ObservationArtifact]:
        """Query ObservationArtifact by id.

        Args:
            artifact_id: ObservationArtifact.id

        Returns:
            ObservationArtifact if found, None otherwise
        """
        return self._by_id.get(artifact_id)

    def query_by_execution_id(self, execution_id: str) -> List[ObservationArtifact]:
        """Query all ObservationArtifacts for an execution_id.

        Args:
            execution_id: Execution identifier

        Returns:
            List of ObservationArtifacts (empty list if none)
            Order: insertion order (FIFO)
        """
        if not execution_id:
            return []
        artifact_ids = self._by_execution.get(execution_id, [])
        return [self._by_id[aid] for aid in artifact_ids if aid in self._by_id]
