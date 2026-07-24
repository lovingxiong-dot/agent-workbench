"""presentation/view_models/skill.py — Skill ViewModel。

v6.10.0-alpha Skill System Foundation。

设计原则：
  ✓ Skill 是 v6-agent 层 Product 概念，不进入 Runtime Kernel
  ✓ Skill composes 已有 Capability（Composition > Runtime extension）
  ✓ Skill 不是 Runtime object（不修改 Capability Runtime Contract）

Brief 字段映射：
  id        -> skill_id
  name      -> name
  description -> description
  version   -> version
  capabilities -> capabilities (List[str], capability_ids)
  tools     -> tools (List[str], tool_ids)
  prompt    -> prompt
  metadata  -> metadata
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SkillViewModel:
    """Skill UI 视图模型（v6-agent 层 Product 概念）。

    注意：
      - Skill 不属于 Runtime Capability
      - Skill 通过 capabilities: List[str] 引用已有 Capability ID
      - Skill 通过 tools: List[str] 引用 Tool ID
    """

    skill_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    prompt: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capabilities is None:
            self.capabilities = []
        if self.tools is None:
            self.tools = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SkillListViewModel:
    """Skill 列表视图模型。"""

    skills: List[SkillViewModel] = field(default_factory=list)
    total_count: int = 0

    def __post_init__(self) -> None:
        if self.skills is None:
            self.skills = []
        self.total_count = len(self.skills)

    def find_by_id(self, skill_id: str) -> Optional[SkillViewModel]:
        for s in self.skills:
            if s.skill_id == skill_id:
                return s
        return None


@dataclass
class SkillCompositionResult:
    """Skill Capability Composition 验证结果。

    用于确保 Skill 引用的 Capability / Tool 真实存在。
    """

    skill_id: str
    valid_capabilities: List[str] = field(default_factory=list)
    missing_capabilities: List[str] = field(default_factory=list)
    valid_tools: List[str] = field(default_factory=list)
    missing_tools: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return not self.missing_capabilities and not self.missing_tools