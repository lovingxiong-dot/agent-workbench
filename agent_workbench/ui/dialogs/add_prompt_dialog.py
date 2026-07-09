"""agent_workbench/ui/dialogs/add_prompt_dialog.py — 新增 Prompt 模板对话框。

返回的 prompt 配置字典格式：
{
    "name": str,
    "description": str,
    "template": str,
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QLineEdit, QPlainTextEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddPromptDialog(AddConfigItemDialog):
    """用于新增 Prompt 模板的表单对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add Prompt", parent)

        self._name_edit = self._line_edit("coder")
        self._form.addRow("Name:", self._name_edit)

        self._description_edit = self._line_edit("Code assistant prompt")
        self._form.addRow("Description:", self._description_edit)

        self._template_edit = QPlainTextEdit(self)
        self._template_edit.setPlaceholderText("You are a helpful coding assistant...")
        self._template_edit.setMaximumBlockCount(200)
        self._form.addRow("Template:", self._template_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 prompt 配置字典。"""
        return {
            "name": self._name_edit.text().strip(),
            "description": self._description_edit.text().strip(),
            "template": self._template_edit.toPlainText().strip(),
            "enabled": self._enabled_check.isChecked(),
        }
