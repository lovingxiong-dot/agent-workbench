"""tests/presentation/adapter/test_observation_presentation_adapter.py — Phase 3.13 Step 2 Tests.

Tests (user spec):
- artifact mapping
- missing optional fields
- metadata preservation
- schema_version handling
- pure function (deterministic)
- stateless
"""
from __future__ import annotations

import pytest

from tools.observation.contract import (
    ObservationArtifact,
    ObservationScore,
    ObservationSource,
    ObservationType,
)
from tools.presentation.adapter import ObservationPresentationAdapter
from tools.presentation.contract import (
    ObservationViewModel,
    PresentationCategory,
    PresentationSeverity,
    PresentationSource,
)


def _make_artifact(
    artifact_id: str = "obs-001",
    observation_type: ObservationType = ObservationType.PERFORMANCE,
    confidence: float = 1.0,
    content: dict = None,
    task_id: str = "task-1",
    source: ObservationSource = ObservationSource.RUNTIME,
) -> ObservationArtifact:
    """Helper: create test artifact."""
    if content is None:
        content = {"event_type": "task.started", "payload": {"latency_ms": 120.5}}
    return ObservationArtifact(
        id=artifact_id,
        observation_type=observation_type,
        content=content,
        score=ObservationScore(relevance=1.0, confidence=confidence, stability=1.0),
        source=source,
        created_by="test",
        task_id=task_id,
    )


@pytest.fixture
def adapter() -> ObservationPresentationAdapter:
    """Standard adapter instance."""
    return ObservationPresentationAdapter()


# ============================================================
# Basic Mapping Tests
# ============================================================


def test_adapt_returns_observation_view_model(adapter):
    """adapt() returns ObservationViewModel."""
    artifact = _make_artifact()
    vm = adapter.adapt(artifact)
    assert isinstance(vm, ObservationViewModel)


def test_adapt_id_includes_artifact_id(adapter):
    """adapt(): vm id = '{prefix}-{artifact.id}'."""
    artifact = _make_artifact(artifact_id="obs-xyz")
    vm = adapter.adapt(artifact)
    assert vm.id == "vm-obs-xyz"


def test_adapt_accepts_custom_id_prefix(adapter):
    """adapt(): custom id_prefix."""
    artifact = _make_artifact(artifact_id="obs-001")
    vm = adapter.adapt(artifact, id_prefix="custom")
    assert vm.id == "custom-obs-001"


def test_adapt_maps_category_from_observation_type(adapter):
    """adapt(): ObservationType → PresentationCategory (1:1)."""
    for obs_type, expected_cat in [
        (ObservationType.PERFORMANCE, PresentationCategory.PERFORMANCE),
        (ObservationType.RESOURCE, PresentationCategory.RESOURCE),
        (ObservationType.LIFECYCLE, PresentationCategory.LIFECYCLE),
        (ObservationType.EVENT, PresentationCategory.EVENT),
        (ObservationType.HEALTH, PresentationCategory.HEALTH),
    ]:
        artifact = _make_artifact(observation_type=obs_type)
        vm = adapter.adapt(artifact)
        assert vm.category == expected_cat


def test_adapt_maps_source_from_observation_source(adapter):
    """adapt(): ObservationSource → PresentationSource (1:1)."""
    for obs_source, expected_src in [
        (ObservationSource.HUMAN, PresentationSource.HUMAN),
        (ObservationSource.AGENT, PresentationSource.AGENT),
        (ObservationSource.RUNTIME, PresentationSource.RUNTIME),
        (ObservationSource.SYSTEM, PresentationSource.SYSTEM),
    ]:
        artifact = _make_artifact(source=obs_source)
        vm = adapter.adapt(artifact)
        assert vm.source == expected_src


# ============================================================
# Title / Summary Derivation Tests
# ============================================================


def test_adapt_derives_title_with_task_id(adapter):
    """adapt(): title = '{Category} · {task_id}' when task_id present."""
    artifact = _make_artifact(task_id="task-abc")
    vm = adapter.adapt(artifact)
    assert vm.title == "Performance · task-abc"


def test_adapt_derives_title_without_task_id(adapter):
    """adapt(): title = '{Category} Observation' when task_id empty."""
    artifact = _make_artifact(task_id="")
    vm = adapter.adapt(artifact)
    assert vm.title == "Performance Observation"


def test_adapt_derives_summary_from_event_type(adapter):
    """adapt(): summary = 'Event: {event_type}' when event_type in content."""
    artifact = _make_artifact(content={"event_type": "task.started", "payload": {}})
    vm = adapter.adapt(artifact)
    assert vm.summary == "Event: task.started"


def test_adapt_derives_summary_fallback(adapter):
    """adapt(): summary fallback = 'Source={source} Score={confidence:.2f}'."""
    artifact = _make_artifact(content="non-dict-content", confidence=0.85)
    vm = adapter.adapt(artifact)
    assert vm.summary == "Source=runtime Score=0.85"


# ============================================================
# Severity Inference Tests
# ============================================================


@pytest.mark.parametrize(
    "confidence,expected_severity",
    [
        (0.0, PresentationSeverity.CRITICAL),
        (0.3, PresentationSeverity.CRITICAL),
        (0.4, PresentationSeverity.ERROR),
        (0.6, PresentationSeverity.ERROR),
        (0.7, PresentationSeverity.WARNING),
        (0.9, PresentationSeverity.WARNING),
        (1.0, PresentationSeverity.INFO),
    ],
)
def test_adapt_infers_severity_from_confidence(adapter, confidence, expected_severity):
    """adapt(): severity inferred from confidence score (rule-based, no AI)."""
    artifact = _make_artifact(confidence=confidence)
    vm = adapter.adapt(artifact)
    assert vm.severity == expected_severity


# ============================================================
# Metrics / Metadata Extraction Tests
# ============================================================


def test_adapt_extracts_metrics_from_payload(adapter):
    """adapt(): metrics = content['payload'] (display-ready)."""
    artifact = _make_artifact(content={"event_type": "x", "payload": {"latency_ms": 100, "tokens": 50}})
    vm = adapter.adapt(artifact)
    assert vm.metrics == {"latency_ms": 100, "tokens": 50}


def test_adapt_metrics_empty_when_no_payload(adapter):
    """adapt(): metrics = {} when content has no payload."""
    artifact = _make_artifact(content={"event_type": "x"})
    vm = adapter.adapt(artifact)
    assert vm.metrics == {}


def test_adapt_metadata_preserves_source_info(adapter):
    """adapt(): metadata includes source schema_version, id, type."""
    artifact = _make_artifact(artifact_id="obs-meta")
    vm = adapter.adapt(artifact)
    assert vm.metadata["source_schema_version"] == "observation.v0.1"
    assert vm.metadata["source_id"] == "obs-meta"
    assert vm.metadata["source_type"] == "performance"


def test_adapt_metadata_includes_non_payload_content(adapter):
    """adapt(): metadata includes non-payload content fields."""
    artifact = _make_artifact(content={"event_type": "task.started", "phase": "inference", "payload": {}})
    vm = adapter.adapt(artifact)
    assert vm.metadata["event_type"] == "task.started"
    assert vm.metadata["phase"] == "inference"


# ============================================================
# Schema Version Tests
# ============================================================


def test_adapt_output_uses_presentation_schema_version(adapter):
    """adapt(): output uses frozen 'presentation.v0.1'."""
    artifact = _make_artifact()
    vm = adapter.adapt(artifact)
    assert vm.schema_version == "presentation.v0.1"


def test_adapt_metadata_preserves_source_schema_version(adapter):
    """adapt(): metadata['source_schema_version'] = 'observation.v0.1'."""
    artifact = _make_artifact()
    vm = adapter.adapt(artifact)
    assert vm.metadata["source_schema_version"] == "observation.v0.1"


# ============================================================
# Pure Function Tests (Deterministic + Stateless)
# ============================================================


def test_adapt_is_pure_function(adapter):
    """adapt() is pure: same artifact → same view model structure."""
    artifact = _make_artifact(artifact_id="obs-pure")
    vm1 = adapter.adapt(artifact)
    vm2 = adapter.adapt(artifact)
    assert vm1.id == vm2.id
    assert vm1.title == vm2.title
    assert vm1.summary == vm2.summary
    assert vm1.category == vm2.category
    assert vm1.severity == vm2.severity
    assert vm1.source == vm2.source
    assert vm1.timestamp == vm2.timestamp
    assert vm1.metrics == vm2.metrics
    assert vm1.metadata == vm2.metadata
    assert vm1.schema_version == vm2.schema_version


def test_adapter_is_stateless(adapter):
    """Adapter is stateless: multiple instances produce same output."""
    adapter1 = ObservationPresentationAdapter()
    adapter2 = ObservationPresentationAdapter()
    artifact = _make_artifact()
    vm1 = adapter1.adapt(artifact)
    vm2 = adapter2.adapt(artifact)
    assert vm1 == vm2


# ============================================================
# Boundary Compliance Tests
# ============================================================


def test_adapter_has_no_eventbus_reference(adapter):
    """Boundary: Adapter has NO EventBus reference."""
    forbidden_attrs = ["eventbus", "event_bus", "bus", "subscriber", "subscribers"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"


def test_adapter_has_no_storage_methods(adapter):
    """Boundary: Adapter has NO storage methods (cache, save, load)."""
    forbidden_methods = ["save", "load", "cache", "persist", "flush", "sync"]
    for method in forbidden_methods:
        assert not hasattr(adapter, method), f"Adapter should not have {method!r}"


def test_adapter_has_no_subscribe_method(adapter):
    """Boundary: Adapter has no subscribe() method (no event subscription)."""
    assert not hasattr(adapter, "subscribe")
    assert not hasattr(adapter, "register")
    assert not hasattr(adapter, "publish")


def test_adapter_has_no_runtime_dependency(adapter):
    """Boundary: Adapter has no runtime / event / session / engine dependency."""
    forbidden_attrs = ["runtime", "event", "session", "engine", "orchestrator"]
    for attr in forbidden_attrs:
        assert not hasattr(adapter, attr), f"Adapter should not have {attr!r}"
