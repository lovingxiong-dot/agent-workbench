"""presentation/services/agent_profile_service.py — Workbench Agent Profile Service。

v6.10.0-alpha Agent Configuration Layer。

边界（关键）：
  - AgentProfile 是 v6-agent Product 概念
  - 通过 ConfigStore 持久化（Configuration-Driven Principle P5）
  - 不进入 Runtime
  - 不修改 Foundation Protocol AgentIdentity（frozen）
  - 不修改 RuntimeContext / RuntimeRequest / InteractionEvent

Brief 字段映射：
  identity / provider / skills / tools / policy

数据流：
  UI -> AgentProfileViewModel -> ConfigStore 持久化
                  ↓
  WorkbenchAgentProfileRegistry -> Runtime Provider/Skill/Tool lookup 验证
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from agent_workbench.presentation.view_models.agent_profile import (
    AgentIdentityView,
    AgentPolicyView,
    AgentProfile,
    AgentProfileListViewModel,
)


@dataclass
class CreateAgentResult:
    """创建 Agent 结果。"""

    success: bool
    agent_id: str = ""
    error: str = ""


@dataclass
class DeleteAgentResult:
    """删除 Agent 结果。"""

    success: bool
    agent_id: str = ""
    error: str = ""


class RuntimeEntityLookup(Protocol):
    """Runtime Entity Lookup Protocol（用于 Agent Profile composition 验证）。

    检查 Agent Profile 引用的 Provider / Skill / Tool 是否存在。
    """

    def provider_exists(self, provider_id: str) -> bool:
        ...

    def skill_exists(self, skill_id: str) -> bool:
        ...

    def tool_exists(self, tool_id: str) -> bool:
        ...


class AgentConfigBackend:
    """Agent Profile 配置持久化后端（委托 ConfigStore）。

    Configuration-Driven Principle (P5):
      UI 修改 Agent -> ConfigStore 持久化 -> 自动 reload
    """

    _KEY = "agent.profiles"

    def __init__(self, config_store) -> None:
        self._store = config_store

    def list_agent_dicts(self) -> List[Dict[str, Any]]:
        """列出所有 Agent 配置字典。"""
        return self._store.get(self._KEY, []) or []

    def upsert_agent(self, agent_dict: Dict[str, Any]) -> bool:
        """新增或更新 Agent 配置。"""
        agents = self.list_agent_dicts()
        agent_id = agent_dict.get("agent_id", "")
        existing_idx = None
        for i, a in enumerate(agents):
            if a.get("agent_id") == agent_id:
                existing_idx = i
                break
        if existing_idx is not None:
            agents[existing_idx] = agent_dict
        else:
            agents.append(agent_dict)
        self._store.set(self._KEY, agents)
        return True

    def remove_agent(self, agent_id: str) -> bool:
        """删除 Agent 配置。"""
        agents = self.list_agent_dicts()
        new_agents = [a for a in agents if a.get("agent_id") != agent_id]
        if len(new_agents) == len(agents):
            return False
        self._store.set(self._KEY, new_agents)
        return True

    def set_active_agent(self, agent_id: str) -> bool:
        """设置当前激活 Agent。"""
        self._store.set("agent.active", agent_id)
        return True

    def get_active_agent_id(self) -> Optional[str]:
        """获取当前激活 Agent ID。"""
        return self._store.get("agent.active")


class WorkbenchAgentProfileRegistry:
    """Workbench Agent Profile Registry（v6-agent 层 Product 概念）。

    Agent Profile 是 Agent 的配置蓝图：
      - 引用 Runtime Provider / Skill / Tool
      - 通过 identity / policy 表达行为约束
      - 创建/删除无需修改源码（Configuration-Driven）

    关键边界：
      - Agent Profile 不是 Runtime object
      - Profile 不进入 RuntimeDecision / Orchestrator
      - Profile execution 仍由 Runtime 处理
    """

    def __init__(
        self,
        config_backend: AgentConfigBackend,
        lookup: RuntimeEntityLookup,
    ) -> None:
        self._config = config_backend
        self._lookup = lookup

    # ─── List ────────────────────────────────────────────────

    def list_view_model(self) -> AgentProfileListViewModel:
        """获取所有 Agent Profile ViewModel。"""
        profiles = [self._dict_to_profile(d) for d in self._config.list_agent_dicts()]
        return AgentProfileListViewModel(
            profiles=profiles,
            active_agent_id=self._config.get_active_agent_id(),
        )

    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """获取单个 Agent Profile。"""
        for d in self._config.list_agent_dicts():
            if d.get("agent_id") == agent_id:
                return self._dict_to_profile(d)
        return None

    # ─── Create / Delete ────────────────────────────────────

    def create_agent(self, profile: AgentProfile) -> CreateAgentResult:
        """创建 Agent Profile（无需修改源码，Configuration-Driven）。

        Args:
            profile: AgentProfile（包含 identity / provider / skills / tools / policy）。

        Returns:
            CreateAgentResult 包含 success / agent_id / error。
        """
        identity = profile.identity
        if not identity.agent_id or not identity.agent_id.strip():
            return CreateAgentResult(success=False, error="agent_id 不能为空。")
        if not identity.name or not identity.name.strip():
            return CreateAgentResult(
                success=False, agent_id=identity.agent_id, error="name 不能为空。"
            )
        # Policy 校验
        if profile.policy.require_provider and not profile.provider_id:
            return CreateAgentResult(
                success=False,
                agent_id=identity.agent_id,
                error="policy.require_provider=True 时必须指定 provider。",
            )
        # 引用完整性检查（不发起 Runtime 调用，只 lookup）
        if profile.provider_id and not self._lookup.provider_exists(profile.provider_id):
            return CreateAgentResult(
                success=False,
                agent_id=identity.agent_id,
                error=f"provider '{profile.provider_id}' 不存在。",
            )
        for skill_id in profile.skills:
            if not self._lookup.skill_exists(skill_id):
                return CreateAgentResult(
                    success=False,
                    agent_id=identity.agent_id,
                    error=f"skill '{skill_id}' 不存在。",
                )
        for tool_id in profile.tools:
            if not self._lookup.tool_exists(tool_id):
                return CreateAgentResult(
                    success=False,
                    agent_id=identity.agent_id,
                    error=f"tool '{tool_id}' 不存在。",
                )

        self._config.upsert_agent(self._profile_to_dict(profile))
        return CreateAgentResult(success=True, agent_id=identity.agent_id)

    def delete_agent(self, agent_id: str) -> DeleteAgentResult:
        """删除 Agent Profile。"""
        ok = self._config.remove_agent(agent_id)
        if not ok:
            return DeleteAgentResult(
                success=False, agent_id=agent_id, error=f"agent '{agent_id}' 不存在。"
            )
        return DeleteAgentResult(success=True, agent_id=agent_id)

    def activate_agent(self, agent_id: str) -> bool:
        """激活 Agent（Runtime 仍由 RuntimeContext 触发）。"""
        if self.get_profile(agent_id) is None:
            return False
        self._config.set_active_agent(agent_id)
        return True

    # ─── Profile <-> Dict ───────────────────────────────────

    @staticmethod
    def _profile_to_dict(profile: AgentProfile) -> Dict[str, Any]:
        """AgentProfile -> ConfigStore dict。"""
        return {
            "agent_id": profile.identity.agent_id,
            "name": profile.identity.name,
            "description": profile.identity.description,
            "avatar": profile.identity.avatar,
            "version": profile.identity.version,
            "identity_metadata": dict(profile.identity.metadata),
            "provider_id": profile.provider_id,
            "skills": list(profile.skills),
            "tools": list(profile.tools),
            "policy": {
                "require_provider": profile.policy.require_provider,
                "require_skills": profile.policy.require_skills,
                "max_concurrent_tasks": profile.policy.max_concurrent_tasks,
                "custom_rules": dict(profile.policy.custom_rules),
            },
            "metadata": dict(profile.metadata),
        }

    @staticmethod
    def _dict_to_profile(d: Dict[str, Any]) -> AgentProfile:
        """ConfigStore dict -> AgentProfile。"""
        identity = AgentIdentityView(
            agent_id=d.get("agent_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            avatar=d.get("avatar", ""),
            version=d.get("version", "1.0.0"),
            metadata=dict(d.get("identity_metadata", {}) or {}),
        )
        policy_dict = d.get("policy", {}) or {}
        policy = AgentPolicyView(
            require_provider=bool(policy_dict.get("require_provider", True)),
            require_skills=bool(policy_dict.get("require_skills", False)),
            max_concurrent_tasks=int(policy_dict.get("max_concurrent_tasks", 1)),
            custom_rules=dict(policy_dict.get("custom_rules", {}) or {}),
        )
        return AgentProfile(
            identity=identity,
            provider_id=d.get("provider_id", ""),
            skills=list(d.get("skills", []) or []),
            tools=list(d.get("tools", []) or []),
            policy=policy,
            metadata=dict(d.get("metadata", {}) or {}),
        )