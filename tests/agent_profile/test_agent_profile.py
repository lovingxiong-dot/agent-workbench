"""tests/agent_profile/test_agent_profile.py — AgentProfile 测试。

v6.10.0-alpha Agent Configuration Layer。

边界：
  - Agent Profile 数据模型 / Registry 测试
  - 不发起 Runtime 调用
  - Agent Profile 不进入 Runtime
"""
from __future__ import annotations

from typing import Set

import pytest

from agent_workbench.presentation.services.agent_profile_service import (
    AgentConfigBackend,
    RuntimeEntityLookup,
    WorkbenchAgentProfileRegistry,
)
from agent_workbench.presentation.view_models.agent_profile import (
    AgentIdentityView,
    AgentPolicyView,
    AgentProfile,
    AgentProfileListViewModel,
)


class MockConfigStore:
    def __init__(self, initial: dict | None = None) -> None:
        self._data: dict = initial or {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value


class MockEntityLookup:
    """Mock RuntimeEntityLookup（满足 RuntimeEntityLookup Protocol）。"""

    def __init__(
        self,
        providers: set[str] | None = None,
        skills: set[str] | None = None,
        tools: set[str] | None = None,
    ) -> None:
        self._providers = providers or set()
        self._skills = skills or set()
        self._tools = tools or set()

    def provider_exists(self, provider_id: str) -> bool:
        return provider_id in self._providers

    def skill_exists(self, skill_id: str) -> bool:
        return skill_id in self._skills

    def tool_exists(self, tool_id: str) -> bool:
        return tool_id in self._tools


def make_profile(
    agent_id: str = "personal_agent",
    name: str = "Personal Assistant",
    provider_id: str = "openai",
    skills: list[str] | None = None,
    tools: list[str] | None = None,
    policy: AgentPolicyView | None = None,
) -> AgentProfile:
    """工厂：构造 AgentProfile。"""
    return AgentProfile(
        identity=AgentIdentityView(agent_id=agent_id, name=name),
        provider_id=provider_id,
        skills=skills or [],
        tools=tools or [],
        policy=policy or AgentPolicyView(),
    )


def make_registry(
    agents: list[dict] | None = None,
    active: str | None = None,
    providers: set[str] | None = None,
    skills: set[str] | None = None,
    tools: set[str] | None = None,
) -> WorkbenchAgentProfileRegistry:
    """工厂：构造 WorkbenchAgentProfileRegistry。"""
    store = MockConfigStore({"agent.profiles": agents or []})
    if active is not None:
        store.set("agent.active", active)
    backend = AgentConfigBackend(store)
    lookup = MockEntityLookup(providers, skills, tools)
    return WorkbenchAgentProfileRegistry(backend, lookup)


class TestAgentIdentityView:
    """AgentIdentityView 测试。"""

    def test_default_values(self) -> None:
        identity = AgentIdentityView(agent_id="a", name="A")
        assert identity.agent_id == "a"
        assert identity.version == "1.0.0"
        assert identity.metadata == {}

    def test_none_metadata_becomes_empty(self) -> None:
        identity = AgentIdentityView(agent_id="a", name="A", metadata=None)
        assert identity.metadata == {}


class TestAgentPolicyView:
    """AgentPolicyView 测试。"""

    def test_default_policy(self) -> None:
        policy = AgentPolicyView()
        assert policy.require_provider is True
        assert policy.require_skills is False
        assert policy.max_concurrent_tasks == 1
        assert policy.custom_rules == {}

    def test_custom_rules_default_empty(self) -> None:
        policy = AgentPolicyView(custom_rules=None)
        assert policy.custom_rules == {}


class TestAgentProfile:
    """AgentProfile 测试。"""

    def test_default_lists(self) -> None:
        profile = AgentProfile(identity=AgentIdentityView(agent_id="a", name="A"))
        assert profile.skills == []
        assert profile.tools == []
        assert profile.metadata == {}


class TestAgentConfigBackend:
    """AgentConfigBackend 测试。"""

    def test_list_empty(self) -> None:
        store = MockConfigStore()
        backend = AgentConfigBackend(store)
        assert backend.list_agent_dicts() == []

    def test_upsert_new(self) -> None:
        store = MockConfigStore()
        backend = AgentConfigBackend(store)
        backend.upsert_agent({"agent_id": "a", "name": "A"})
        assert len(backend.list_agent_dicts()) == 1

    def test_upsert_existing(self) -> None:
        store = MockConfigStore({"agent.profiles": [{"agent_id": "a", "name": "old"}]})
        backend = AgentConfigBackend(store)
        backend.upsert_agent({"agent_id": "a", "name": "new"})
        agents = backend.list_agent_dicts()
        assert len(agents) == 1
        assert agents[0]["name"] == "new"

    def test_remove(self) -> None:
        store = MockConfigStore({"agent.profiles": [{"agent_id": "a"}, {"agent_id": "b"}]})
        backend = AgentConfigBackend(store)
        backend.remove_agent("a")
        agents = backend.list_agent_dicts()
        assert len(agents) == 1
        assert agents[0]["agent_id"] == "b"

    def test_active(self) -> None:
        store = MockConfigStore()
        backend = AgentConfigBackend(store)
        backend.set_active_agent("a")
        assert backend.get_active_agent_id() == "a"


class TestWorkbenchAgentProfileRegistryCreate:
    """Agent 创建测试（Create Agent without code modification）。"""

    def test_create_success(self) -> None:
        registry = make_registry(providers={"openai"})
        profile = make_profile(agent_id="p1", provider_id="openai")
        result = registry.create_agent(profile)
        assert result.success is True
        assert result.agent_id == "p1"
        assert registry.get_profile("p1") is not None

    def test_create_with_skills_and_tools(self) -> None:
        registry = make_registry(
            providers={"openai"},
            skills={"code_review"},
            tools={"pylint"},
        )
        profile = make_profile(
            agent_id="dev",
            provider_id="openai",
            skills=["code_review"],
            tools=["pylint"],
        )
        result = registry.create_agent(profile)
        assert result.success is True

    def test_create_empty_agent_id(self) -> None:
        registry = make_registry()
        profile = AgentProfile(identity=AgentIdentityView(agent_id="", name="A"))
        result = registry.create_agent(profile)
        assert result.success is False

    def test_create_empty_name(self) -> None:
        registry = make_registry()
        profile = AgentProfile(identity=AgentIdentityView(agent_id="a", name=""))
        result = registry.create_agent(profile)
        assert result.success is False

    def test_create_missing_provider(self) -> None:
        registry = make_registry()  # no providers
        profile = make_profile(agent_id="a", provider_id="missing")
        result = registry.create_agent(profile)
        assert result.success is False
        assert "provider" in result.error

    def test_create_missing_skill(self) -> None:
        registry = make_registry(providers={"openai"}, skills=set())
        profile = make_profile(agent_id="a", provider_id="openai", skills=["missing"])
        result = registry.create_agent(profile)
        assert result.success is False
        assert "skill" in result.error

    def test_create_missing_tool(self) -> None:
        registry = make_registry(
            providers={"openai"}, skills={"s1"}, tools=set()
        )
        profile = make_profile(
            agent_id="a", provider_id="openai", skills=["s1"], tools=["missing"]
        )
        result = registry.create_agent(profile)
        assert result.success is False
        assert "tool" in result.error

    def test_create_policy_violation(self) -> None:
        registry = make_registry()  # no providers
        # policy.require_provider=True (default) + no provider
        profile = AgentProfile(
            identity=AgentIdentityView(agent_id="a", name="A"),
            policy=AgentPolicyView(require_provider=True),
        )
        result = registry.create_agent(profile)
        assert result.success is False
        assert "policy" in result.error or "provider" in result.error


class TestWorkbenchAgentProfileRegistryDelete:
    """Agent 删除测试。"""

    def test_delete_success(self) -> None:
        registry = make_registry(
            agents=[{"agent_id": "a", "name": "A"}],
            providers={"openai"},
        )
        result = registry.delete_agent("a")
        assert result.success is True
        assert registry.get_profile("a") is None

    def test_delete_missing(self) -> None:
        registry = make_registry()
        result = registry.delete_agent("nonexistent")
        assert result.success is False


class TestWorkbenchAgentProfileRegistryList:
    """Agent 列表测试。"""

    def test_list_empty(self) -> None:
        registry = make_registry()
        list_vm = registry.list_view_model()
        assert list_vm.total_count == 0

    def test_list_with_agents(self) -> None:
        agents = [
            {"agent_id": "a", "name": "A"},
            {"agent_id": "b", "name": "B"},
        ]
        registry = make_registry(agents=agents, active="a")
        list_vm = registry.list_view_model()
        assert list_vm.total_count == 2
        active = list_vm.get_active()
        assert active is not None
        assert active.identity.agent_id == "a"

    def test_get_profile(self) -> None:
        agents = [{"agent_id": "a", "name": "A"}]
        registry = make_registry(agents=agents)
        profile = registry.get_profile("a")
        assert profile is not None
        assert profile.identity.name == "A"

    def test_get_profile_missing(self) -> None:
        registry = make_registry()
        assert registry.get_profile("nonexistent") is None


class TestActivateAgent:
    """Agent 激活测试。"""

    def test_activate_existing(self) -> None:
        agents = [{"agent_id": "a", "name": "A"}]
        registry = make_registry(agents=agents)
        ok = registry.activate_agent("a")
        assert ok is True

    def test_activate_missing(self) -> None:
        registry = make_registry()
        assert registry.activate_agent("nonexistent") is False


class TestProfileDictRoundtrip:
    """Profile <-> Dict 序列化测试。"""

    def test_roundtrip_preserves_all_fields(self) -> None:
        registry = make_registry(
            providers={"openai"},
            skills={"s1"},
            tools={"t1"},
        )
        original = AgentProfile(
            identity=AgentIdentityView(
                agent_id="p1", name="P1", description="desc", avatar="🤖", version="2.0.0",
                metadata={"k": "v"},
            ),
            provider_id="openai",
            skills=["s1"],
            tools=["t1"],
            policy=AgentPolicyView(
                require_provider=False,
                require_skills=True,
                max_concurrent_tasks=3,
                custom_rules={"r": "v"},
            ),
            metadata={"profile_meta": "v"},
        )
        result = registry.create_agent(original)
        assert result.success is True

        loaded = registry.get_profile("p1")
        assert loaded is not None
        assert loaded.identity.agent_id == "p1"
        assert loaded.identity.description == "desc"
        assert loaded.identity.avatar == "🤖"
        assert loaded.identity.version == "2.0.0"
        assert loaded.identity.metadata == {"k": "v"}
        assert loaded.provider_id == "openai"
        assert loaded.skills == ["s1"]
        assert loaded.tools == ["t1"]
        assert loaded.policy.require_provider is False
        assert loaded.policy.require_skills is True
        assert loaded.policy.max_concurrent_tasks == 3
        assert loaded.policy.custom_rules == {"r": "v"}
        assert loaded.metadata == {"profile_meta": "v"}