"""tests/observation/consumer/test_runtime_event_consumer.py — Phase 3.12 Batch 2 RuntimeEvent Consumer Tests.

Tests (60% Primitive):
- Pure function: RuntimeEvent → ObservationArtifact
- 5 ObservationType mapping (Performance / Resource / Lifecycle / Event / Health)
- Default score (1.0, 1.0, 1.0)
- Content extraction (payload / source / phase)
- Provenance (created_by + source = RUNTIME)
- Frozen output
- No EventBus subscription / state
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time

import pytest

from tools.observation.consumer import RuntimeEventConsumer
from tools.observation.contract import (
    ObservationArtifact,
    ObservationSource,
    ObservationType,
)


# ============================================================
# Test Fixtures: Mock RuntimeEvent (avoid import v6.runtime)
# ============================================================


@dataclass
class MockRuntimeEvent:
    """Mock RuntimeEvent for testing Consumer (avoids runtime import)."""

    type: str
    payload: dict
    task_id: str
    source: str = ""
    trace_id: str = ""
    phase: str = ""
    timestamp: float = field(default_factory=time.time)


@pytest.fixture
def consumer() -> RuntimeEventConsumer:
    """Standard consumer instance."""
    return RuntimeEventConsumer()


# ============================================================
# Basic Functionality Tests
# ============================================================


def test_consume_returns_observation_artifact(consumer):
    """Contract: consume() returns ObservationArtifact."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={"task": "test"},
        task_id="task-1",
    )
    result = consumer.consume(event)
    assert isinstance(result, ObservationArtifact)


def test_consume_output_is_frozen(consumer):
    """Contract: consume() output is frozen dataclass."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={},
        task_id="task-1",
    )
    result = consumer.consume(event)
    with pytest.raises((AttributeError, Exception)):
        result.id = "modified"  # type: ignore


# ============================================================
# 5 ObservationType Mapping Tests
# ============================================================


def test_consume_maps_performance_event(consumer):
    """Mapping: TASK_STARTED → PERFORMANCE."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.observation_type == ObservationType.PERFORMANCE


def test_consume_maps_engine_event_to_performance(consumer):
    """Mapping: ENGINE_* → PERFORMANCE."""
    for event_type in ["engine.started", "engine.completed", "engine.failed"]:
        event = MockRuntimeEvent(type=event_type, payload={}, task_id="t1")
        result = consumer.consume(event)
        assert result.observation_type == ObservationType.PERFORMANCE


def test_consume_maps_stream_event_to_performance(consumer):
    """Mapping: STREAM events (FIRST_TOKEN, CHUNK_RECEIVED) → PERFORMANCE."""
    for event_type in ["first.token", "chunk.received", "stream.finished"]:
        event = MockRuntimeEvent(type=event_type, payload={}, task_id="t1")
        result = consumer.consume(event)
        assert result.observation_type == ObservationType.PERFORMANCE


def test_consume_maps_provider_event_to_resource(consumer):
    """Mapping: PROVIDER_*, MODEL_*, SERVICE_*, CAPABILITY_RESOLVED → RESOURCE."""
    for event_type in ["provider.selected", "model.selected", "service.selected", "capability.resolved"]:
        event = MockRuntimeEvent(type=event_type, payload={}, task_id="t1")
        result = consumer.consume(event)
        assert result.observation_type == ObservationType.RESOURCE


def test_consume_maps_lifecycle_event(consumer):
    """Mapping: REQUEST_SENT, SERVICE_* (legacy) → LIFECYCLE."""
    for event_type in ["request.sent", "service.started.legacy", "service.completed", "service.failed"]:
        event = MockRuntimeEvent(type=event_type, payload={}, task_id="t1")
        result = consumer.consume(event)
        assert result.observation_type == ObservationType.LIFECYCLE


def test_consume_maps_tool_event_to_event(consumer):
    """Mapping: TOOL_*, DECISION_*, MANAGER_*, CAPABILITY_CHAIN → EVENT."""
    for event_type in [
        "tool.started", "tool.completed",
        "decision.planned",
        "manager.intent.classified", "manager.capability.selected",
        "manager.chain.step.started",
        "capability.chain.step.started",
    ]:
        event = MockRuntimeEvent(type=event_type, payload={}, task_id="t1")
        result = consumer.consume(event)
        assert result.observation_type == ObservationType.EVENT


def test_consume_unmapped_event_falls_back_to_event(consumer):
    """Mapping: unmapped event type → EVENT (catch-all default)."""
    event = MockRuntimeEvent(type="custom.unknown.event", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.observation_type == ObservationType.EVENT


# ============================================================
# Provenance Tests
# ============================================================


def test_consume_source_is_runtime(consumer):
    """Provenance: source = RUNTIME (auto-set by Consumer)."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.source == ObservationSource.RUNTIME


def test_consume_uses_default_created_by(consumer):
    """Provenance: default created_by = 'runtime_event_consumer'."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.created_by == "runtime_event_consumer"


def test_consume_accepts_custom_created_by(consumer):
    """Provenance: custom created_by overrides default."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event, created_by="my_custom_adapter")
    assert result.created_by == "my_custom_adapter"


# ============================================================
# Default Score Tests
# ============================================================


def test_consume_default_score_is_1_0(consumer):
    """Score: relevance/confidence/stability = 1.0 (Frozen Runtime)."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.score.relevance == 1.0
    assert result.score.confidence == 1.0
    assert result.score.stability == 1.0


# ============================================================
# Content Extraction Tests
# ============================================================


def test_consume_extracts_payload_into_content(consumer):
    """Content: event.payload preserved as content.payload."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={"model": "gpt-4", "tokens": 100},
        task_id="t1",
    )
    result = consumer.consume(event)
    assert result.content["payload"] == {"model": "gpt-4", "tokens": 100}


def test_consume_extracts_event_type_into_content(consumer):
    """Content: event.type preserved as content.event_type."""
    event = MockRuntimeEvent(type="engine.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.content["event_type"] == "engine.started"


def test_consume_extracts_source_when_provided(consumer):
    """Content: event.source → content.source (if non-empty)."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={},
        task_id="t1",
        source="engine:llm",
    )
    result = consumer.consume(event)
    assert result.content["source"] == "engine:llm"


def test_consume_omits_empty_source(consumer):
    """Content: empty source NOT included in content."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1", source="")
    result = consumer.consume(event)
    assert "source" not in result.content


def test_consume_extracts_phase_when_provided(consumer):
    """Content: event.phase → content.phase (if non-empty)."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={},
        task_id="t1",
        phase="inference",
    )
    result = consumer.consume(event)
    assert result.content["phase"] == "inference"


def test_consume_omits_empty_phase(consumer):
    """Content: empty phase NOT included in content."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1", phase="")
    result = consumer.consume(event)
    assert "phase" not in result.content


def test_consume_handles_empty_payload(consumer):
    """Content: empty payload → content.payload = {} (not None)."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.content["payload"] == {}


# ============================================================
# Metadata Forwarding Tests
# ============================================================


def test_consume_forwards_task_id(consumer):
    """Metadata: event.task_id → artifact.task_id."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="task-abc-123")
    result = consumer.consume(event)
    assert result.task_id == "task-abc-123"


def test_consume_forwards_trace_id_to_execution_id(consumer):
    """Metadata: event.trace_id → artifact.execution_id."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={},
        task_id="t1",
        trace_id="trace-xyz-789",
    )
    result = consumer.consume(event)
    assert result.execution_id == "trace-xyz-789"


def test_consume_preserves_timestamp(consumer):
    """Metadata: event.timestamp → artifact.created_at."""
    fixed_ts = 1700000000.0
    event = MockRuntimeEvent(
        type="task.started",
        payload={},
        task_id="t1",
        timestamp=fixed_ts,
    )
    result = consumer.consume(event)
    assert result.created_at == fixed_ts


# ============================================================
# ID Generation Tests
# ============================================================


def test_consume_generates_unique_id(consumer):
    """ID: each consume() generates unique id."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    r1 = consumer.consume(event)
    r2 = consumer.consume(event)
    assert r1.id != r2.id


def test_consume_id_starts_with_obs_prefix(consumer):
    """ID: default id starts with 'obs-'."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.id.startswith("obs-")


def test_consume_id_accepts_custom_prefix(consumer):
    """ID: custom id_prefix overrides default."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event, id_prefix="myapp")
    assert result.id.startswith("myapp-")


# ============================================================
# Schema Version Tests
# ============================================================


def test_consume_output_uses_frozen_schema_version(consumer):
    """Schema: output uses frozen 'observation.v0.1'."""
    event = MockRuntimeEvent(type="task.started", payload={}, task_id="t1")
    result = consumer.consume(event)
    assert result.schema_version == "observation.v0.1"


# ============================================================
# Boundary Compliance Tests
# ============================================================


def test_consumer_does_not_hold_eventbus_reference(consumer):
    """Boundary: Consumer has NO EventBus reference (read-only Adapter)."""
    # Check that consumer has no eventbus/subscribe/publish attributes
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r} attribute"


def test_consumer_has_no_subscribe_method(consumer):
    """Boundary: Consumer has no subscribe() method (NO subscription)."""
    assert not hasattr(consumer, "subscribe")
    assert not hasattr(consumer, "register")
    assert not hasattr(consumer, "publish")


def test_consumer_has_no_runtime_mutation_methods(consumer):
    """Boundary: Consumer has no runtime mutation methods (NO submit/dispatch/update)."""
    forbidden_methods = ["submit", "dispatch", "update", "mutate", "write", "modify"]
    for method in forbidden_methods:
        assert not hasattr(consumer, method), f"Consumer should not have {method!r} method"


def test_consume_is_pure_function(consumer):
    """Boundary: consume() is pure (same input → same output structure, only id/timestamp differ)."""
    event = MockRuntimeEvent(
        type="task.started",
        payload={"key": "value"},
        task_id="task-1",
        trace_id="trace-1",
        source="engine:llm",
        phase="inference",
        timestamp=1700000000.0,
    )
    r1 = consumer.consume(event, created_by="adapter-A", id_prefix="obs")
    r2 = consumer.consume(event, created_by="adapter-A", id_prefix="obs")
    # Same content/structure (only id differs because of uuid)
    assert r1.content == r2.content
    assert r1.observation_type == r2.observation_type
    assert r1.task_id == r2.task_id
    assert r1.execution_id == r2.execution_id
    assert r1.score == r2.score
    # IDs differ (uuid generation)
    assert r1.id != r2.id
