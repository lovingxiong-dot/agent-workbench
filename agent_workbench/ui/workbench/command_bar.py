"""agent_workbench/ui/workbench/command_bar.py — 底部命令输入栏。

用户在此输入命令/消息，按回车后发出 command_submitted(text) 信号。
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from v6.ui.base import C, font


class CommandBar(QWidget):
    """Workbench 命令输入栏。"""

    command_submitted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(8)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("输入命令或消息...")
        self._input.setFont(font(11))
        self._input.returnPressed.connect(self._submit)
        self._layout.addWidget(self._input, 1)

        self._btn = QPushButton("发送", self)
        self._btn.setFont(font(11))
        self._btn.clicked.connect(self._submit)
        self._layout.addWidget(self._btn)

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_darker']}; border-top: 1px solid {C['border']};"
        )
        self._input.setStyleSheet(
            f"background-color: {C['bg_input']}; color: {C['text_primary']}; border: 1px solid {C['border']}; border-radius: 4px; padding: 6px;"
        )
        self._btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['accent']}; color: {C['text_inverse']}; border: none; border-radius: 4px; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue']}; }}"
        )

    def _submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self.command_submitted.emit(text)
            self._input.clear()

    def set_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._btn.setEnabled(enabled)
