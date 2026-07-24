"""agent_workbench/ui/workspaces/skill_workspace.py — Skill Workspace。

v6.10.0-alpha Skill System Foundation。

原 SkillWorkspace 占位实现已存在；本扩展追加 ViewModel 接入。
Skill 不进入 Runtime；Workspace 仅做 Product UI 接入。
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from agent_workbench.ui.workspace import Workspace


class SkillWorkspace(Workspace):
    """Skill Workspace（v6.10.0-alpha 扩展 ViewModel 接入）。"""

    workspace_id = "skill"
    title = "Skill"
    icon = "🧩"

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: Skill 操作 signals
    # ──────────────────────────────────────────────────────────

    add_requested = Signal()
    edit_requested = Signal(str)  # skill_id
    delete_requested = Signal(str)  # skill_id
    verify_composition_requested = Signal(str)  # skill_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._placeholder = QLabel("Skill Composition (v6.10.0-alpha ready)", self)
        self._layout.addWidget(self._placeholder)

        self._skills: list[Any] = []  # SkillViewModel 列表

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: ViewModel API
    # ──────────────────────────────────────────────────────────

    def set_view_models(self, view_models: list[Any]) -> None:
        """设置 Skill ViewModel 列表。

        Args:
            view_models: view_models.skill.SkillViewModel 列表。
        """
        self._skills = list(view_models)
        total_cap = sum(len(s.capabilities) for s in self._skills)
        total_tools = sum(len(s.tools) for s in self._skills)
        self._placeholder.setText(
            f"Skill Composition: {len(self._skills)} skills "
            f"({total_cap} capabilities, {total_tools} tools)"
        )

    def get_view_models(self) -> list[Any]:
        """获取当前 Skill ViewModel 列表。"""
        return list(self._skills)

    def request_add(self) -> None:
        """UI 请求添加 Skill（emit signal）。"""
        self.add_requested.emit()

    def request_edit(self, skill_id: str) -> None:
        """UI 请求编辑 Skill。"""
        self.edit_requested.emit(skill_id)

    def request_delete(self, skill_id: str) -> None:
        """UI 请求删除 Skill。"""
        self.delete_requested.emit(skill_id)

    def request_verify_composition(self, skill_id: str) -> None:
        """UI 请求验证 Skill composition。"""
        self.verify_composition_requested.emit(skill_id)