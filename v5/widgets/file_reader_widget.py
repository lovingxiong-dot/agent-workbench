"""V5 文件读取/编辑器组件。"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel, QPushButton, QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from .base import theme, C, font


class FileReaderWidget(QWidget):
    """文本文件读取/编辑器：打开、保存、大文件截断、多编码解码。"""
    file_opened = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = ""
        self._max_size = 1024 * 1024  # 1MB
        self._setup_ui()
        self._apply_theme()
        theme.changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 文件路径行
        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self._path_label = QLabel("未打开文件")
        self._path_label.setWordWrap(True)
        self._path_label.setFont(font(10))
        path_row.addWidget(self._path_label, 1)

        self._open_btn = QPushButton("打开...")
        self._open_btn.setFixedWidth(64)
        self._open_btn.setCursor(Qt.PointingHandCursor)
        self._open_btn.clicked.connect(self._on_open_file_dialog)
        path_row.addWidget(self._open_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setFixedWidth(56)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        path_row.addWidget(self._save_btn)

        layout.addLayout(path_row)

        # 编辑器
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Cascadia Code", 10))
        self._editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        layout.addWidget(self._editor, 1)

    def _apply_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._editor.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 8px; }}"
        )
        self._path_label.setStyleSheet(f"color: {C['text_secondary']};")
        btn_style = (
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._open_btn.setStyleSheet(btn_style)
        self._save_btn.setStyleSheet(btn_style)

    def _on_open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件")
        if path:
            self.open_file(path)
            self.file_opened.emit(path)

    def open_file(self, path: str):
        if not path or not os.path.isfile(path):
            self._editor.setPlainText(f"[文件不存在] {path}")
            return
        self._current_path = path
        self._path_label.setText(path)
        try:
            size = os.path.getsize(path)
            if size > self._max_size:
                with open(path, "rb") as f:
                    raw = f.read(self._max_size)
                text = self._decode(raw)
                self._editor.setPlainText(
                    text + f"\n\n[文件过大，仅显示前 {self._max_size // 1024}KB]"
                )
            else:
                with open(path, "rb") as f:
                    raw = f.read()
                self._editor.setPlainText(self._decode(raw))
        except Exception as e:
            self._editor.setPlainText(f"[读取失败] {e}")

    def set_content(self, content: str):
        self._editor.setPlainText(content)

    def _on_save(self):
        if not self._current_path:
            path, _ = QFileDialog.getSaveFileName(self, "保存文件")
            if not path:
                return
            self._current_path = path
            self._path_label.setText(path)
        try:
            with open(self._current_path, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    @staticmethod
    def _decode(raw: bytes) -> str:
        for encoding in ("utf-8", "gbk", "gb2312", "latin1"):
            try:
                return raw.decode(encoding)
            except Exception:
                continue
        return raw.decode("utf-8", errors="replace")
