"""tests/skill/test_skill.py — Skill System 测试。

v6.10.0-alpha Skill System Foundation。

边界：
  - Skill 数据模型 / Adapter / Registry 测试
  - 不发起 Runtime 调用
  - Skill 不进入 Runtime Kernel
"""
from __future__ import annotations

from typing import List

import pytest

from agent_workbench.presentation.adapters.skill_adapter import SkillAdapter
from agent_workbench.presentation.services.skill_service import (
    AddSkillResult,
    RemoveSkillResult,
    RuntimeCapabilityLookup,
    SkillConfigBackend,
    WorkbenchSkillRegistry,
)
from agent_workbench.presentation.view_models.skill import (
    SkillCompositionResult,
    SkillListViewModel,
    SkillViewModel,
)


class MockConfigStore:
    def __init__(self, initial: dict | None = None) -> None:
        self._data: dict = initial or {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value


class MockCapabilityLookup:
    def __init__(self, capability_ids: List[str] | None = None, tool_ids: List[str] | None = None) -> None:
        self._cap = set(capability_ids or [])
        self._tools = set(tool_ids or [])

    def list_capability_ids(self) -> List[str]:
        return sorted(self._cap)

    def list_tool_ids(self) -> List[str]:
        return sorted(self._tools)


def make_registry(
    skills: list[dict] | None = None,
    capability_ids: List[str] | None = None,
    tool_ids: List[str] | None = None,
) -> WorkbenchSkillRegistry:
    """工厂：构造 WorkbenchSkillRegistry。"""
    store = MockConfigStore({"skill.registry": skills or []})
    config_backend = SkillConfigBackend(store)
    lookup = MockCapabilityLookup(capability_ids, tool_ids)
    return WorkbenchSkillRegistry(config_backend, lookup)


class TestSkillViewModel:
    """SkillViewModel 测试。"""

    def test_default_values(self) -> None:
        vm = SkillViewModel(skill_id="s1", name="Skill 1")
        assert vm.skill_id == "s1"
        assert vm.name == "Skill 1"
        assert vm.version == "1.0.0"
        assert vm.capabilities == []
        assert vm.tools == []
        assert vm.prompt == ""
        assert vm.metadata == {}

    def test_none_lists_become_empty(self) -> None:
        vm = SkillViewModel(
            skill_id="s2", name="S", capabilities=None, tools=None, metadata=None
        )
        assert vm.capabilities == []
        assert vm.tools == []
        assert vm.metadata == {}


class TestSkillAdapter:
    """SkillAdapter 测试。"""

    def test_to_view_model(self) -> None:
        adapter = SkillAdapter()
        skill_dict = {
            "id": "code_review",
            "name": "Code Review",
            "description": "Reviews Python code",
            "version": "2.0.0",
            "capabilities": ["code_analysis", "lint"],
            "tools": ["pylint"],
            "prompt": "Review code carefully",
            "metadata": {"author": "test"},
        }
        vm = adapter.to_view_model(skill_dict)
        assert vm.skill_id == "code_review"
        assert vm.capabilities == ["code_analysis", "lint"]
        assert vm.tools == ["pylint"]
        assert vm.metadata == {"author": "test"}

    def test_to_list_view_model(self) -> None:
        adapter = SkillAdapter()
        skills = [{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}]
        list_vm = adapter.to_list_view_model(skills)
        assert list_vm.total_count == 2
        assert list_vm.find_by_id("s1") is not None
        assert list_vm.find_by_id("nonexistent") is None

    def test_view_model_to_dict_roundtrip(self) -> None:
        adapter = SkillAdapter()
        vm = SkillViewModel(
            skill_id="s1",
            name="S1",
            capabilities=["c1"],
            tools=["t1"],
            prompt="p",
            metadata={"k": "v"},
        )
        d = adapter.view_model_to_dict(vm)
        assert d["id"] == "s1"
        assert d["capabilities"] == ["c1"]
        assert d["tools"] == ["t1"]

        # roundtrip
        vm2 = adapter.to_view_model(d)
        assert vm2.skill_id == vm.skill_id
        assert vm2.capabilities == vm.capabilities


class TestSkillConfigBackend:
    """SkillConfigBackend 测试。"""

    def test_list_empty(self) -> None:
        store = MockConfigStore()
        backend = SkillConfigBackend(store)
        assert backend.list_skill_dicts() == []

    def test_upsert_new(self) -> None:
        store = MockConfigStore()
        backend = SkillConfigBackend(store)
        backend.upsert_skill({"id": "s1", "name": "S1"})
        assert len(backend.list_skill_dicts()) == 1

    def test_upsert_existing(self) -> None:
        store = MockConfigStore({"skill.registry": [{"id": "s1", "name": "old"}]})
        backend = SkillConfigBackend(store)
        backend.upsert_skill({"id": "s1", "name": "new"})
        skills = backend.list_skill_dicts()
        assert len(skills) == 1
        assert skills[0]["name"] == "new"

    def test_remove_existing(self) -> None:
        store = MockConfigStore({"skill.registry": [{"id": "s1"}, {"id": "s2"}]})
        backend = SkillConfigBackend(store)
        backend.remove_skill("s1")
        skills = backend.list_skill_dicts()
        assert len(skills) == 1
        assert skills[0]["id"] == "s2"

    def test_remove_nonexistent(self) -> None:
        store = MockConfigStore({"skill.registry": []})
        backend = SkillConfigBackend(store)
        backend.remove_skill("nonexistent")
        assert backend.list_skill_dicts() == []


class TestWorkbenchSkillRegistry:
    """WorkbenchSkillRegistry 测试。"""

    def test_list_empty(self) -> None:
        registry = make_registry()
        assert registry.list_view_model().total_count == 0

    def test_list_with_skills(self) -> None:
        registry = make_registry([
            {"id": "s1", "name": "S1"},
            {"id": "s2", "name": "S2"},
        ])
        assert registry.list_view_model().total_count == 2

    def test_get_view_model_existing(self) -> None:
        registry = make_registry([{"id": "s1", "name": "S1"}])
        vm = registry.get_view_model("s1")
        assert vm is not None
        assert vm.skill_id == "s1"

    def test_get_view_model_missing(self) -> None:
        registry = make_registry()
        assert registry.get_view_model("nonexistent") is None

    def test_add_skill(self) -> None:
        registry = make_registry()
        vm = SkillViewModel(skill_id="s1", name="S1")
        result = registry.add_skill(vm)
        assert result.success is True
        assert registry.get_view_model("s1") is not None

    def test_add_skill_empty_id(self) -> None:
        registry = make_registry()
        vm = SkillViewModel(skill_id="", name="S")
        result = registry.add_skill(vm)
        assert result.success is False

    def test_add_skill_empty_name(self) -> None:
        registry = make_registry()
        vm = SkillViewModel(skill_id="s1", name="")
        result = registry.add_skill(vm)
        assert result.success is False

    def test_remove_skill(self) -> None:
        registry = make_registry([{"id": "s1", "name": "S1"}])
        result = registry.remove_skill("s1")
        assert result.success is True
        assert registry.get_view_model("s1") is None

    def test_remove_skill_missing(self) -> None:
        registry = make_registry()
        result = registry.remove_skill("nonexistent")
        assert result.success is False


class TestSkillComposition:
    """Skill Composition 验证测试（关键 — Skill 不进入 Runtime）。"""

    def test_complete_composition(self) -> None:
        registry = make_registry(
            skills=[
                {
                    "id": "code_review",
                    "name": "Code Review",
                    "capabilities": ["code_analysis", "lint"],
                    "tools": ["pylint"],
                }
            ],
            capability_ids=["code_analysis", "lint", "other"],
            tool_ids=["pylint", "black"],
        )
        result = registry.verify_composition("code_review")
        assert result is not None
        assert result.is_complete is True
        assert result.missing_capabilities == []
        assert result.missing_tools == []

    def test_incomplete_capabilities(self) -> None:
        registry = make_registry(
            skills=[
                {
                    "id": "code_review",
                    "name": "Code Review",
                    "capabilities": ["code_analysis", "lint", "formatting"],
                    "tools": ["pylint"],
                }
            ],
            capability_ids=["code_analysis"],
            tool_ids=["pylint"],
        )
        result = registry.verify_composition("code_review")
        assert result is not None
        assert result.is_complete is False
        assert "lint" in result.missing_capabilities
        assert "formatting" in result.missing_capabilities

    def test_incomplete_tools(self) -> None:
        registry = make_registry(
            skills=[
                {
                    "id": "s",
                    "name": "S",
                    "capabilities": ["c"],
                    "tools": ["t1", "t2"],
                }
            ],
            capability_ids=["c"],
            tool_ids=["t1"],
        )
        result = registry.verify_composition("s")
        assert result is not None
        assert "t2" in result.missing_tools

    def test_verify_missing_skill(self) -> None:
        registry = make_registry()
        assert registry.verify_composition("nonexistent") is None