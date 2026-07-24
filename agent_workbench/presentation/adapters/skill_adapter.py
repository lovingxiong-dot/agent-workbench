"""presentation/adapters/skill_adapter.py — Skill Adapter。

v6.10.0-alpha Skill System Foundation。

边界：
  - Skill data 来自 ConfigStore（Configuration-Driven Principle P5）
  - 转换为 SkillViewModel 供 UI 消费
  - 不发起 Runtime 调用
  - Skill 不进入 Runtime Kernel
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from agent_workbench.presentation.view_models.skill import (
    SkillListViewModel,
    SkillViewModel,
)


class SkillAdapter:
    """Skill dict (ConfigStore) → SkillViewModel (UI) Adapter。"""

    def to_view_model(self, skill_dict: Dict[str, Any]) -> SkillViewModel:
        """转换 Skill dict 为 SkillViewModel。

        Args:
            skill_dict: ConfigStore 中的 Skill 配置。

        Returns:
            SkillViewModel 适用于 UI 渲染。
        """
        return SkillViewModel(
            skill_id=str(skill_dict.get("id", "")),
            name=str(skill_dict.get("name", "")),
            description=str(skill_dict.get("description", "")),
            version=str(skill_dict.get("version", "1.0.0")),
            capabilities=list(skill_dict.get("capabilities", []) or []),
            tools=list(skill_dict.get("tools", []) or []),
            prompt=str(skill_dict.get("prompt", "")),
            metadata=dict(skill_dict.get("metadata", {}) or {}),
        )

    def to_list_view_model(self, skills: Iterable[Dict[str, Any]]) -> SkillListViewModel:
        """转换 Skill dict 列表为 SkillListViewModel。"""
        view_models = [self.to_view_model(s) for s in skills]
        return SkillListViewModel(skills=view_models)

    def view_model_to_dict(self, vm: SkillViewModel) -> Dict[str, Any]:
        """SkillViewModel → Skill dict（持久化）。"""
        return {
            "id": vm.skill_id,
            "name": vm.name,
            "description": vm.description,
            "version": vm.version,
            "capabilities": list(vm.capabilities),
            "tools": list(vm.tools),
            "prompt": vm.prompt,
            "metadata": dict(vm.metadata),
        }