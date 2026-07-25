"""tests/presentation/consumer/test_observation_consumer.py — Phase 3.13 Step 3 Consumer Tests.

Tests (user spec):
- consume valid model
- reject invalid schema
- no mutation
"""
from __future__ import annotations

import json

import pytest

from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)
from tools.presentation.adapter import ObservationPresentationAdapter
from tools.presentation.consumer import ObservationConsumer
from tools.presentation.contract import (
    ObservationViewModel,
    PresentationCategory,
    PresentationSeverity,
    PresentationSource,
)


def _make_artifact() -> ObservationArtifact:
    """Helper: standard test artifact."""
    return ObservationArtifact(
        id="obs-001",
        observation_type=ObservationType.PERFORMANCE,
        content={"event_type": "task.started", "payload": {"latency_ms": 120.5}},
        score=ObservationScore(relevance=1.0, confidence=1.0, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="test",
        task_id="task-1",
    )


def _make_view_model() -> ObservationViewModel:
    """Helper: standard test view model (from Adapter)."""
    adapter = ObservationPresentationAdapter()
    return adapter.adapt(_make_artifact())


@pytest.fixture
def consumer() -> ObservationConsumer:
    """Standard consumer instance."""
    return ObservationConsumer()


# ============================================================
# Basic Produce Tests
# ============================================================


def test_produce_returns_dict(consumer):
    """produce(): returns dict (presentation output)."""
    vm = _make_view_model()
    output = consumer.produce(vm)
    assert isinstance(output, dict)


def test_produce_output_has_all_fields(consumer):
    """produce(): output has all 10 fields from view model."""
    vm = _make_view_model()
    output = consumer.produce(vm)
    expected_fields = {
        "id", "title", "summary", "category", "severity",
        "timestamp", "source", "metrics", "metadata", "schema_version",
    }
    assert set(output.keys()) == expected_fields


def test_produce_does_not_mutate_view_model(consumer):
    """produce(): does NOT mutate view_model (read-only)."""
    vm = _make_view_model()
    original_id = vm.id
    original_title = vm.title
    consumer.produce(vm)
    assert vm.id == original_id
    assert vm.title == original_title


# ============================================================
# JSON Serialization Tests
# ============================================================


def test_produce_json_returns_string(consumer):
    """produce_json(): returns JSON string."""
    vm = _make_view_model()
    output = consumer.produce_json(vm)
    assert isinstance(output, str)


def test_produce_json_is_parseable(consumer):
    """produce_json(): output is valid JSON."""
    vm = _make_view_model()
    output = consumer.produce_json(vm)
    parsed = json.loads(output)
    assert parsed["id"] == vm.id
    assert parsed["category"] == vm.category.value


def test_produce_json_round_trip(consumer):
    """produce_json(): round-trip preserves all fields."""
    vm = _make_view_model()
    json_str = consumer.produce_json(vm)
    parsed = json.loads(json_str)
    assert parsed["title"] == vm.title
    assert parsed["summary"] == vm.summary
    assert parsed["severity"] == vm.severity.value
    assert parsed["source"] == vm.source.value


# ============================================================
# Schema Validation Tests
# ============================================================


def test_produce_rejects_invalid_schema_version(consumer):
    """produce(): rejects view model with invalid schema_version."""
    # Construct invalid view model via __new__ (bypass validation)
    invalid_vm = ObservationViewModel(
        id="vm-invalid",
        title="t",
        summary="s",
        category=PresentationCategory.PERFORMANCE,
        severity=PresentationSeverity.INFO,
        source=PresentationSource.RUNTIME,
    )
    # Manually override schema_version (frozen allows this via object.__setattr__)
    object.__setattr__(invalid_vm, "schema_version", "invalid.v999.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce(invalid_vm)


def test_produce_json_rejects_invalid_schema_version(consumer):
    """produce_json(): rejects view model with invalid schema_version."""
    invalid_vm = ObservationViewModel(
        id="vm-invalid",
        title="t",
        summary="s",
        category=PresentationCategory.PERFORMANCE,
        severity=PresentationSeverity.INFO,
        source=PresentationSource.RUNTIME,
    )
    object.__setattr__(invalid_vm, "schema_version", "old.v0.0")
    with pytest.raises(ValueError, match="Invalid schema version"):
        consumer.produce_json(invalid_vm)


# ============================================================
# Pure Function Tests
# ============================================================


def test_produce_is_pure_function(consumer):
    """produce() is pure: same view model → same output."""
    vm = _make_view_model()
    output1 = consumer.produce(vm)
    output2 = consumer.produce(vm)
    assert output1 == output2


def test_consumer_is_stateless(consumer):
    """Consumer is stateless: multiple instances produce same output."""
    c1 = ObservationConsumer()
    c2 = ObservationConsumer()
    vm = _make_view_model()
    assert c1.produce(vm) == c2.produce(vm)


# ============================================================
# Boundary Compliance Tests (Forbidden Couplings)
# ============================================================


def test_consumer_has_no_eventbus_reference(consumer):
    """Boundary: Consumer has NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_observation_store_reference(consumer):
    """Boundary: Consumer has NO Observation Store (Registry) reference."""
    forbidden_attrs = ["registry", "store", "repository", "database", "cache"]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_runtime_reference(consumer):
    """Boundary: Consumer has NO Runtime reference."""
    forbidden_attrs = [
        "runtime", "event", "session", "engine", "orchestrator",
        "task", "execution",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(consumer, attr), f"Consumer should not have {attr!r}"


def test_consumer_has_no_subscribe_method(consumer):
    """Boundary: Consumer has no subscribe() method."""
    assert not hasattr(consumer, "subscribe")
    assert not hasattr(consumer, "register")
    assert not hasattr(consumer, "publish")


def test_consumer_has_no_storage_methods(consumer):
    """Boundary: Consumer has no storage methods (no save/load/persist)."""
    forbidden_methods = ["save", "load", "persist", "flush", "sync", "cache"]
    for method in forbidden_methods:
        assert not hasattr(consumer, method), f"Consumer should not have {method!r}"


def test_consumer_has_no_artifact_dependency(consumer):
    """Boundary: Consumer does NOT depend on ObservationArtifact (only ViewModel)."""
    # Consumer should work with ViewModel alone (not require Artifact).
    import inspect
    source = inspect.getsource(consumer.produce)
    assert "ObservationArtifact" not in source, "Consumer should not reference ObservationArtifact"
