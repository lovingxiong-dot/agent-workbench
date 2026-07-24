"""presentation/services/skill_service.py — Workbench Skill Service。

v6.10.0-alpha Skill System Foundation。

边界（关键）：
  - Skill 不进入 Runtime Kernel
  - Skill composes Runtime Capability（by capability_ids / tool_ids）
  - Skill 持久化在 ConfigStore
  - Skill 执行通过 Runtime Capability Runtime Contract（已存在）

Skill 数据流：
  ConfigStore -> SkillAdapter -> SkillViewModel -> UI
                ↓
  WorkbenchSkillRegistry -> Capability Registry 验证 composition 完整性
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from agent_workbench.presentation.adapters.skill_adapter import SkillAdapter
from agent_workbench.presentation.view_models.skill import (
    SkillCompositionResult,
    SkillListViewModel,
    SkillViewModel,
)


@dataclass
class AddSkillResult:
    """添加 Skill 结果。"""

    success: bool
    skill_id: str = ""
    error: str = ""


@dataclass
class RemoveSkillResult:
    """删除 Skill 结果。"""

    success: bool
    skill_id: str = ""
    error: str = ""


class RuntimeCapabilityLookup(Protocol):
    """Runtime Capability Lookup Protocol（v6-agent 层定义）。

    用于 Skill composition 验证：检查 Skill 引用的 capability / tool 是否存在。
    """

    def list_capability_ids(self) -> List[str]:
        """列出所有已注册 Capability ID。"""
        ...

    def list_tool_ids(self) -> List[str]:
        """列出所有已注册 Tool ID。"""
        ...


class SkillConfigBackend:
    """Skill 配置持久化后端（委托 ConfigStore）。

    Configuration-Driven Principle (P5):
      UI 修改 Skill -> ConfigStore 持久化 -> SkillRegistry 反映
    """

    _KEY = "skill.registry"

    def __init__(self, config_store) -> None:
        self._store = config_store

    def list_skill_dicts(self) -> List[Dict[str, Any]]:
        """列出所有 Skill 配置字典。"""
        return self._store.get(self._KEY, []) or []

    def upsert_skill(self, skill_dict: Dict[str, Any]) -> bool:
        """新增或更新 Skill 配置。"""
        skills = self.list_skill_dicts()
        skill_id = skill_dict.get("id", "")
        existing_idx = None
        for i, s in enumerate(skills):
            if s.get("id") == skill_id:
                existing_idx = i
                break
        if existing_idx is not None:
            skills[existing_idx] = skill_dict
        else:
            skills.append(skill_dict)
        self._store.set(self._KEY, skills)
        return True

    def remove_skill(self, skill_id: str) -> bool:
        """删除 Skill 配置。"""
        skills = self.list_skill_dicts()
        new_skills = [s for s in skills if s.get("id") != skill_id]
        if len(new_skills) == len(skills):
            return False
        self._store.set(self._KEY, new_skills)
        return True


class WorkbenchSkillRegistry:
    """Workbench Skill Registry（v6-agent 层 Product 概念）。

    关键边界：
      - Skill 不是 Runtime object
      - Skill 仅是 Capability Composition 描述
      - Skill execution 由 Runtime Capability Runtime Contract 处理
    """

    def __init__(
        self,
        config_backend: SkillConfigBackend,
        capability_lookup: RuntimeCapabilityLookup,
        adapter: Optional[SkillAdapter] = None,
    ) -> None:
        self._config = config_backend
        self._capability = capability_lookup
        self._adapter = adapter or SkillAdapter()

    # ─── List ────────────────────────────────────────────────

    def list_view_model(self) -> SkillListViewModel:
        """获取所有 Skill ViewModel。"""
        return self._adapter.to_list_view_model(self._config.list_skill_dicts())

    def get_view_model(self, skill_id: str) -> Optional[SkillViewModel]:
        """获取单个 Skill ViewModel。"""
        for s in self._config.list_skill_dicts():
            if s.get("id") == skill_id:
                return self._adapter.to_view_model(s)
        return None

    # ─── Composition ────────────────────────────────────────

    def verify_composition(self, skill_id: str) -> Optional[SkillCompositionResult]:
        """验证 Skill 引用的 Capability / Tool 是否存在。

        这是 Skill 的关键安全门：
          - Skill 不注册到 Runtime Capability
          - Skill 仅声明引用关系
          - 验证失败 → UI 显示 incomplete Skill
        """
        vm = self.get_view_model(skill_id)
        if vm is None:
            return None
        available_capabilities = set(self._capability.list_capability_ids())
        available_tools = set(self._capability.list_tool_ids())
        valid_cap = [c for c in vm.capabilities if c in available_capabilities]
        missing_cap = [c for c in vm.capabilities if c not in available_capabilities]
        valid_tools = [t for t in vm.tools if t in available_tools]
        missing_tools = [t for t in vm.tools if t not in available_tools]
        return SkillCompositionResult(
            skill_id=skill_id,
            valid_capabilities=valid_cap,
            missing_capabilities=missing_cap,
            valid_tools=valid_tools,
            missing_tools=missing_tools,
        )

    # ─── Add / Remove ──────────────────────────────────────

    def add_skill(self, vm: SkillViewModel) -> AddSkillResult:
        """添加 Skill。"""
        if not vm.skill_id or not vm.skill_id.strip():
            return AddSkillResult(success=False, error="skill_id 不能为空。")
        if not vm.name or not vm.name.strip():
            return AddSkillResult(success=False, skill_id=vm.skill_id, error="name 不能为空。")
        self._config.upsert_skill(self._adapter.view_model_to_dict(vm))
        return AddSkillResult(success=True, skill_id=vm.skill_id)

    def remove_skill(self, skill_id: str) -> RemoveSkillResult:
        """删除 Skill。"""
        ok = self._config.remove_skill(skill_id)
        if not ok:
            return RemoveSkillResult(success=False, skill_id=skill_id, error=f"Skill '{skill_id}' 不存在。")
        return RemoveSkillResult(success=True, skill_id=skill_id)