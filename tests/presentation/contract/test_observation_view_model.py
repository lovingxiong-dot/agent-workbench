"""tests/presentation/contract/test_observation_view_model.py — Phase 3.13 ObservationViewModel Tests.

Tests (60% Primitive):
- schema creation
- serialization roundtrip
- required fields validation
- forbidden field detection (UI/storage/runtime)
- frozen dataclass verification
"""
from __future__ import annotations

import json

import pytest

from tools.presentation.contract import (
    OBSERVATION_VIEW_MODEL_SCHEMA_VERSION,
    ObservationViewModel,
    PresentationCategory,
    PresentationSeverity,
    PresentationSource,
)


# ============================================================
# Schema Version Tests
# ============================================================


def test_schema_version_is_presentation_v0_1():
    """Contract Frozen: schema_version = 'presentation.v0.1' (ADR-017)."""
    assert OBSERVATION_VIEW_MODEL_SCHEMA_VERSION == "presentation.v0.1"


# ============================================================
# PresentationCategory Tests
# ============================================================


def test_presentation_category_has_5_categories():
    """Contract: 5 categories (mirror ObservationType)."""
    assert len(PresentationCategory) == 5


def test_presentation_category_values():
    """Contract: values match ObservationType values."""
    assert PresentationCategory.PERFORMANCE.value == "performance"
    assert PresentationCategory.RESOURCE.value == "resource"
    assert PresentationCategory.LIFECYCLE.value == "lifecycle"
    assert PresentationCategory.EVENT.value == "event"
    assert PresentationCategory.HEALTH.value == "health"


# ============================================================
# PresentationSeverity Tests
# ============================================================


def test_presentation_severity_has_4_categories():
    """Contract: 4 severity levels (presentation-level)."""
    assert len(PresentationSeverity) == 4


def test_presentation_severity_values():
    """Contract: severity values."""
    assert PresentationSeverity.INFO.value == "info"
    assert PresentationSeverity.WARNING.value == "warning"
    assert PresentationSeverity.ERROR.value == "error"
    assert PresentationSeverity.CRITICAL.value == "critical"


# ============================================================
# PresentationSource Tests
# ============================================================


def test_presentation_source_has_4_categories():
    """Contract: 4 source categories (mirror ObservationSource)."""
    assert len(PresentationSource) == 4


def test_presentation_source_values():
    """Contract: source values match ObservationSource values."""
    assert PresentationSource.HUMAN.value == "human"
    assert PresentationSource.AGENT.value == "agent"
    assert PresentationSource.RUNTIME.value == "runtime"
    assert PresentationSource.SYSTEM.value == "system"


# ============================================================
# ObservationViewModel Tests
# ============================================================


def _make_view_model(
    vm_id: str = "vm-001",
    title: str = "Test View Model",
    summary: str = "Test summary",
    category: PresentationCategory = PresentationCategory.PERFORMANCE,
    severity: PresentationSeverity = PresentationSeverity.INFO,
    source: PresentationSource = PresentationSource.RUNTIME,
) -> ObservationViewModel:
    """Helper: create test view model."""
    return ObservationViewModel(
        id=vm_id,
        title=title,
        summary=summary,
        category=category,
        severity=severity,
        source=source,
    )


def test_view_model_minimal_required():
    """Contract: id/title/summary/category/severity/source are required."""
    vm = _make_view_model()
    assert vm.id == "vm-001"
    assert vm.title == "Test View Model"
    assert vm.summary == "Test summary"
    assert vm.category == PresentationCategory.PERFORMANCE
    assert vm.severity == PresentationSeverity.INFO
    assert vm.source == PresentationSource.RUNTIME
    assert vm.schema_version == "presentation.v0.1"


def test_view_model_default_metrics_empty_dict():
    """Contract: metrics default to empty dict."""
    vm = _make_view_model()
    assert vm.metrics == {}


def test_view_model_default_metadata_empty_dict():
    """Contract: metadata default to empty dict."""
    vm = _make_view_model()
    assert vm.metadata == {}


def test_view_model_with_metrics_and_metadata():
    """Contract: metrics and metadata can be populated."""
    metrics = {"latency_ms": 120.5, "throughput": 1000}
    metadata = {"raw_event": "task.started", "task_id": "task-1"}
    vm = ObservationViewModel(
        id="vm-002",
        title="Performance",
        summary="Task latency observation",
        category=PresentationCategory.PERFORMANCE,
        severity=PresentationSeverity.WARNING,
        source=PresentationSource.RUNTIME,
        metrics=metrics,
        metadata=metadata,
    )
    assert vm.metrics == metrics
    assert vm.metadata == metadata


def test_view_model_is_frozen():
    """Contract: ObservationViewModel is frozen (immutable)."""
    vm = _make_view_model()
    with pytest.raises((AttributeError, Exception)):
        vm.id = "vm-modified"  # type: ignore


def test_view_model_equality_by_value():
    """Contract: equality by value (frozen dataclass)."""
    vm1 = _make_view_model(vm_id="vm-eq")
    vm2 = _make_view_model(vm_id="vm-eq")
    vm3 = _make_view_model(vm_id="vm-diff")
    assert vm1 == vm2
    assert vm1 != vm3


# ============================================================
# Required Field Validation Tests
# ============================================================


def test_view_model_rejects_empty_id():
    """Validation: empty id raises ValueError."""
    with pytest.raises(ValueError, match="id must be non-empty"):
        ObservationViewModel(
            id="",
            title="t",
            summary="s",
            category=PresentationCategory.PERFORMANCE,
            severity=PresentationSeverity.INFO,
            source=PresentationSource.RUNTIME,
        )


def test_view_model_rejects_empty_title():
    """Validation: empty title raises ValueError (display-ready)."""
    with pytest.raises(ValueError, match="title must be non-empty"):
        ObservationViewModel(
            id="vm-001",
            title="",
            summary="s",
            category=PresentationCategory.PERFORMANCE,
            severity=PresentationSeverity.INFO,
            source=PresentationSource.RUNTIME,
        )


def test_view_model_rejects_empty_summary():
    """Validation: empty summary raises ValueError (display-ready)."""
    with pytest.raises(ValueError, match="summary must be non-empty"):
        ObservationViewModel(
            id="vm-001",
            title="t",
            summary="",
            category=PresentationCategory.PERFORMANCE,
            severity=PresentationSeverity.INFO,
            source=PresentationSource.RUNTIME,
        )


# ============================================================
# Serialization Tests
# ============================================================


def test_to_dict_basic():
    """to_dict(): basic structure with all fields."""
    metrics = {"latency_ms": 120.5}
    metadata = {"task_id": "task-1"}
    vm = ObservationViewModel(
        id="vm-dict-001",
        title="Performance Alert",
        summary="Task latency exceeds threshold",
        category=PresentationCategory.PERFORMANCE,
        severity=PresentationSeverity.WARNING,
        source=PresentationSource.RUNTIME,
        timestamp=1700000000.0,
        metrics=metrics,
        metadata=metadata,
    )
    result = vm.to_dict()
    assert result["id"] == "vm-dict-001"
    assert result["title"] == "Performance Alert"
    assert result["summary"] == "Task latency exceeds threshold"
    assert result["category"] == "performance"
    assert result["severity"] == "warning"
    assert result["timestamp"] == 1700000000.0
    assert result["source"] == "runtime"
    assert result["metrics"] == {"latency_ms": 120.5}
    assert result["metadata"] == {"task_id": "task-1"}
    assert result["schema_version"] == "presentation.v0.1"


def test_to_dict_is_json_serializable():
    """to_dict(): JSON-serializable (round-trip)."""
    vm = _make_view_model()
    result = vm.to_dict()
    serialized = json.dumps(result)
    deserialized = json.loads(serialized)
    assert deserialized["id"] == vm.id
    assert deserialized["category"] == vm.category.value
    assert deserialized["severity"] == vm.severity.value
    assert deserialized["source"] == vm.source.value


# ============================================================
# Forbidden Field Detection Tests (UI/Storage/Runtime coupling)
# ============================================================


def test_view_model_has_no_ui_fields():
    """Boundary: NO UI fields (renderer/widget/layout/panel/theme/style/view_state)."""
    vm = _make_view_model()
    forbidden_attrs = [
        "renderer", "widget", "layout", "panel", "theme",
        "style", "view_state", "css", "qml", "html",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(vm, attr), f"ObservationViewModel should not have {attr!r}"


def test_view_model_has_no_storage_fields():
    """Boundary: NO storage fields (database/file/cache/persistence)."""
    vm = _make_view_model()
    forbidden_attrs = [
        "database", "file_path", "cache", "persistent", "store",
        "save", "load",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(vm, attr), f"ObservationViewModel should not have {attr!r}"


def test_view_model_has_no_runtime_fields():
    """Boundary: NO runtime fields (event/session/engine/orchestrator)."""
    vm = _make_view_model()
    forbidden_attrs = [
        "runtime_event", "session", "engine", "orchestrator",
        "execution_id", "task_id",  # These are ObservationArtifact fields, not ViewModel
    ]
    # Note: ObservationViewModel may have execution_id/task_id as metadata, not as direct fields
    for attr in ["runtime_event", "session", "engine", "orchestrator"]:
        assert not hasattr(vm, attr), f"ObservationViewModel should not have {attr!r}"


# ============================================================
# Parametrized Category / Severity / Source Tests
# ============================================================


@pytest.mark.parametrize(
    "category",
    [
        PresentationCategory.PERFORMANCE,
        PresentationCategory.RESOURCE,
        PresentationCategory.LIFECYCLE,
        PresentationCategory.EVENT,
        PresentationCategory.HEALTH,
    ],
)
def test_all_5_categories_constructable(category):
    """Contract: All 5 PresentationCategory values construct valid view models."""
    vm = ObservationViewModel(
        id=f"vm-{category.value}",
        title="t",
        summary="s",
        category=category,
        severity=PresentationSeverity.INFO,
        source=PresentationSource.RUNTIME,
    )
    assert vm.category == category


@pytest.mark.parametrize(
    "severity",
    [
        PresentationSeverity.INFO,
        PresentationSeverity.WARNING,
        PresentationSeverity.ERROR,
        PresentationSeverity.CRITICAL,
    ],
)
def test_all_4_severities_constructable(severity):
    """Contract: All 4 PresentationSeverity values construct valid view models."""
    vm = ObservationViewModel(
        id=f"vm-{severity.value}",
        title="t",
        summary="s",
        category=PresentationCategory.PERFORMANCE,
        severity=severity,
        source=PresentationSource.RUNTIME,
    )
    assert vm.severity == severity


@pytest.mark.parametrize(
    "source",
    [
        PresentationSource.HUMAN,
        PresentationSource.AGENT,
        PresentationSource.RUNTIME,
        PresentationSource.SYSTEM,
    ],
)
def test_all_4_sources_constructable(source):
    """Contract: All 4 PresentationSource values construct valid view models."""
    vm = ObservationViewModel(
        id=f"vm-{source.value}",
        title="t",
        summary="s",
        category=PresentationCategory.PERFORMANCE,
        severity=PresentationSeverity.INFO,
        source=source,
    )
    assert vm.source == source
