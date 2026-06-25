"""
右侧工作区组件
- 顶部标签栏：终端 / 日志 / 文档
- 集中管理终端、日志、文档编辑器的显示与交互
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QTextEdit,
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt

from .terminal import TerminalWidget
from .document_editor import DocumentEditor


class WorkspaceWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_log_lines = 500
        self.setObjectName("workspace")
        self.setTabPosition(QTabWidget.North)
        self._setup_tabs()

    def _setup_tabs(self):
        # ── 终端 ────────────────────────────────
        self.terminal = TerminalWidget()
        self.addTab(self.terminal, "终端")

        # ── 日志 ────────────────────────────────
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Cascadia Code", 9))
        self.log_area.setObjectName("logArea")
        log_layout.addWidget(self.log_area)
        self.addTab(log_widget, "日志")

        # ── 文档 ────────────────────────────────
        self.document_editor = DocumentEditor()
        self.addTab(self.document_editor, "文档")

    def add_log(self, text: str, is_header: bool = False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_header:
            self.log_area.append("")
            self.log_area.append(f"[{timestamp}] {text}")
        else:
            self.log_area.append(f"  [{timestamp}] {text}")
        self._trim_log()

    def clear_logs(self):
        self.log_area.clear()

    def set_logs_max_lines(self, max_lines: int):
        self._max_log_lines = max(max_lines, 10)
        self._trim_log()

    def _trim_log(self):
        doc = self.log_area.document()
        count = doc.blockCount()
        if count <= self._max_log_lines:
            return
        remove_count = min(50, count - self._max_log_lines)
        if remove_count <= 0:
            return
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor, remove_count)
        cursor.removeSelectedText()

    def set_terminal_focus(self):
        self.setCurrentIndex(0)
        self.terminal.input.setFocus()

    def open_document(self, path: str):
        self.setCurrentIndex(2)
        self.document_editor.open_file(path)

    def set_document_editable(self, editable: bool):
        self.document_editor.set_editable(editable)
