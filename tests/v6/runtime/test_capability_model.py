"""tests/v6/runtime/test_capability_model.py — Capability Model 契约测试。"""
from __future__ import annotations

from agent_workbench.runtime.capability import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityIntent,
    CapabilityMatch,
    CapabilityMode,
    CapabilityPersona,
)


def test_capability_definition_creation():
    definition = CapabilityDefinition(id="coding.python.debugging")
    assert definition.id == "coding.python.debugging"
    assert definition.name == ""
    assert definition.engine_capability == ""
    assert definition.parent_id is None


def test_capability_definition_full_fields():
    persona = CapabilityPersona(role="python_expert", style="concise")
    definition = CapabilityDefinition(
        id="coding.python.debugging",
        name="Python Debugging",
        summary="Debug Python code.",
        description="Debug Python code.",
        category=CapabilityCategory.CODE,
        version="1.1.0",
        provider_type="llm",
        supported_modes=[CapabilityMode.ACTION],
        priority=10,
        providers=["echo"],
        engine_capability="code_generation",
        parent_id="coding.python",
        keywords=["debug", "python"],
        persona=persona,
    )
    assert definition.name == "Python Debugging"
    assert definition.summary == "Debug Python code."
    assert definition.category == CapabilityCategory.CODE
    assert definition.version == "1.1.0"
    assert definition.provider_type == "llm"
    assert definition.supported_modes == [CapabilityMode.ACTION]
    assert definition.priority == 10
    assert definition.engine_capability == "code_generation"
    assert definition.parent_id == "coding.python"
    assert definition.keywords == ["debug", "python"]
    assert definition.persona is not None
    assert definition.persona.role == "python_expert"


def test_capability_definition_serialization_roundtrip():
    persona = CapabilityPersona(role="expert", preferred_tools=["pytest"])
    original = CapabilityDefinition(
        id="coding.python.testing",
        name="Python Testing",
        summary="Run Python tests.",
        category=CapabilityCategory.CODE,
        provider_type="llm",
        supported_modes=[CapabilityMode.ACTION],
        priority=5,
        engine_capability="code_generation",
        parent_id="coding.python",
        keywords=["test"],
        persona=persona,
    )
    data = original.to_dict()
    restored = CapabilityDefinition.from_dict(data)

    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.summary == original.summary
    assert restored.category == original.category
    assert restored.provider_type == original.provider_type
    assert restored.supported_modes == original.supported_modes
    assert restored.priority == original.priority
    assert restored.engine_capability == original.engine_capability
    assert restored.parent_id == original.parent_id
    assert restored.keywords == original.keywords
    assert restored.persona is not None
    assert restored.persona.role == "expert"
    assert restored.persona.preferred_tools == ["pytest"]


def test_capability_definition_default_isolation():
    """默认可变字段应隔离，避免实例间互相污染。"""
    definition1 = CapabilityDefinition(id="a")
    definition2 = CapabilityDefinition(id="b")

    definition1.providers.append("p1")
    definition1.keywords.append("k1")

    assert definition1.providers == ["p1"]
    assert definition1.keywords == ["k1"]
    assert definition2.providers == []
    assert definition2.keywords == []


def test_capability_persona_default_isolation():
    persona1 = CapabilityPersona()
    persona2 = CapabilityPersona()
    persona1.preferred_tools.append("tool_a")
    assert persona1.preferred_tools == ["tool_a"]
    assert persona2.preferred_tools == []


def test_capability_match_creation():
    definition = CapabilityDefinition(id="chat")
    match = CapabilityMatch(definition=definition, score=0.95, lineage=["assistant", "chat"])
    assert match.definition.id == "chat"
    assert match.score == 0.95
    assert match.lineage == ["assistant", "chat"]


def test_capability_intent_creation():
    intent = CapabilityIntent(
        text="fix this bug",
        metadata={"session_id": "s1"},
        required_permissions=["code.read"],
        preferred_providers=["deepseek"],
    )
    assert intent.text == "fix this bug"
    assert intent.metadata == {"session_id": "s1"}
    assert intent.required_permissions == ["code.read"]
    assert intent.preferred_providers == ["deepseek"]


def test_capability_intent_serialization_roundtrip():
    original = CapabilityIntent(
        text="analyze project",
        metadata={"path": "/tmp"},
        required_permissions=["file.read"],
    )
    data = original.to_dict()
    restored = CapabilityIntent.from_dict(data)
    assert restored.text == original.text
    assert restored.metadata == original.metadata
    assert restored.required_permissions == original.required_permissions
    assert restored.preferred_providers == original.preferred_providers
