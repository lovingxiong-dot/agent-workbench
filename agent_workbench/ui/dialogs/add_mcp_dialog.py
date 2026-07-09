"""agent_workbench/ui/dialogs/add_mcp_dialog.py — 新增 MCP Server 对话框。

返回的 MCP server 配置字典格式：
{
    "name": str,
    "command": str,
    "args": list[str],
    "env": dict[str, str],
    "enabled": bool,
}
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QLineEdit, QWidget

from agent_workbench.ui.dialogs.base import AddConfigItemDialog


class AddMcpDialog(AddConfigItemDialog):
    """用于新增 MCP Server 的表单对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add MCP Server", parent)

        self._name_edit = self._line_edit("filesystem-server")
        self._form.addRow("Name:", self._name_edit)

        self._command_edit = self._line_edit("npx")
        self._form.addRow("Command:", self._command_edit)

        self._args_edit = self._line_edit("-y @modelcontextprotocol/server-filesystem")
        self._form.addRow("Args:", self._args_edit)

        self._env_edit = self._line_edit("KEY=value, ANOTHER=1")
        self._form.addRow("Env:", self._env_edit)

        self._enabled_check = QCheckBox("Enabled", self)
        self._enabled_check.setChecked(True)
        self._form.addRow(self._enabled_check)

    def _build_result(self) -> dict[str, Any]:
        """返回用户填写的 MCP server 配置字典。"""
        args_text = self._args_edit.text().strip()
        args = [arg for arg in args_text.split() if arg]

        env: dict[str, str] = {}
        env_text = self._env_edit.text().strip()
        if env_text:
            for pair in env_text.split(","):
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    env[key.strip()] = value.strip()

        return {
            "name": self._name_edit.text().strip(),
            "command": self._command_edit.text().strip(),
            "args": args,
            "env": env,
            "enabled": self._enabled_check.isChecked(),
        }
