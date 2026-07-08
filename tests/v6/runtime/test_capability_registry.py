"""tests/v6/runtime/test_capability_registry.py — Capability Tree 核心测试。"""
from __future__ import annotations

import pytest

from agent_workbench.runtime.capability import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityIntent,
    CapabilityMode,
)
from agent_workbench.runtime.capability.graph import CapabilityRegistry


def test_register_and_get():
    registry = CapabilityRegistry()
    definition = CapabilityDefinition(id="chat", engine_capability="text_generation")
    registry.register(definition)

    assert registry.get("chat") is definition
    assert registry.get("missing") is None


def test_default_graph_has_roots():
    registry = CapabilityRegistry()
    registry.load_defaults()

    roots = registry.roots()
    assert len(roots) == 1
    assert roots[0].id == "assistant"


def test_lineage_from_leaf_to_root():
    registry = CapabilityRegistry()
    registry.load_defaults()

    lineage = registry.lineage("coding.python.debugging")
    assert lineage == ["assistant", "coding", "coding.python", "coding.python.debugging"]


def test_children_query():
    registry = CapabilityRegistry()
    registry.load_defaults()

    assistant_children = [child.id for child in registry.children("assistant")]
    assert set(assistant_children) == {"chat", "analyze", "tool", "coding", "image_generation"}

    coding_children = [child.id for child in registry.children("coding")]
    assert set(coding_children) == {"coding.python", "coding.code_editor"}

    missing_children = registry.children("missing")
    assert missing_children == []


def test_register_out_of_order_links_parent():
    """即使先注册子节点再注册父节点，父子关系也应正确建立。"""
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(id="child", parent_id="parent"))
    registry.register(CapabilityDefinition(id="parent"))

    parent_node = registry.get("parent")
    child_node = registry.get("child")
    assert parent_node is not None
    assert child_node is not None
    assert child_node.parent_id == "parent"
    assert [child.id for child in registry.children("parent")] == ["child"]
    assert registry.lineage("child") == ["parent", "child"]


def test_default_graph_leaf_has_engine_capability():
    registry = CapabilityRegistry()
    registry.load_defaults()

    debugging = registry.get("coding.python.debugging")
    assert debugging is not None
    assert debugging.engine_capability == "code_generation"


def test_find_by_keyword():
    registry = CapabilityRegistry()
    registry.load_defaults()

    # 使用不命中父节点 "coding.python" 关键词的查询，确保命中叶子节点。
    matches = registry.find(CapabilityIntent(text="fix this bug"))
    assert len(matches) >= 1
    assert matches[0].definition.id == "coding.python.debugging"
    assert "bug" in matches[0].definition.keywords


def test_find_respects_permissions():
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            id="restricted",
            keywords=["secret"],
            permissions=["admin"],
        )
    )
    registry.register(
        CapabilityDefinition(
            id="public",
            keywords=["secret"],
            permissions=[],
        )
    )

    matches = registry.find(CapabilityIntent(text="secret", required_permissions=["admin"]))
    assert len(matches) == 1
    assert matches[0].definition.id == "restricted"


def test_find_respects_preferred_providers():
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            id="with_provider",
            keywords=["hello"],
            providers=["deepseek"],
        )
    )
    registry.register(
        CapabilityDefinition(
            id="without_provider",
            keywords=["hello"],
            providers=[],
        )
    )

    matches = registry.find(CapabilityIntent(text="hello", preferred_providers=["deepseek"]))
    assert len(matches) == 1
    assert matches[0].definition.id == "with_provider"


def test_resolve_returns_best_match():
    registry = CapabilityRegistry()
    registry.load_defaults()

    match = registry.resolve(CapabilityIntent(text="fix this bug"))
    assert match.definition.id == "coding.python.debugging"
    assert match.score > 0


def test_resolve_fallback_to_chat_for_unknown_input():
    registry = CapabilityRegistry()
    registry.load_defaults()

    match = registry.resolve(CapabilityIntent(text="something completely unrelated"))
    assert match.definition.id == "chat"
    assert match.score == 0.0


def test_default_graph_has_runtime_contract_fields():
    registry = CapabilityRegistry()
    registry.load_defaults()

    chat = registry.get("chat")
    assert chat is not None
    assert chat.category == CapabilityCategory.TEXT
    assert chat.provider_type == "llm"
    assert chat.supported_modes == [CapabilityMode.CHAT]

    image = registry.get("image_generation")
    assert image is not None
    assert image.category == CapabilityCategory.IMAGE
    assert image.provider_type == "llm"
    assert image.supported_modes == [CapabilityMode.ACTION]

    tool = registry.get("tool")
    assert tool is not None
    assert tool.category == CapabilityCategory.TOOL
    assert tool.provider_type == "tool"


def test_persona_serialization():
    from agent_workbench.runtime.capability import CapabilityPersona

    persona = CapabilityPersona(role="tester", preferred_tools=["pytest"])
    data = persona.to_dict()
    restored = CapabilityPersona.from_dict(data)
    assert restored.role == "tester"
    assert restored.preferred_tools == ["pytest"]
