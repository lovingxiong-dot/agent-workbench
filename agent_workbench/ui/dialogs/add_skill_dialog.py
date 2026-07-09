"""agent_workbench/ui/dialogs/add_skill_dialog.py — 新增 Skill 对话框。

返回的 skill 配置字典格式：
{
    "name": str,
    "type": "python" | "script" | "echo",
    "source": str,
    "description": str,
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddSkillDialog(AddConfigItemDialog):
    """用于新增 Skill 的表单对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add Skill", parent)

        self._name_edit = self._line_edit("hello-skill")
        self._form.addRow("Name:", self._name_edit)

        self._type_combo = QComboBox(self)
        self._type_combo.addItems(["python", "script", "echo"])
        self._form.addRow("Type:", self._type_combo)

        self._source_edit = self._line_edit("skills/hello_skill.py")
        self._form.addRow("Source:", self._source_edit)

        self._description_edit = self._line_edit("A short description")
        self._form.addRow("Description:", self._description_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 skill 配置字典。"""
        return {
            "name": self._name_edit.text().strip(),
            "type": self._type_combo.currentText(),
            "source": self._source_edit.text().strip(),
            "description": self._description_edit.text().strip(),
            "enabled": self._enabled_check.isChecked(),
        }
