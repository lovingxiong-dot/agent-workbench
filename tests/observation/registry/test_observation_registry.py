"""tests/observation/registry/test_observation_registry.py — Phase 3.12 Batch 3 Minimal Observation Registry Tests.

Tests (60% Primitive):
- Empty registry: query_by_id returns None, query_by_execution_id returns []
- register + query_by_id round-trip
- register + query_by_execution_id round-trip
- Multiple artifacts per execution_id
- Multiple execution_ids
- Empty execution_id (skipped from index)
- Re-register (idempotent overwrite)
- 3 methods only (no extra API surface)
"""
from __future__ import annotations

import pytest

from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)
from tools.observation.registry import ObservationRegistry


def _make_artifact(
    artifact_id: str = "obs-001",
    execution_id: str = "exec-1",
    task_id: str = "task-1",
    observation_type: ObservationType = ObservationType.PERFORMANCE,
) -> ObservationArtifact:
    """Helper: create test artifact."""
    return ObservationArtifact(
        id=artifact_id,
        observation_type=observation_type,
        content={"test": True},
        score=ObservationScore(relevance=1.0, confidence=1.0, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        execution_id=execution_id,
        task_id=task_id,
    )


@pytest.fixture
def registry() -> ObservationRegistry:
    """Standard registry instance."""
    return ObservationRegistry()


# ============================================================
# Empty Registry Tests
# ============================================================


def test_empty_registry_query_by_id_returns_none(registry):
    """Empty registry: query_by_id returns None."""
    assert registry.query_by_id("nonexistent") is None


def test_empty_registry_query_by_execution_id_returns_empty_list(registry):
    """Empty registry: query_by_execution_id returns []."""
    assert registry.query_by_execution_id("exec-1") == []


# ============================================================
# register + query_by_id Round-trip Tests
# ============================================================


def test_register_then_query_by_id_returns_artifact(registry):
    """register + query_by_id: round-trip."""
    artifact = _make_artifact(artifact_id="obs-001")
    registry.register(artifact)
    result = registry.query_by_id("obs-001")
    assert result is not None
    assert result.id == "obs-001"
    assert result.execution_id == "exec-1"


def test_query_by_id_after_register_preserves_all_fields(registry):
    """register + query_by_id: all fields preserved."""
    artifact = _make_artifact(artifact_id="obs-002")
    registry.register(artifact)
    result = registry.query_by_id("obs-002")
    assert result is not None
    assert result.observation_type == ObservationType.PERFORMANCE
    assert result.content == {"test": True}
    assert result.source == ObservationSource.RUNTIME
    assert result.task_id == "task-1"
    assert result.created_by == "test"


def test_query_by_id_returns_frozen_artifact(registry):
    """query_by_id returns frozen artifact (immutable)."""
    artifact = _make_artifact()
    registry.register(artifact)
    result = registry.query_by_id("obs-001")
    assert result is not None
    with pytest.raises((AttributeError, Exception)):
        result.id = "modified"  # type: ignore


# ============================================================
# register + query_by_execution_id Round-trip Tests
# ============================================================


def test_register_then_query_by_execution_id_returns_list(registry):
    """register + query_by_execution_id: round-trip."""
    artifact = _make_artifact(artifact_id="obs-010", execution_id="exec-A")
    registry.register(artifact)
    result = registry.query_by_execution_id("exec-A")
    assert len(result) == 1
    assert result[0].id == "obs-010"


def test_query_by_execution_id_empty_string_returns_empty_list(registry):
    """query_by_execution_id("") returns [] (no artifacts for empty execution_id)."""
    artifact = _make_artifact(execution_id="")
    registry.register(artifact)  # empty execution_id not indexed
    assert registry.query_by_execution_id("") == []


def test_query_by_execution_id_multiple_artifacts(registry):
    """Multiple artifacts per execution_id: returned in insertion order (FIFO)."""
    a1 = _make_artifact(artifact_id="obs-100", execution_id="exec-multi")
    a2 = _make_artifact(artifact_id="obs-101", execution_id="exec-multi")
    a3 = _make_artifact(artifact_id="obs-102", execution_id="exec-multi")
    registry.register(a1)
    registry.register(a2)
    registry.register(a3)
    result = registry.query_by_execution_id("exec-multi")
    assert len(result) == 3
    assert [r.id for r in result] == ["obs-100", "obs-101", "obs-102"]


def test_query_by_execution_id_filters_correctly(registry):
    """Multiple execution_ids: query filters by execution_id."""
    a1 = _make_artifact(artifact_id="obs-A", execution_id="exec-1")
    a2 = _make_artifact(artifact_id="obs-B", execution_id="exec-2")
    a3 = _make_artifact(artifact_id="obs-C", execution_id="exec-1")
    registry.register(a1)
    registry.register(a2)
    registry.register(a3)
    result_1 = registry.query_by_execution_id("exec-1")
    result_2 = registry.query_by_execution_id("exec-2")
    assert len(result_1) == 2
    assert {r.id for r in result_1} == {"obs-A", "obs-C"}
    assert len(result_2) == 1
    assert result_2[0].id == "obs-B"


def test_query_by_execution_id_returns_empty_for_nonexistent(registry):
    """query_by_execution_id for unknown execution_id returns []."""
    assert registry.query_by_execution_id("nonexistent") == []


# ============================================================
# Re-register Tests (Idempotent)
# ============================================================


def test_register_overwrites_existing_id(registry):
    """register with same id: overwrites (idempotent re-register)."""
    a1 = _make_artifact(artifact_id="obs-dup", )
    a1 = ObservationArtifact(
        id="obs-dup",
        observation_type=ObservationType.PERFORMANCE,
        content={"version": 1},
        score=ObservationScore(relevance=1.0, confidence=1.0, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        execution_id="exec-1",
        task_id="task-1",
    )
    a2 = ObservationArtifact(
        id="obs-dup",
        observation_type=ObservationType.PERFORMANCE,
        content={"version": 2},
        score=ObservationScore(relevance=1.0, confidence=1.0, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        execution_id="exec-1",
        task_id="task-1",
    )
    registry.register(a1)
    registry.register(a2)
    result = registry.query_by_id("obs-dup")
    assert result is not None
    assert result.content == {"version": 2}


def test_register_does_not_duplicate_in_execution_index(registry):
    """register with same id+execution_id: not duplicated in execution index."""
    artifact = _make_artifact(artifact_id="obs-dup", execution_id="exec-1")
    registry.register(artifact)
    registry.register(artifact)
    result = registry.query_by_execution_id("exec-1")
    assert len(result) == 1
    assert result[0].id == "obs-dup"


# ============================================================
# Empty execution_id Behavior
# ============================================================


def test_register_artifact_with_empty_execution_id_skips_index(registry):
    """register with execution_id="": NOT indexed in execution_id index."""
    artifact = _make_artifact(artifact_id="obs-noexec", execution_id="")
    registry.register(artifact)
    # query_by_id works
    assert registry.query_by_id("obs-noexec") is not None
    # query_by_execution_id("") returns empty (not indexed)
    assert registry.query_by_execution_id("") == []


# ============================================================
# 3-Method API Surface (Minimal Contract)
# ============================================================


def test_registry_has_exactly_3_public_methods(registry):
    """API Contract: Registry has exactly 3 public methods (minimal)."""
    public_methods = [m for m in dir(registry) if not m.startswith("_") and callable(getattr(registry, m))]
    # Filter out dunder methods
    user_methods = [m for m in public_methods if not m.startswith("__")]
    assert set(user_methods) == {"register", "query_by_id", "query_by_execution_id"}


def test_registry_does_not_have_persistence_methods(registry):
    """API Contract: NO persistence methods (in-memory only)."""
    forbidden = ["save", "load", "persist", "flush", "sync", "backup"]
    for method in forbidden:
        assert not hasattr(registry, method), f"Registry should not have {method!r}"


def test_registry_does_not_have_governance_methods(registry):
    """API Contract: NO governance methods."""
    forbidden = ["validate", "audit", "policy", "permission", "access_control"]
    for method in forbidden:
        assert not hasattr(registry, method), f"Registry should not have {method!r}"


def test_registry_does_not_have_aggregation_methods(registry):
    """API Contract: NO aggregation methods (minimal)."""
    forbidden = ["aggregate", "count", "sum", "group_by", "stats", "summary"]
    for method in forbidden:
        assert not hasattr(registry, method), f"Registry should not have {method!r}"


# ============================================================
# Independence (Multiple Registry Instances)
# ============================================================


def test_multiple_registry_instances_are_independent():
    """Multiple Registry instances: independent state (in-memory only)."""
    r1 = ObservationRegistry()
    r2 = ObservationRegistry()
    artifact = _make_artifact(artifact_id="obs-iso")
    r1.register(artifact)
    assert r1.query_by_id("obs-iso") is not None
    assert r2.query_by_id("obs-iso") is None


# ============================================================
# Consumer → Registry Integration Test
# ============================================================


def test_consumer_then_registry_integration():
    """End-to-end: Consumer → Registry → query."""
    from tools.observation.consumer import RuntimeEventConsumer
    from dataclasses import dataclass, field
    import time

    @dataclass
    class MockEvent:
        type: str = "task.started"
        payload: dict = field(default_factory=dict)
        task_id: str = "task-1"
        source: str = ""
        trace_id: str = "trace-1"
        phase: str = ""
        timestamp: float = field(default_factory=time.time)

    consumer = RuntimeEventConsumer()
    registry = ObservationRegistry()

    event = MockEvent()
    artifact = consumer.consume(event, id_prefix="integration")
    registry.register(artifact)

    # Query by id
    found = registry.query_by_id(artifact.id)
    assert found is not None
    assert found.id == artifact.id

    # Query by execution_id (event.trace_id = "trace-1")
    found_list = registry.query_by_execution_id("trace-1")
    assert len(found_list) == 1
    assert found_list[0].id == artifact.id
