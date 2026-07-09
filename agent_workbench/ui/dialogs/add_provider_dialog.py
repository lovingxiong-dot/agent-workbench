"""agent_workbench/ui/dialogs/add_provider_dialog.py — 新增 Provider 对话框。

返回的 provider 字典与 ModelModule 期望的格式保持一致：
{
    "name": str,
    "type": "echo" | "openai",
    "model": str,
    "api_key": str,
    "base_url": str,
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddProviderDialog(AddConfigItemDialog):
    """用于新增 AI Provider 的表单对话框。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        provider_types: list[str] | None = None,
    ) -> None:
        super().__init__("Add AI Provider", parent)

        self._name_edit = self._line_edit("openai-gpt4")
        self._form.addRow("Name:", self._name_edit)

        self._type_combo = QComboBox(self)
        self._type_combo.addItems(provider_types or ["echo", "openai"])
        self._form.addRow("Type:", self._type_combo)

        self._model_edit = self._line_edit("gpt-4o")
        self._form.addRow("Model:", self._model_edit)

        self._api_key_edit = QLineEdit(self)
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("sk-...")
        self._form.addRow("API Key:", self._api_key_edit)

        self._base_url_edit = self._line_edit("https://api.openai.com/v1")
        self._form.addRow("Base URL:", self._base_url_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 provider 配置字典。"""
        return {
            "name": self._name_edit.text().strip(),
            "type": self._type_combo.currentText(),
            "model": self._model_edit.text().strip(),
            "api_key": self._api_key_edit.text().strip(),
            "base_url": self._base_url_edit.text().strip(),
            "enabled": self._enabled_check.isChecked(),
        }
