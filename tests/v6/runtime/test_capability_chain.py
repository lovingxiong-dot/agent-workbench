"""tests/v6/runtime/test_capability_chain.py — Capability Chain 序列化契约测试。"""
from __future__ import annotations

from agent_workbench.runtime.capability import CapabilityChain, CapabilityStep


def test_capability_step_creation():
    step = CapabilityStep(
        capability_id="coding.python.debugging",
        engine_capability="code_generation",
    )
    assert step.capability_id == "coding.python.debugging"
    assert step.engine_capability == "code_generation"
    assert step.payload_overrides == {}
    assert step.persona == {}


def test_capability_step_serialization_roundtrip():
    original = CapabilityStep(
        capability_id="coding.python.testing",
        engine_capability="code_generation",
        payload_overrides={"path": "/src"},
        persona={"role": "tester"},
    )
    data = original.to_dict()
    restored = CapabilityStep.from_dict(data)

    assert restored.capability_id == original.capability_id
    assert restored.engine_capability == original.engine_capability
    assert restored.payload_overrides == original.payload_overrides
    assert restored.persona == original.persona


def test_capability_chain_to_metadata():
    chain = [
        CapabilityStep(capability_id="analyze", engine_capability="text_generation"),
        CapabilityStep(capability_id="coding.python.debugging", engine_capability="code_generation"),
    ]
    metadata = CapabilityChain.to_metadata(chain)

    assert "capability_chain" in metadata
    assert len(metadata["capability_chain"]) == 2
    assert metadata["capability_chain"][0]["capability_id"] == "analyze"
    assert metadata["capability_chain"][1]["capability_id"] == "coding.python.debugging"


def test_capability_chain_from_metadata():
    metadata = {
        "capability_chain": [
            {"capability_id": "analyze", "engine_capability": "text_generation"},
            {"capability_id": "coding.python.debugging", "engine_capability": "code_generation"},
        ],
    }
    chain = CapabilityChain.from_metadata(metadata)

    assert chain is not None
    assert len(chain) == 2
    assert chain[0].capability_id == "analyze"
    assert chain[1].capability_id == "coding.python.debugging"


def test_capability_chain_from_empty_metadata_returns_none():
    assert CapabilityChain.from_metadata({}) is None
    assert CapabilityChain.from_metadata({"capability_chain": []}) is None


def test_capability_chain_roundtrip():
    original = [
        CapabilityStep(
            capability_id="coding.python.debugging",
            engine_capability="code_generation",
            payload_overrides={"file": "main.py"},
        ),
    ]
    metadata = CapabilityChain.to_metadata(original)
    restored = CapabilityChain.from_metadata(metadata)

    assert restored is not None
    assert len(restored) == 1
    assert restored[0].capability_id == original[0].capability_id
    assert restored[0].engine_capability == original[0].engine_capability
    assert restored[0].payload_overrides == original[0].payload_overrides


def test_capability_chain_invalid_type_returns_none():
    """非列表类型的 capability_chain 应安全返回 None，不抛异常。"""
    assert CapabilityChain.from_metadata({"capability_chain": "not-a-list"}) is None
