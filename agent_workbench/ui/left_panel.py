"""agent_workbench/ui/left_panel.py — V6 左栏扩展。

在 v6.ui.left_panel.LeftPanel 基础上新增左下角「设置」按钮，用于打开右侧
Agent Configuration 面板。完全保留 V6 左栏的设计与信号契约。
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton

from v6.ui.base import font
from v6.ui.left_panel import LeftPanel as V6LeftPanel


class WorkbenchLeftPanel(V6LeftPanel):
    """Agent Workbench 专用左栏：新增设置按钮入口。"""

    settings_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings_btn = QPushButton("设置", self)
        self._settings_btn.setFont(font(11))
        self._settings_btn.setFixedWidth(56)
        self._settings_btn.setToolTip("打开 Agent Configuration 面板")
        self._settings_btn.clicked.connect(self.settings_requested.emit)

        # 在 theme_btn 之后、stretch 之前插入设置按钮
        bottom = self.layout().itemAt(self.layout().count() - 1).layout()
        bottom.insertWidget(bottom.count() - 1, self._settings_btn)

    def _style(self) -> None:
        super()._style()
        if hasattr(self, "_settings_btn"):
            self._settings_btn.setStyleSheet(self._theme_btn.styleSheet())
