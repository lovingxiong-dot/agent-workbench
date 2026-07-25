"""tools/observation/registry/ — Phase 3.12 Batch 3 Minimal Observation Registry.

In-memory store (NOT Memory, NOT persistence).

Principle: Observation records what happened. Memory remembers what matters.
两者不要提前合并。

Scope (minimal):
- Storage: in-memory dict (NOT persistence, NOT database)
- API: 3 methods only
  - register(artifact) → None
  - query_by_id(artifact_id) → Optional[ObservationArtifact]
  - query_by_execution_id(execution_id) → List[ObservationArtifact]

Explicitly NOT in scope (Phase 3.16+ Memory):
- ❌ Persistence (file/DB/vector store)
- ❌ Schema registry / versioning
- ❌ Governance layer
- ❌ Aggregation / analytics
- ❌ Multi-tenant
- ❌ Cross-process / cross-machine
- ❌ Auto-cleanup / TTL
"""
from tools.observation.registry.observation_registry import ObservationRegistry

__all__ = ["ObservationRegistry"]
