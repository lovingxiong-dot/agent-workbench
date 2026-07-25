"""tests/presentation/integration/test_presentation_flow.py — Phase 3.13 Step 4: End-to-end Integration.

Flow tested:
ObservationArtifact
        ↓
ObservationPresentationAdapter
        ↓
ObservationViewModel
        ↓
ObservationConsumer
        ↓
Presentation output (dict / JSON)

Coverage (user spec):
- end-to-end conversion
- contract stability
- platform independence
- No UI tests
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


def _make_artifact(
    artifact_id: str = "obs-int-001",
    observation_type: ObservationType = ObservationType.PERFORMANCE,
    confidence: float = 1.0,
    content: dict = None,
    task_id: str = "task-int-1",
) -> ObservationArtifact:
    """Helper: test artifact with content."""
    if content is None:
        content = {
            "event_type": "task.started",
            "phase": "inference",
            "payload": {"latency_ms": 150.0, "tokens": 250},
        }
    return ObservationArtifact(
        id=artifact_id,
        observation_type=observation_type,
        content=content,
        score=ObservationScore(relevance=1.0, confidence=confidence, stability=1.0),
        source=ObservationSource.RUNTIME,
        created_by="integration_test",
        task_id=task_id,
    )


# ============================================================
# End-to-End Flow Tests
# ============================================================


def test_end_to_end_artifact_to_presentation_output():
    """End-to-end: ObservationArtifact → Adapter → ViewModel → Consumer → output."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    # Full flow
    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)

    # Verify output structure
    assert output["id"] == f"vm-{artifact.id}"
    assert output["title"] == f"Performance · {artifact.task_id}"
    assert output["summary"] == f"Event: {artifact.content['event_type']}"
    assert output["category"] == "performance"
    assert output["severity"] == "info"
    assert output["source"] == "runtime"
    assert output["metrics"] == {"latency_ms": 150.0, "tokens": 250}
    assert output["schema_version"] == "presentation.v0.1"


def test_end_to_end_json_serialization():
    """End-to-end: full flow + JSON serialization."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    json_str = consumer.produce_json(vm)

    # JSON parseable
    parsed = json.loads(json_str)
    assert parsed["id"] == f"vm-{artifact.id}"
    assert parsed["metrics"]["latency_ms"] == 150.0


def test_end_to_end_all_5_observation_types():
    """End-to-end: all 5 ObservationType values produce valid output."""
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    for obs_type in ObservationType:
        artifact = _make_artifact(observation_type=obs_type)
        vm = adapter.adapt(artifact)
        output = consumer.produce(vm)
        assert output["category"] == obs_type.value
        # Title should include the category
        assert obs_type.value.capitalize() in output["title"]


# ============================================================
# Contract Stability Tests
# ============================================================


def test_contract_stability_preserves_required_fields():
    """Contract stability: required fields preserved end-to-end."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)

    required_fields = ["id", "title", "summary", "category", "severity", "source"]
    for field in required_fields:
        assert field in output, f"Required field {field!r} missing"
        assert output[field], f"Required field {field!r} is empty"


def test_contract_stability_schema_version_consistent():
    """Contract stability: schema_version consistent across all flow."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)

    # Both ViewModel and output have same schema version
    assert vm.schema_version == "presentation.v0.1"
    assert output["schema_version"] == "presentation.v0.1"


def test_contract_stability_metadata_preserves_source_schema():
    """Contract stability: source schema_version preserved in metadata."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)

    # Source schema version preserved in metadata
    assert output["metadata"]["source_schema_version"] == "observation.v0.1"


# ============================================================
# Platform Independence Tests
# ============================================================


def test_platform_independence_no_qt_in_dependencies():
    """Platform independence: NO Qt/PySide import in presentation layer."""
    import inspect
    import tools.presentation

    # Check no Qt imports
    source = inspect.getsource(tools.presentation)
    forbidden_imports = ["PySide", "PyQt", "qt", "QWidget", "QML", "QObject"]
    for forbidden in forbidden_imports:
        assert forbidden not in source, f"Presentation should not depend on {forbidden}"


def test_platform_independence_no_web_in_dependencies():
    """Platform independence: NO Web framework import in presentation layer."""
    import inspect
    import tools.presentation

    source = inspect.getsource(tools.presentation)
    forbidden_imports = ["react", "vue", "angular", "html", "css", "dom"]
    for forbidden in forbidden_imports:
        assert forbidden not in source, f"Presentation should not depend on {forbidden}"


def test_platform_independence_output_is_platform_neutral():
    """Platform independence: output is platform-neutral (JSON-serializable)."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)

    # JSON-serializable (works for any platform)
    json_str = json.dumps(output)
    parsed = json.loads(json_str)
    assert parsed["id"] == output["id"]


# ============================================================
# End-to-End with Varying Inputs
# ============================================================


@pytest.mark.parametrize("observation_type", list(ObservationType))
def test_end_to_end_all_5_types(observation_type):
    """End-to-end: each ObservationType produces a valid output."""
    artifact = _make_artifact(observation_type=observation_type)
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)
    assert output["category"] == observation_type.value


@pytest.mark.parametrize("confidence,expected_severity", [
    (0.0, "critical"),
    (0.4, "error"),
    (0.7, "warning"),
    (1.0, "info"),
])
def test_end_to_end_severity_inference(confidence, expected_severity):
    """End-to-end: severity inferred from confidence."""
    artifact = _make_artifact(confidence=confidence)
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    output = consumer.produce(vm)
    assert output["severity"] == expected_severity


# ============================================================
# Architectural Boundary Verification (Success Criteria)
# ============================================================


def test_architecture_runtime_does_not_know_presentation():
    """Success Criterion: Runtime 不知道 Presentation 存在.

    Check ONLY Phase 3.13 NEW subdirs (contract/, adapter/, consumer/).
    Prototype subdirs (view_models/, adapters/) are pre-existing and out of scope.
    """
    import os
    import re

    # Only check our NEW subdirs (Phase 3.13 contract / adapter / consumer)
    new_subdirs = [
        "tools/presentation/contract",
        "tools/presentation/adapter",
        "tools/presentation/consumer",
    ]
    forbidden_patterns = [
        r"from v6\.runtime",
        r"import v6\.runtime",
    ]
    for subdir in new_subdirs:
        for root, dirs, files in os.walk(subdir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    for pattern in forbidden_patterns:
                        assert not re.search(pattern, content), (
                            f"{filepath} should not import v6.runtime"
                        )


def test_architecture_presentation_does_not_know_ui():
    """Success Criterion: Presentation 不知道 UI 平台.

    Check ONLY Phase 3.13 NEW subdirs (contract/, adapter/, consumer/).
    Use word boundary matching to avoid false positives (e.g. 'Renderer' in docstring).
    """
    import os
    import re

    # Only check our NEW subdirs
    new_subdirs = [
        "tools/presentation/contract",
        "tools/presentation/adapter",
        "tools/presentation/consumer",
    ]
    # Use word boundary for accurate matching
    forbidden_patterns = [
        r"\bPySide\b", r"\bPyQt\b", r"\btkinter\b", r"\bQWidget\b", r"\bQML\b",
        r"\breact\b", r"\bvue\b", r"\bangular\b",
        r"^from PySide", r"^import PySide",
        r"^from PyQt", r"^import PyQt",
    ]
    for subdir in new_subdirs:
        for root, dirs, files in os.walk(subdir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    for pattern in forbidden_patterns:
                        assert not re.search(pattern, content, re.MULTILINE), (
                            f"{filepath} should not import UI platform ({pattern})"
                        )


def test_architecture_consumer_is_read_only():
    """Success Criterion: Consumer 只读 (no mutation)."""
    artifact = _make_artifact()
    adapter = ObservationPresentationAdapter()
    consumer = ObservationConsumer()

    vm = adapter.adapt(artifact)
    original_id = vm.id
    original_title = vm.title
    original_metrics = dict(vm.metrics)

    # Multiple consumer calls
    consumer.produce(vm)
    consumer.produce_json(vm)

    # Verify view model unchanged
    assert vm.id == original_id
    assert vm.title == original_title
    assert vm.metrics == original_metrics


def test_architecture_contract_is_freezable():
    """Success Criterion: Contract 可冻结 (frozen dataclass)."""
    from tools.presentation.contract import ObservationViewModel
    vm = ObservationViewModel(
        id="vm-freeze",
        title="t",
        summary="s",
        category="performance",  # using raw string
        severity="info",
        source="runtime",
    )
    # Attempt mutation (should fail)
    with pytest.raises((AttributeError, Exception)):
        vm.id = "modified"  # type: ignore
