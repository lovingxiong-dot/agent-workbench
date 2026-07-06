"""v6/ui/file_reader_widget.py — 文件阅读器组件。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton,
)

from v6.ui.base import C, font, mono_font, theme


class FileReaderWidget(QWidget):
    """文件阅读器：地址栏 + 文本编辑区，占位显示 Demo 内容。"""

    open_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = ""
        self._build()
        self.open_file("README.md", "# Agent Workbench V6\n\n从零重写的结构化 UI 层。\n")
        self.refresh_theme()
        theme.changed.connect(self.refresh_theme)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        self._addr = QLineEdit()
        self._addr.setPlaceholderText("文件路径...")
        self._addr.returnPressed.connect(self._on_open)
        top.addWidget(self._addr, 1)
        self._open_btn = QPushButton("打开")
        self._open_btn.setFixedWidth(56)
        self._open_btn.clicked.connect(self._on_open)
        top.addWidget(self._open_btn)
        layout.addLayout(top)

        self._edit = QTextEdit()
        self._edit.setReadOnly(True)
        self._edit.setFont(mono_font(12))
        self._edit.setAcceptRichText(False)
        layout.addWidget(self._edit, 1)

    def _on_open(self) -> None:
        path = self._addr.text().strip()
        if path:
            self.open_requested.emit(path)
            self.open_file(path, f"# {path}\n\n[Demo 内容占位]\n")

    def open_file(self, path: str, content: str) -> None:
        """打开并显示文件内容。"""
        self._path = path
        self._addr.setText(path)
        self._edit.setPlainText(content)

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._addr.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 6px; }}"
        )
        self._edit.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_primary']}; color: {C['mono_text']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 6px; }}"
        )
        self._open_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
