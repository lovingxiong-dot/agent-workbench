"""presentation/services/product_shell.py — v6.10 Product Shell Integration。

v6.10.0-alpha Product Shell Integration。

职责：
  - 聚合 Phase 1-4 的 Service Controllers
  - 提供统一的 Product Shell API（list/add/remove/switch for Provider/Tool/Skill/Agent）
  - 通过 Configuration-Driven Principle (P5) 暴露所有能力
  - 不修改 Runtime / Protocol / 现有 UI Shell

Left panel / Right panel / Center 三栏通过 WorkbenchProductShell 协调。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent_workbench.presentation.adapters.provider_adapter import ProviderAdapter
from agent_workbench.presentation.adapters.skill_adapter import SkillAdapter
from agent_workbench.presentation.adapters.tool_adapter import ToolAdapter
from agent_workbench.presentation.services.agent_profile_service import (
    AgentConfigBackend,
    RuntimeEntityLookup,
    WorkbenchAgentProfileRegistry,
)
from agent_workbench.presentation.services.provider_service import (
    ProviderServiceController,
    WorkbenchProviderConfigBackend,
    WorkbenchProviderRegistry,
)
from agent_workbench.presentation.services.skill_service import (
    RuntimeCapabilityLookup,
    SkillConfigBackend,
    WorkbenchSkillRegistry,
)
from agent_workbench.presentation.services.tool_service import (
    RuntimeToolBackend,
    WorkbenchToolServiceController,
)


@dataclass
class ShellSnapshot:
    """Product Shell 当前状态快照。"""

    providers: List[Any] = field(default_factory=list)
    active_provider_id: Optional[str] = None
    tools: List[Any] = field(default_factory=list)
    skills: List[Any] = field(default_factory=list)
    agents: List[Any] = field(default_factory=list)
    active_agent_id: Optional[str] = None


class WorkbenchProductShell:
    """v6.10 Product Shell Integration Controller。

    职责：
      - 持有 Phase 1-4 的所有 Service Controllers
      - 暴露统一的 Shell API（left/right/center 各自一套）
      - 提供 ShellSnapshot（UI 一站式 refresh 入口）
      - 不修改 Runtime / Protocol / 现有 UI Shell

    UI 用法：
      shell = WorkbenchProductShell(...)
      snapshot = shell.snapshot()
      left_panel.set_view_models(snapshot.providers)
      center_panel.set_view_model(snapshot.active_agent)
      right_panel.set_view_models(snapshot.tools)
    """

    def __init__(
        self,
        provider_service: ProviderServiceController,
        tool_service: WorkbenchToolServiceController,
        skill_registry: WorkbenchSkillRegistry,
        agent_registry: WorkbenchAgentProfileRegistry,
    ) -> None:
        self._provider = provider_service
        self._tool = tool_service
        self._skill = skill_registry
        self._agent = agent_registry

    # ─── Snapshot ────────────────────────────────────────────

    def snapshot(self) -> ShellSnapshot:
        """获取 Product Shell 状态快照。"""
        provider_vm = self._provider.list_view_model()
        tool_vm = self._tool.list_view_model()
        skill_vm = self._skill.list_view_model()
        agent_vm = self._agent.list_view_model()
        return ShellSnapshot(
            providers=provider_vm.providers,
            active_provider_id=provider_vm.active_provider_id,
            tools=tool_vm.tools,
            skills=skill_vm.skills,
            agents=agent_vm.profiles,
            active_agent_id=agent_vm.active_agent_id,
        )

    # ─── Provider operations (Left panel) ───────────────────

    def add_provider(self, endpoint: Any) -> Any:
        """添加 Provider。"""
        return self._provider.add_provider(endpoint)

    def remove_provider(self, provider_id: str) -> Any:
        """删除 Provider。"""
        return self._provider.remove_provider(provider_id)

    def switch_provider(self, provider_id: str) -> Any:
        """切换 Provider。"""
        return self._provider.switch_provider(provider_id)

    def list_provider_view_models(self) -> List[Any]:
        """获取 Provider ViewModel 列表。"""
        return self._provider.list_view_model().providers

    # ─── Tool operations (Right panel) ──────────────────────

    def enable_tool(self, tool_id: str) -> Any:
        return self._tool.enable_tool(tool_id)

    def disable_tool(self, tool_id: str) -> Any:
        return self._tool.disable_tool(tool_id)

    def list_tool_view_models(self) -> List[Any]:
        return self._tool.list_view_model().tools

    # ─── Skill operations (Left panel) ──────────────────────

    def add_skill(self, skill_vm: Any) -> Any:
        return self._skill.add_skill(skill_vm)

    def remove_skill(self, skill_id: str) -> Any:
        return self._skill.remove_skill(skill_id)

    def verify_skill_composition(self, skill_id: str) -> Optional[Any]:
        return self._skill.verify_composition(skill_id)

    def list_skill_view_models(self) -> List[Any]:
        return self._skill.list_view_model().skills

    # ─── Agent operations (Center) ──────────────────────────

    def create_agent(self, profile: Any) -> Any:
        return self._agent.create_agent(profile)

    def delete_agent(self, agent_id: str) -> Any:
        return self._agent.delete_agent(agent_id)

    def activate_agent(self, agent_id: str) -> bool:
        return self._agent.activate_agent(agent_id)

    def list_agent_profiles(self) -> List[Any]:
        return self._agent.list_view_model().profiles

    def get_active_agent(self) -> Optional[Any]:
        return self._agent.list_view_model().get_active()


def build_product_shell(
    config_store,
    runtime_provider_backend,
    runtime_tool_backend,
    capability_registry_backend,
    tool_ids_backend,
    active_provider_id: Optional[str] = None,
) -> WorkbenchProductShell:
    """工厂：从 ConfigStore + Runtime 后端构造 WorkbenchProductShell。

    这是 v6.10 的标准组装路径：
      ConfigStore + Runtime Backends -> 4 个 Service Controllers -> Shell
    """
    # Provider
    provider_registry = WorkbenchProviderRegistry(runtime_provider_backend)
    provider_config_backend = WorkbenchProviderConfigBackend(config_store)
    provider_service = ProviderServiceController(provider_registry, provider_config_backend)

    # Tool
    tool_service = WorkbenchToolServiceController(runtime_tool_backend)

    # Skill
    capability_lookup = _CompositeCapabilityLookup(capability_registry_backend, tool_ids_backend)
    skill_config_backend = SkillConfigBackend(config_store)
    skill_registry = WorkbenchSkillRegistry(skill_config_backend, capability_lookup)

    # Agent
    agent_lookup = _AgentEntityLookup(
        provider_service=provider_service,
        skill_registry=skill_registry,
        tool_service=tool_service,
    )
    agent_config_backend = AgentConfigBackend(config_store)
    agent_registry = WorkbenchAgentProfileRegistry(agent_config_backend, agent_lookup)

    return WorkbenchProductShell(
        provider_service=provider_service,
        tool_service=tool_service,
        skill_registry=skill_registry,
        agent_registry=agent_registry,
    )


class _CompositeCapabilityLookup:
    """组合 Capability + Tool 的 Capability Lookup。"""

    def __init__(self, capability_backend: Any, tool_backend: Any) -> None:
        self._capability = capability_backend
        self._tool = tool_backend

    def list_capability_ids(self) -> List[str]:
        return self._capability.list_capability_ids()

    def list_tool_ids(self) -> List[str]:
        return self._tool.list_tool_ids()


class _AgentEntityLookup:
    """Agent Profile 引用完整性检查（聚合 Provider/Skill/Tool）。"""

    def __init__(
        self,
        provider_service: ProviderServiceController,
        skill_registry: WorkbenchSkillRegistry,
        tool_service: WorkbenchToolServiceController,
    ) -> None:
        self._provider = provider_service
        self._skill = skill_registry
        self._tool = tool_service

    def provider_exists(self, provider_id: str) -> bool:
        providers = self._provider.list_view_model().providers
        return any(p.provider_id == provider_id for p in providers)

    def skill_exists(self, skill_id: str) -> bool:
        return any(s.skill_id == skill_id for s in self._skill.list_view_model().skills)

    def tool_exists(self, tool_id: str) -> bool:
        return any(t.tool_id == tool_id for t in self._tool.list_view_model().tools)