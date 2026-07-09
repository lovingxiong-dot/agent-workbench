"""agent_workbench/ui/dialogs/add_memory_dialog.py — 新增 Memory Store 对话框。

返回的 memory 配置字典格式：
{
    "name": str,
    "provider": "sqlite",
    "path": str,
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddMemoryDialog(AddConfigItemDialog):
    """用于新增 Memory Store 的表单对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add Memory Store", parent)

        self._name_edit = self._line_edit("default")
        self._form.addRow("Name:", self._name_edit)

        self._provider_combo = QComboBox(self)
        self._provider_combo.addItems(["sqlite"])
        self._form.addRow("Provider:", self._provider_combo)

        self._path_edit = self._line_edit("storage/memory/default.db")
        self._form.addRow("Path:", self._path_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 memory 配置字典。"""
        return {
            "name": self._name_edit.text().strip(),
            "provider": self._provider_combo.currentText(),
            "path": self._path_edit.text().strip(),
            "enabled": self._enabled_check.isChecked(),
        }
