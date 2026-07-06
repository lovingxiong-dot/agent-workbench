"""v6/ui/terminal_widget.py — 终端组件。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
)

from v6.ui.base import C, mono_font, theme


class TerminalWidget(QWidget):
    """终端面板：命令输出区 + 命令输入框，占位显示 Demo 历史。"""

    command_entered = Signal(str)

    DEMO_HISTORY = [
        "Microsoft Windows [版本 10.0.19045.3693]",
        "(c) Microsoft Corporation。保留所有权利。",
        "",
        "F:\\Agent\\agent_workbench> python -m pytest tests/v6/test_v6_smoke.py -v",
        "============================== 5 passed in 0.22s ==============================",
        "",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        for line in self.DEMO_HISTORY:
            self.append_output(line)
        self.refresh_theme()
        theme.changed.connect(self.refresh_theme)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(mono_font(12))
        self._output.setAcceptRichText(False)
        layout.addWidget(self._output, 1)

        bottom = QHBoxLayout()
        self._prompt = QLabel(">")
        self._input = QLineEdit()
        self._input.setPlaceholderText("输入命令...")
        self._input.returnPressed.connect(self._on_command)
        bottom.addWidget(self._prompt)
        bottom.addWidget(self._input, 1)
        self._run_btn = QPushButton("运行")
        self._run_btn.setFixedWidth(56)
        self._run_btn.clicked.connect(self._on_command)
        bottom.addWidget(self._run_btn)
        layout.addLayout(bottom)

    def _on_command(self) -> None:
        cmd = self._input.text().strip()
        if not cmd:
            return
        self.append_output(f"$ {cmd}")
        self.command_entered.emit(cmd)
        self._input.clear()

    def append_output(self, text: str) -> None:
        """追加终端输出。"""
        self._output.append(text)

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._output.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_primary']}; color: {C['mono_text']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 6px; }}"
        )
        self._input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 6px; }}"
        )
        self._run_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )


