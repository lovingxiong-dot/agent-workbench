"""v4 终端组件 — 基于 TerminalWorker 的命令终端。"""
import os
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .base import theme, C, font
from workers.terminal_worker import TerminalWorker


class TerminalWidget(QWidget):
    """命令终端：显示输出 + 输入命令 + 运行/停止/清空。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[TerminalWorker] = None
        self._cwd = os.getcwd()
        self._setup_ui()
        self._apply_theme()
        theme.changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 输出区
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Cascadia Code", 10))
        self._output.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        layout.addWidget(self._output, 1)

        # 命令输入行
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)

        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("输入命令并回车执行...")
        self._cmd_input.returnPressed.connect(self._on_run_command)
        cmd_row.addWidget(self._cmd_input, 1)

        self._run_btn = QPushButton("运行")
        self._run_btn.setFixedWidth(56)
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.clicked.connect(self._on_run_command)
        cmd_row.addWidget(self._run_btn)

        self._stop_btn = QPushButton("停止")
        self._stop_btn.setFixedWidth(56)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setVisible(False)
        self._stop_btn.clicked.connect(self.stop)
        cmd_row.addWidget(self._stop_btn)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedWidth(56)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self.clear)
        cmd_row.addWidget(self._clear_btn)

        layout.addLayout(cmd_row)

    def _apply_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._output.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 8px; }}"
        )
        btn_style = (
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._run_btn.setStyleSheet(btn_style)
        self._stop_btn.setStyleSheet(btn_style)
        self._clear_btn.setStyleSheet(btn_style)
        self._cmd_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        )

    def set_cwd(self, cwd: str):
        self._cwd = cwd or os.getcwd()

    def run_command(self, command: str, cwd: str = ""):
        if not command or not command.strip():
            return
        if self._worker and self._worker.isRunning():
            return
        self.append_output(f"$ {command}")
        self._cmd_input.clear()
        self._stop_btn.setVisible(True)
        self._run_btn.setEnabled(False)
        self._worker = TerminalWorker(command, cwd or self._cwd)
        self._worker.output.connect(self.append_output)
        self._worker.finished_cmd.connect(self._on_command_finished)
        self._worker.start()

    def _on_run_command(self):
        cmd = self._cmd_input.text().strip()
        if cmd:
            self.run_command(cmd)

    def _on_command_finished(self, code: int):
        self.append_output(f"[退出码: {code}]")
        self._stop_btn.setVisible(False)
        self._run_btn.setEnabled(True)
        self._worker = None

    def append_output(self, text: str):
        self._output.appendPlainText(text)
        scrollbar = self._output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self._output.clear()

    def stop(self):
        if self._worker:
            self._worker.stop()
            self._worker = None
        self._stop_btn.setVisible(False)
        self._run_btn.setEnabled(True)
