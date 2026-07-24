"""tests/product_shell/test_product_shell.py — Product Shell 集成测试。

v6.10.0-alpha Product Shell Integration。

边界：
  - 测试 Phase 1-4 Service Controllers 聚合
  - UI configuration flow 验证（左侧/右侧/中央）
  - 使用 Mock ConfigStore + Mock Runtime Backends
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.services.product_shell import (
    ShellSnapshot,
    WorkbenchProductShell,
    build_product_shell,
)
from agent_workbench.presentation.view_models.agent_profile import (
    AgentIdentityView,
    AgentPolicyView,
    AgentProfile,
)
from agent_workbench.presentation.view_models.skill import SkillViewModel


class MockConfigStore:
    """Mock ConfigStore。"""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def add(self, key: str, value) -> None:
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(value)


class MockRuntimeProviderBackend:
    def __init__(self, providers: List[Any] | None = None, active: Optional[str] = None) -> None:
        self._providers = providers or []
        self._active = active

    def list_provider_names(self) -> List[str]:
        return [p.provider_id for p in self._providers]

    def list_provider_infos(self) -> List[Any]:
        return list(self._providers)

    def get_active_provider_name(self) -> Optional[str]:
        return self._active

    def switch_provider(self, provider_name: str) -> bool:
        if provider_name not in self.list_provider_names():
            return False
        self._active = provider_name
        return True


class MockRuntimeToolBackend:
    def __init__(self, tools: List[Dict[str, Any]] | None = None) -> None:
        self._tools = {t["name"]: dict(t) for t in (tools or [])}

    def list_tool_dicts(self) -> List[Dict[str, Any]]:
        return [dict(t) for t in self._tools.values()]

    def set_tool_enabled(self, tool_id: str, enabled: bool) -> bool:
        if tool_id not in self._tools:
            return False
        self._tools[tool_id]["enabled"] = enabled
        return True

    def set_tool_config(self, tool_id: str, config: Dict[str, Any]) -> bool:
        if tool_id not in self._tools:
            return False
        self._tools[tool_id].update(config)
        return True


class MockCapabilityBackend:
    def __init__(self, ids: List[str] | None = None) -> None:
        self._ids = set(ids or [])

    def list_capability_ids(self) -> List[str]:
        return sorted(self._ids)


class MockToolIdsBackend:
    def __init__(self, tool_ids: List[str] | None = None) -> None:
        self._ids = set(tool_ids or [])

    def list_tool_ids(self) -> List[str]:
        return sorted(self._ids)


@pytest.fixture
def shell() -> WorkbenchProductShell:
    """标准 Product Shell fixture。"""
    return build_product_shell(
        config_store=MockConfigStore(),
        runtime_provider_backend=MockRuntimeProviderBackend(
            providers=[],
            active=None,
        ),
        runtime_tool_backend=MockRuntimeToolBackend(
            tools=[{"name": "echo", "enabled": True, "permission": "user"}],
        ),
        capability_registry_backend=MockCapabilityBackend(
            ids=["code_analysis", "lint"],
        ),
        tool_ids_backend=MockToolIdsBackend(tool_ids=["echo"]),
    )


class TestProductShellSnapshot:
    """ShellSnapshot 测试。"""

    def test_empty_snapshot(self, shell: WorkbenchProductShell) -> None:
        snap = shell.snapshot()
        assert snap.providers == []
        assert snap.tools != []  # echo tool exists
        assert snap.skills == []
        assert snap.agents == []
        assert snap.active_provider_id is None
        assert snap.active_agent_id is None

    def test_snapshot_with_data(self, shell: WorkbenchProductShell) -> None:
        # Add provider
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk-test",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)

        # Add skill
        skill = SkillViewModel(
            skill_id="code_review",
            name="Code Review",
            capabilities=["code_analysis"],
            tools=["echo"],
        )
        shell.add_skill(skill)

        # Add agent
        agent = AgentProfile(
            identity=AgentIdentityView(agent_id="p1", name="P1"),
            provider_id="openai",
            skills=["code_review"],
            tools=["echo"],
        )
        shell.create_agent(agent)

        snap = shell.snapshot()
        assert len(snap.providers) == 1
        assert len(snap.tools) >= 1
        assert len(snap.skills) == 1
        assert len(snap.agents) == 1


class TestProductShellProviderOperations:
    """Provider 操作测试。"""

    def test_add_provider(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        result = shell.add_provider(endpoint)
        assert result.success is True

    def test_remove_provider(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)
        result = shell.remove_provider("openai")
        assert result.success is True

    def test_switch_provider(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)
        # Need to register in Runtime backend for switch to work
        # (this test just exercises the path)
        result = shell.switch_provider("openai")
        # switch will fail because no Runtime registration
        assert result.success is False


class TestProductShellToolOperations:
    """Tool 操作测试。"""

    def test_enable_tool(self, shell: WorkbenchProductShell) -> None:
        result = shell.enable_tool("echo")
        assert result.success is True

    def test_disable_tool(self, shell: WorkbenchProductShell) -> None:
        result = shell.disable_tool("echo")
        assert result.success is True

    def test_list_tool_view_models(self, shell: WorkbenchProductShell) -> None:
        tools = shell.list_tool_view_models()
        assert any(t.tool_id == "echo" for t in tools)


class TestProductShellSkillOperations:
    """Skill 操作测试。"""

    def test_add_skill(self, shell: WorkbenchProductShell) -> None:
        skill = SkillViewModel(
            skill_id="code_review",
            name="Code Review",
            capabilities=["code_analysis"],
            tools=["echo"],
        )
        result = shell.add_skill(skill)
        assert result.success is True

    def test_verify_skill_composition(self, shell: WorkbenchProductShell) -> None:
        skill = SkillViewModel(
            skill_id="code_review",
            name="Code Review",
            capabilities=["code_analysis"],
            tools=["echo"],
        )
        shell.add_skill(skill)
        result = shell.verify_skill_composition("code_review")
        assert result is not None
        assert result.is_complete is True

    def test_verify_incomplete_skill(self, shell: WorkbenchProductShell) -> None:
        skill = SkillViewModel(
            skill_id="missing_skill",
            name="Missing",
            capabilities=["non_existent_capability"],
        )
        shell.add_skill(skill)
        result = shell.verify_skill_composition("missing_skill")
        assert result is not None
        assert result.is_complete is False


class TestProductShellAgentOperations:
    """Agent 操作测试（Create Agent without code modification）。"""

    def test_create_agent(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)
        agent = AgentProfile(
            identity=AgentIdentityView(agent_id="p1", name="P1"),
            provider_id="openai",
            tools=["echo"],
        )
        result = shell.create_agent(agent)
        assert result.success is True

    def test_create_agent_invalid_provider(self, shell: WorkbenchProductShell) -> None:
        agent = AgentProfile(
            identity=AgentIdentityView(agent_id="p1", name="P1"),
            provider_id="nonexistent",
        )
        result = shell.create_agent(agent)
        assert result.success is False

    def test_activate_agent(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)
        agent = AgentProfile(
            identity=AgentIdentityView(agent_id="p1", name="P1"),
            provider_id="openai",
            tools=["echo"],
        )
        shell.create_agent(agent)
        ok = shell.activate_agent("p1")
        assert ok is True

    def test_get_active_agent(self, shell: WorkbenchProductShell) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk",
            models=["gpt-4"],
        )
        shell.add_provider(endpoint)
        agent = AgentProfile(
            identity=AgentIdentityView(agent_id="p1", name="P1"),
            provider_id="openai",
            tools=["echo"],
        )
        shell.create_agent(agent)
        shell.activate_agent("p1")
        active = shell.get_active_agent()
        assert active is not None
        assert active.identity.agent_id == "p1"


class TestProductShellUIConfigurationFlow:
    """UI configuration flow 测试（Configuration-Driven Principle P5）。"""

    def test_full_configuration_flow(self, shell: WorkbenchProductShell) -> None:
        """完整 UI 配置流程：Provider -> Skill -> Agent -> Activate。"""

        # Step 1: Add Provider
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk-test",
            models=["gpt-4", "gpt-3.5-turbo"],
        )
        r1 = shell.add_provider(endpoint)
        assert r1.success is True

        # Step 2: Add Skill (uses provider's tools and capabilities)
        skill = SkillViewModel(
            skill_id="code_review",
            name="Code Review",
            capabilities=["code_analysis"],
            tools=["echo"],
        )
        r2 = shell.add_skill(skill)
        assert r2.success is True

        # Step 3: Verify Skill composition
        comp = shell.verify_skill_composition("code_review")
        assert comp is not None
        assert comp.is_complete is True

        # Step 4: Create Agent (uses Provider + Skill + Tools)
        agent = AgentProfile(
            identity=AgentIdentityView(
                agent_id="dev_agent",
                name="Development Agent",
                description="AI software engineer",
            ),
            provider_id="openai",
            skills=["code_review"],
            tools=["echo"],
            policy=AgentPolicyView(
                require_provider=True,
                max_concurrent_tasks=2,
            ),
        )
        r3 = shell.create_agent(agent)
        assert r3.success is True

        # Step 5: Activate Agent
        assert shell.activate_agent("dev_agent") is True

        # Step 6: Snapshot reflects all UI panels
        snap = shell.snapshot()
        # Left panel: Providers
        assert len(snap.providers) == 1
        assert snap.providers[0].provider_id == "openai"
        # Left panel: Skills
        assert len(snap.skills) == 1
        assert snap.skills[0].skill_id == "code_review"
        # Right panel: Tools
        assert any(t.tool_id == "echo" for t in snap.tools)
        # Center: Agents
        assert len(snap.agents) == 1
        assert snap.agents[0].identity.agent_id == "dev_agent"
        # Center active: Agent
        assert snap.active_agent_id == "dev_agent"

    def test_no_source_modification_required(self, shell: WorkbenchProductShell) -> None:
        """验证: 创建 Provider/Skill/Agent 不需要修改源码。"""
        # Phase 1-4 已建立完整的 Service Controller 入口
        # UI 操作只需要调用 Shell API

        # Add 2 providers
        shell.add_provider(ProviderEndpoint(
            provider_id="openai", protocol=ProviderProtocol.OPENAI,
            api_key="sk", models=["gpt-4"],
        ))
        shell.add_provider(ProviderEndpoint(
            provider_id="deepseek", protocol=ProviderProtocol.DEEPSEEK,
            api_key="sk", models=["deepseek-chat"],
        ))

        # Add 2 skills
        shell.add_skill(SkillViewModel(
            skill_id="skill1", name="S1", capabilities=["code_analysis"],
        ))
        shell.add_skill(SkillViewModel(
            skill_id="skill2", name="S2", capabilities=["lint"], tools=["echo"],
        ))

        # Add 3 agents
        for i in range(1, 4):
            shell.create_agent(AgentProfile(
                identity=AgentIdentityView(agent_id=f"agent{i}", name=f"A{i}"),
                provider_id="openai",
                skills=[f"skill{i % 2 + 1}"],
                tools=["echo"],
            ))

        snap = shell.snapshot()
        assert len(snap.providers) == 2
        assert len(snap.skills) == 2
        assert len(snap.agents) == 3