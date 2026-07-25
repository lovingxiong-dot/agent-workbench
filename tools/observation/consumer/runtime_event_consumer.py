"""tools/observation/consumer/runtime_event_consumer.py — Phase 3.12 Batch 2 RuntimeEvent Consumer.

Read-only Adapter (NOT Runtime subscription).

边界 (ADR-016 + 用户 Check 2):
- ✅ consume(RuntimeEvent) → ObservationArtifact (pure function)
- ❌ runtime.submit() / dispatch() / task.update() (NO Runtime mutation)
- ❌ subscribe EventBus (NOT subscription)
- ❌ hold EventBus reference (NO state)

RuntimeEvent fields consumed:
- type: str (RuntimeEventType value, mapped to ObservationType)
- payload: dict (passed as content)
- task_id: str (passed as artifact.task_id)
- source: str (preserved in content.source)
- trace_id: str (passed as execution_id)
- phase: str (passed as content.phase)
- timestamp: float (preserved as created_at)
"""
from __future__ import annotations

import uuid

from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)

# Use TYPE_CHECKING to avoid runtime import of v6.runtime (Frozen Boundary)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v6.runtime.event_bus import RuntimeEvent


# ============================================================
# RuntimeEventType → ObservationType Mapping
# ============================================================

# Performance: latency / throughput / response time
_PERFORMANCE_EVENTS = frozenset({
    "task.started", "task.completed", "task.failed", "task.cancelled",
    "engine.started", "engine.completed", "engine.failed",
    "execution.started", "execution.progress", "execution.finished",
    "first.token", "chunk.received", "stream.finished",
})

# Resource: memory / cpu / connections / provider / model
_RESOURCE_EVENTS = frozenset({
    "provider.selected", "service.selected", "model.selected",
    "capability.resolved",
})

# Lifecycle: state transitions
_LIFECYCLE_EVENTS = frozenset({
    "request.sent",
    "service.started.legacy", "service.completed", "service.failed",
})

# Event: task events / errors / decisions / managers
_EVENT_EVENTS = frozenset({
    "tool.started", "tool.completed",
    "decision.planned",
    "manager.intent.classified", "manager.capability.selected",
    "manager.chain.step.started",
    "capability.chain.step.started",
})


class RuntimeEventConsumer:
    """Read-only Adapter: RuntimeEvent → ObservationArtifact.

    关键设计:
    - Pure function style (无 side effects, 无 Runtime state)
    - 不订阅 EventBus (NO subscription)
    - 不持有 EventBus 引用 (NO state)
    - 调用者负责传入 RuntimeEvent 对象
    - 输出 frozen ObservationArtifact

    职责 (用户 Check 2):
    ✅ consume(RuntimeEvent) → 提取 fields → create ObservationArtifact
    ❌ 禁止: runtime.submit() / dispatch() / task.update()
    """

    def consume(
        self,
        event: "RuntimeEvent",
        created_by: str = "runtime_event_consumer",
        id_prefix: str = "obs",
    ) -> ObservationArtifact:
        """Convert a RuntimeEvent into a frozen ObservationArtifact.

        Args:
            event: RuntimeEvent from v6/runtime/event_bus.py
            created_by: Provenance identifier (who produced this observation)
            id_prefix: Prefix for the auto-generated observation id

        Returns:
            ObservationArtifact: frozen dataclass with mapped ObservationType
        """
        observation_type = self._map_event_type(event.type)
        content = self._extract_content(event)
        score = self._default_score(observation_type)

        return ObservationArtifact(
            id=f"{id_prefix}-{uuid.uuid4().hex[:12]}",
            observation_type=observation_type,
            content=content,
            score=score,
            source=ObservationSource.RUNTIME,
            created_at=event.timestamp,
            created_by=created_by,
            execution_id=event.trace_id,
            task_id=event.task_id,
        )

    @staticmethod
    def _map_event_type(event_type: str) -> ObservationType:
        """Map RuntimeEvent.type to ObservationType (5 categories)."""
        if event_type in _PERFORMANCE_EVENTS:
            return ObservationType.PERFORMANCE
        if event_type in _RESOURCE_EVENTS:
            return ObservationType.RESOURCE
        if event_type in _LIFECYCLE_EVENTS:
            return ObservationType.LIFECYCLE
        if event_type in _EVENT_EVENTS:
            return ObservationType.EVENT
        # Default: unmapped events go to EVENT (catch-all)
        # HEALTH is reserved for system health checks (not RuntimeEvents)
        return ObservationType.EVENT

    @staticmethod
    def _extract_content(event: "RuntimeEvent") -> dict:
        """Extract content from RuntimeEvent.

        Includes type, payload, source, phase as content metadata.
        The frozen ObservationArtifact.content is a dict, not RuntimeEvent.
        """
        content: dict = {
            "event_type": event.type,
            "payload": dict(event.payload) if event.payload else {},
        }
        if event.source:
            content["source"] = event.source
        if event.phase:
            content["phase"] = event.phase
        return content

    @staticmethod
    def _default_score(observation_type: ObservationType) -> ObservationScore:
        """Default score for RuntimeEvent-derived observations.

        Relevance: 1.0 (always relevant — comes directly from Runtime)
        Confidence: 1.0 (RuntimeEvent is authoritative)
        Stability: 1.0 (Frozen Contract — v6.16.0-alpha Runtime)
        """
        return ObservationScore(
            relevance=1.0,
            confidence=1.0,
            stability=1.0,
        )
