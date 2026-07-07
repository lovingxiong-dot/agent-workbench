"""tests/v6/test_v6_capability_registry.py — Engine Capability Registry 测试。"""
from __future__ import annotations

import pytest

from v6.runtime.capability_registry import CapabilityQuery, CapabilityRegistry
from v6.runtime.engine_manager import EngineManager
from v6.runtime.engines import (
    CodeEngine,
    KnowledgeEngine,
    LLMEngine,
    MemoryEngine,
    PlannerEngine,
    ToolEngine,
    VisionEngine,
    WorkflowEngine,
)


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    manager = EngineManager(capability_registry=registry)
    manager.register(LLMEngine())
    manager.register(ToolEngine())
    manager.register(MemoryEngine())
    manager.register(PlannerEngine())
    manager.register(CodeEngine())
    manager.register(VisionEngine())
    manager.register(KnowledgeEngine())
    manager.register(WorkflowEngine())
    return registry


def test_registry_lists_all_capabilities() -> None:
    registry = build_registry()
    caps = registry.capabilities()
    assert "text_generation" in caps
    assert "tool_execution" in caps
    assert "memory_retrieval" in caps
    assert "orchestration" in caps


def test_names_for_capability() -> None:
    registry = build_registry()
    names = registry.names_for("text_generation")
    assert names == ["llm"]


def test_find_returns_matches_sorted_by_score() -> None:
    registry = build_registry()
    query = CapabilityQuery(capability="text_generation")
    matches = registry.find(query)
    assert len(matches) == 1
    assert matches[0].name == "llm"
    assert matches[0].score > 0


def test_select_returns_best_match() -> None:
    registry = build_registry()
    name = registry.select(CapabilityQuery(capability="tool_execution"))
    assert name == "tool"


def test_select_returns_none_for_unknown_capability() -> None:
    registry = build_registry()
    name = registry.select(CapabilityQuery(capability="unknown"))
    assert name is None


def test_query_from_dict() -> None:
    query = CapabilityQuery.from_dict(
        {
            "capability": "text_generation",
            "priority": "high",
            "streaming": True,
            "metadata": {"provider": "openai"},
        }
    )
    assert query.capability == "text_generation"
    assert query.priority == "high"
    assert query.streaming is True
    assert query.metadata == {"provider": "openai"}


def test_metadata_filter_excludes_non_matching() -> None:
    registry = CapabilityRegistry()
    from v6.runtime.engines.protocol import EngineDescriptor

    registry.register(
        EngineDescriptor(name="gpt4", capabilities=["text_generation"], metadata={"provider": "openai"})
    )
    registry.register(
        EngineDescriptor(name="claude", capabilities=["text_generation"], metadata={"provider": "anthropic"})
    )

    matches = registry.find(
        CapabilityQuery(capability="text_generation", metadata={"provider": "openai"})
    )
    assert len(matches) == 1
    assert matches[0].name == "gpt4"


def test_engine_manager_exposes_capabilities() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())
    manager.register(ToolEngine())

    assert "text_generation" in manager.capabilities()
    assert "tool_execution" in manager.capabilities()


def test_engine_manager_select_engine_by_dict() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())
    manager.register(ToolEngine())

    name = manager.select_engine({"capability": "text_generation"})
    assert name == "llm"


def test_engine_manager_find_engines_returns_sorted_names() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())
    manager.register(ToolEngine())
    manager.register(MemoryEngine())

    names = manager.find_engines({"capability": "memory_retrieval"})
    assert names == ["memory"]


def test_engine_manager_descriptor_includes_capabilities() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())

    desc = manager.descriptor("llm")
    assert desc is not None
    assert "text_generation" in desc.capabilities


def test_unregister_removes_from_registry() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())
    assert "text_generation" in manager.capabilities()

    manager.unregister("llm")
    assert "text_generation" not in manager.capabilities()


def test_clear_removes_all_capabilities() -> None:
    manager = EngineManager()
    manager.register(LLMEngine())
    manager.register(ToolEngine())
    manager.clear()
    assert manager.capabilities() == []
