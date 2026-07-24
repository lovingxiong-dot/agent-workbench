"""presentation/view_models/agent_profile.py — AgentProfile ViewModel。

v6.10.0-alpha Agent Configuration Layer。

边界（关键）：
  - AgentProfile 是 v6-agent Product 概念，NOT Runtime
  - 通过 identity / provider / skills / tools / policy 组合配置
  - 通过 ConfigStore 持久化（Configuration-Driven Principle P5）
  - 不修改 Foundation Protocol AgentIdentity（frozen）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentIdentityView:
    """Agent Identity 视图（与 Foundation Protocol AgentIdentity 互补）。

    Foundation Protocol AgentIdentity（frozen）：
      agent_id, name, type, version, system_prompt, provider, model, metadata

    AgentIdentityView（v6-agent 视图）：
      简化展示字段，给 UI 渲染用。
    """

    agent_id: str
    name: str
    description: str = ""
    avatar: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentPolicyView:
    """Agent Policy 视图。

    Policy 是 Product 层概念（不在 Runtime）。
    Workbench v6.10 提供默认策略：
      - require_provider: 必须有有效 Provider
      - require_skills: 必须至少有 1 个 Skill
      - max_concurrent_tasks: 最大并发任务数
    """

    require_provider: bool = True
    require_skills: bool = False
    max_concurrent_tasks: int = 1
    custom_rules: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.custom_rules is None:
            self.custom_rules = {}


@dataclass
class AgentProfile:
    """Agent 完整配置（v6-agent Product 概念）。

    字段映射（按 Brief）：
      identity  -> AgentIdentityView
      provider  -> provider_id (str)
      skills    -> List[str] (skill_ids)
      tools     -> List[str] (tool_ids)
      policy    -> AgentPolicyView
    """

    identity: AgentIdentityView
    provider_id: str = ""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    policy: AgentPolicyView = field(default_factory=AgentPolicyView)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.skills is None:
            self.skills = []
        if self.tools is None:
            self.tools = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentProfileListViewModel:
    """Agent Profile 列表视图模型。"""

    profiles: List[AgentProfile] = field(default_factory=list)
    active_agent_id: Optional[str] = None
    total_count: int = 0

    def __post_init__(self) -> None:
        if self.profiles is None:
            self.profiles = []
        self.total_count = len(self.profiles)

    def get_active(self) -> Optional[AgentProfile]:
        if self.active_agent_id is None:
            return None
        for p in self.profiles:
            if p.identity.agent_id == self.active_agent_id:
                return p
        return None