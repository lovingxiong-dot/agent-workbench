"""agent_workbench/ui/workbench/generic_workspace.py — 通用 Workspace。

当 Navigator 选中项没有专属 Workspace 时，显示其 PresentationModel 基本信息。
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from v6.ui.base import C, font


class GenericWorkspaceItem(QWidget):
    """通用工作区：显示模块名称与描述。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(12)

        self._title = QLabel("Generic", self)
        self._title.setFont(font(16, bold=True))
        self._title.setStyleSheet(f"color: {C['text_primary']};")
        self._layout.addWidget(self._title)

        self._description = QLabel("", self)
        self._description.setFont(font(11))
        self._description.setStyleSheet(f"color: {C['text_secondary']};")
        self._description.setWordWrap(True)
        self._layout.addWidget(self._description)

        self._layout.addStretch()
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def set_module(self, name: str, description: str = "") -> None:
        """设置当前显示模块信息。"""
        self._title.setText(name)
        self._description.setText(description)
