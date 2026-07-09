"""agent_workbench/ui/dialogs/add_workflow_dialog.py — 新增 Workflow 对话框。

返回的 workflow 配置字典格式：
{
    "name": str,
    "description": str,
    "steps": list[str],
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QLineEdit, QPlainTextEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddWorkflowDialog(AddConfigItemDialog):
    """用于新增 Workflow 模板（简单步骤列表）的表单对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add Workflow", parent)

        self._name_edit = self._line_edit("daily-report")
        self._form.addRow("Name:", self._name_edit)

        self._description_edit = self._line_edit("Generate daily report")
        self._form.addRow("Description:", self._description_edit)

        self._steps_edit = QPlainTextEdit(self)
        self._steps_edit.setPlaceholderText("One step per line")
        self._steps_edit.setMaximumBlockCount(100)
        self._form.addRow("Steps:", self._steps_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 workflow 配置字典。"""
        steps_text = self._steps_edit.toPlainText().strip()
        steps = [line.strip() for line in steps_text.splitlines() if line.strip()]

        return {
            "name": self._name_edit.text().strip(),
            "description": self._description_edit.text().strip(),
            "steps": steps,
            "enabled": self._enabled_check.isChecked(),
        }
