"""tests/observation/contract/test_observation_artifact.py — Phase 3.12 ObservationArtifact Contract Tests.

Phase 3.12 Batch 1: Observation Contract Schema (Schema-First) tests.

Tests (60% Primitive):
- ObservationType: 5 类 enum + values
- ObservationSource: 4 类 enum + values
- ObservationScore: 3 维 validation (0.0-1.0)
- ObservationArtifact: frozen dataclass + validation + serialization
- Schema version: frozen = "observation.v0.1"
- to_dict(): JSON-friendly serialization
"""
from __future__ import annotations

import json

import pytest

from tools.observation.contract import (
    OBSERVATION_SCHEMA_VERSION,
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)


# ============================================================
# Schema Version Tests
# ============================================================


def test_schema_version_is_observation_v0_1():
    """Contract Frozen: schema_version = "observation.v0.1" (ADR-016)."""
    assert OBSERVATION_SCHEMA_VERSION == "observation.v0.1"


# ============================================================
# ObservationType Tests
# ============================================================


def test_observation_type_has_5_categories():
    """Contract: 5 类 ObservationType (Performance / Resource / Lifecycle / Event / Health)."""
    assert len(ObservationType) == 5


def test_observation_type_values():
    """Contract: ObservationType values are frozen strings."""
    assert ObservationType.PERFORMANCE.value == "performance"
    assert ObservationType.RESOURCE.value == "resource"
    assert ObservationType.LIFECYCLE.value == "lifecycle"
    assert ObservationType.EVENT.value == "event"
    assert ObservationType.HEALTH.value == "health"


def test_observation_type_inherits_string():
    """ObservationType 继承 str, 可直接用于 JSON / dict 序列化."""
    assert isinstance(ObservationType.PERFORMANCE, str)
    assert ObservationType.PERFORMANCE == "performance"


# ============================================================
# ObservationSource Tests
# ============================================================


def test_observation_source_has_4_categories():
    """Contract: 4 类 ObservationSource (human / agent / runtime / system)."""
    assert len(ObservationSource) == 4


def test_observation_source_values():
    """Contract: ObservationSource values are frozen strings."""
    assert ObservationSource.HUMAN.value == "human"
    assert ObservationSource.AGENT.value == "agent"
    assert ObservationSource.RUNTIME.value == "runtime"
    assert ObservationSource.SYSTEM.value == "system"


# ============================================================
# ObservationScore Tests
# ============================================================


def test_observation_score_default_zero():
    """Contract: ObservationScore default = (0.0, 0.0, 0.0)."""
    score = ObservationScore()
    assert score.relevance == 0.0
    assert score.confidence == 0.0
    assert score.stability == 0.0


def test_observation_score_explicit_values():
    """Contract: ObservationScore accepts 0.0-1.0 values."""
    score = ObservationScore(relevance=0.9, confidence=0.8, stability=1.0)
    assert score.relevance == 0.9
    assert score.confidence == 0.8
    assert score.stability == 1.0


def test_observation_score_rejects_relevance_below_0():
    """Validation: relevance < 0.0 raises ValueError."""
    with pytest.raises(ValueError, match="relevance must be in"):
        ObservationScore(relevance=-0.1)


def test_observation_score_rejects_relevance_above_1():
    """Validation: relevance > 1.0 raises ValueError."""
    with pytest.raises(ValueError, match="relevance must be in"):
        ObservationScore(relevance=1.1)


def test_observation_score_rejects_confidence_below_0():
    """Validation: confidence < 0.0 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        ObservationScore(confidence=-0.5)


def test_observation_score_rejects_confidence_above_1():
    """Validation: confidence > 1.0 raises ValueError."""
    with pytest.raises(ValueError, match="confidence must be in"):
        ObservationScore(confidence=1.5)


def test_observation_score_rejects_stability_below_0():
    """Validation: stability < 0.0 raises ValueError."""
    with pytest.raises(ValueError, match="stability must be in"):
        ObservationScore(stability=-0.01)


def test_observation_score_rejects_stability_above_1():
    """Validation: stability > 1.0 raises ValueError."""
    with pytest.raises(ValueError, match="stability must be in"):
        ObservationScore(stability=1.01)


def test_observation_score_accepts_boundary_values():
    """Validation: 0.0 and 1.0 are valid boundary values."""
    score_low = ObservationScore(relevance=0.0, confidence=0.0, stability=0.0)
    score_high = ObservationScore(relevance=1.0, confidence=1.0, stability=1.0)
    assert score_low.relevance == 0.0
    assert score_high.relevance == 1.0


# ============================================================
# ObservationArtifact Tests
# ============================================================


def _make_score() -> ObservationScore:
    """Helper: standard test score (0.9, 0.8, 1.0)."""
    return ObservationScore(relevance=0.9, confidence=0.8, stability=1.0)


def test_observation_artifact_minimal_required():
    """Contract: id / type / content / score / source are required."""
    artifact = ObservationArtifact(
        id="obs-001",
        observation_type=ObservationType.PERFORMANCE,
        content={"latency_ms": 120.5},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test_agent",
    )
    assert artifact.id == "obs-001"
    assert artifact.observation_type == ObservationType.PERFORMANCE
    assert artifact.content == {"latency_ms": 120.5}
    assert artifact.score.relevance == 0.9
    assert artifact.source == ObservationSource.RUNTIME
    assert artifact.created_by == "test_agent"
    assert artifact.schema_version == "observation.v0.1"


def test_observation_artifact_default_execution_metadata():
    """Contract: execution_id / task_id default to empty string."""
    artifact = ObservationArtifact(
        id="obs-002",
        observation_type=ObservationType.LIFECYCLE,
        content={"state": "PLANNING"},
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="test",
    )
    assert artifact.execution_id == ""
    assert artifact.task_id == ""


def test_observation_artifact_with_execution_metadata():
    """Contract: execution_id / task_id 可选填充."""
    artifact = ObservationArtifact(
        id="obs-003",
        observation_type=ObservationType.EVENT,
        content={"event": "TASK_STARTED"},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="runtime_event_adapter",
        execution_id="exec-123",
        task_id="task-456",
    )
    assert artifact.execution_id == "exec-123"
    assert artifact.task_id == "task-456"


def test_observation_artifact_schema_version_frozen():
    """Contract: schema_version is fixed to "observation.v0.1"."""
    artifact = ObservationArtifact(
        id="obs-004",
        observation_type=ObservationType.HEALTH,
        content={"status": "ok"},
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="health_checker",
    )
    assert artifact.schema_version == "observation.v0.1"


# ============================================================
# Validation Tests
# ============================================================


def test_observation_artifact_rejects_empty_id():
    """Validation: empty id raises ValueError."""
    with pytest.raises(ValueError, match="id must be non-empty"):
        ObservationArtifact(
            id="",
            observation_type=ObservationType.PERFORMANCE,
            content={},
            score=_make_score(),
            source=ObservationSource.RUNTIME,
            created_by="test",
        )


def test_observation_artifact_rejects_empty_created_by():
    """Validation: empty created_by raises ValueError (Provenance 强制)."""
    with pytest.raises(ValueError, match="created_by must be non-empty"):
        ObservationArtifact(
            id="obs-005",
            observation_type=ObservationType.PERFORMANCE,
            content={},
            score=_make_score(),
            source=ObservationSource.RUNTIME,
            created_by="",
        )


# ============================================================
# Frozen Dataclass Tests
# ============================================================


def test_observation_artifact_is_frozen():
    """Contract: ObservationArtifact is frozen (immutable)."""
    artifact = ObservationArtifact(
        id="obs-006",
        observation_type=ObservationType.RESOURCE,
        content={"memory_mb": 512},
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="resource_monitor",
    )
    with pytest.raises((AttributeError, Exception)):
        artifact.id = "obs-006-modified"  # type: ignore


def test_observation_artifact_equality_by_value():
    """Frozen dataclass: equality by value."""
    a = ObservationArtifact(
        id="obs-eq",
        observation_type=ObservationType.PERFORMANCE,
        content={"v": 1},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
        created_at=100.0,
    )
    b = ObservationArtifact(
        id="obs-eq",
        observation_type=ObservationType.PERFORMANCE,
        content={"v": 1},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
        created_at=100.0,
    )
    c = ObservationArtifact(
        id="obs-different",
        observation_type=ObservationType.PERFORMANCE,
        content={"v": 1},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
        created_at=100.0,
    )
    assert a == b
    assert a != c


# ============================================================
# to_dict() Serialization Tests
# ============================================================


def test_to_dict_basic():
    """to_dict(): basic structure with all fields."""
    artifact = ObservationArtifact(
        id="obs-dict-001",
        observation_type=ObservationType.PERFORMANCE,
        content={"latency_ms": 120.5},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
        created_at=1700000000.0,
        execution_id="exec-1",
        task_id="task-1",
    )
    result = artifact.to_dict()
    assert result["id"] == "obs-dict-001"
    assert result["schema_version"] == "observation.v0.1"
    assert result["observation_type"] == "performance"
    assert result["source"] == "runtime"
    assert result["score"] == {
        "relevance": 0.9,
        "confidence": 0.8,
        "stability": 1.0,
    }
    assert result["created_at"] == 1700000000.0
    assert result["created_by"] == "test"
    assert result["execution_id"] == "exec-1"
    assert result["task_id"] == "task-1"
    assert result["content"] == {"latency_ms": 120.5}


def test_to_dict_serializes_primitive_content():
    """to_dict(): primitive content (str/int/float/bool/None) preserved."""
    for primitive in ["string", 42, 3.14, True, False, None]:
        artifact = ObservationArtifact(
            id=f"obs-prim-{type(primitive).__name__}",
            observation_type=ObservationType.EVENT,
            content=primitive,
            score=_make_score(),
            source=ObservationSource.SYSTEM,
            created_by="test",
        )
        result = artifact.to_dict()
        assert result["content"] == primitive


def test_to_dict_serializes_nested_dict_content():
    """to_dict(): nested dict content (recursive serialization)."""
    artifact = ObservationArtifact(
        id="obs-nested",
        observation_type=ObservationType.HEALTH,
        content={"metrics": {"cpu": 0.8, "memory": 0.5}, "status": "ok"},
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="health",
    )
    result = artifact.to_dict()
    assert result["content"] == {
        "metrics": {"cpu": 0.8, "memory": 0.5},
        "status": "ok",
    }


def test_to_dict_serializes_list_content():
    """to_dict(): list content (recursive serialization)."""
    artifact = ObservationArtifact(
        id="obs-list",
        observation_type=ObservationType.EVENT,
        content=[1, 2, {"key": "value"}],
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
    )
    result = artifact.to_dict()
    assert result["content"] == [1, 2, {"key": "value"}]


def test_to_dict_falls_back_to_str_for_unsupported_content():
    """to_dict(): unsupported content (e.g. object) falls back to str()."""
    artifact = ObservationArtifact(
        id="obs-obj",
        observation_type=ObservationType.EVENT,
        content=object(),  # plain object
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="test",
    )
    result = artifact.to_dict()
    # Falls back to str() representation
    assert isinstance(result["content"], str)


def test_to_dict_is_json_serializable():
    """to_dict(): output is JSON-serializable (stringifiable)."""
    artifact = ObservationArtifact(
        id="obs-json",
        observation_type=ObservationType.PERFORMANCE,
        content={"nested": {"key": [1, 2, 3]}},
        score=_make_score(),
        source=ObservationSource.RUNTIME,
        created_by="test",
    )
    result = artifact.to_dict()
    # Should not raise
    serialized = json.dumps(result)
    assert isinstance(serialized, str)
    # Should round-trip
    deserialized = json.loads(serialized)
    assert deserialized["id"] == "obs-json"
    assert deserialized["observation_type"] == "performance"


# ============================================================
# All 5 ObservationType Can Be Used
# ============================================================


@pytest.mark.parametrize(
    "obs_type",
    [
        ObservationType.PERFORMANCE,
        ObservationType.RESOURCE,
        ObservationType.LIFECYCLE,
        ObservationType.EVENT,
        ObservationType.HEALTH,
    ],
)
def test_all_5_observation_types_constructable(obs_type):
    """Contract: All 5 ObservationType values construct valid artifacts."""
    artifact = ObservationArtifact(
        id=f"obs-{obs_type.value}",
        observation_type=obs_type,
        content={"test": True},
        score=_make_score(),
        source=ObservationSource.SYSTEM,
        created_by="test",
    )
    assert artifact.observation_type == obs_type


@pytest.mark.parametrize(
    "source",
    [
        ObservationSource.HUMAN,
        ObservationSource.AGENT,
        ObservationSource.RUNTIME,
        ObservationSource.SYSTEM,
    ],
)
def test_all_4_observation_sources_constructable(source):
    """Contract: All 4 ObservationSource values construct valid artifacts."""
    artifact = ObservationArtifact(
        id=f"obs-src-{source.value}",
        observation_type=ObservationType.PERFORMANCE,
        content={"test": True},
        score=_make_score(),
        source=source,
        created_by="test",
    )
    assert artifact.source == source
