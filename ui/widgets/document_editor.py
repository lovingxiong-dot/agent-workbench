"""
文档编辑器组件
- 默认只读模式
- 文本文件可切换编辑模式并保存
- 二进制文件仅显示占位信息，禁止编辑
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


def _detect_text_encoding(data: bytes) -> tuple[str, bool]:
    """尝试将 bytes 解码为文本。返回 (text, is_binary)。"""
    # 1. 空内容直接返回空文本
    if not data:
        return "", False

    # 2. 含 null 字节 -> 二进制
    if b"\x00" in data[:8192]:
        return "", True

    # 3. 优先 UTF-8
    try:
        return data.decode("utf-8", errors="strict"), False
    except UnicodeDecodeError:
        pass

    # 4. 尝试 chardet 探测
    try:
        import chardet
        result = chardet.detect(data[:8192])
        enc = result.get("encoding")
        conf = result.get("confidence", 0)
        if enc and conf and conf > 0.5:
            return data.decode(enc, errors="replace"), False
    except Exception:
        pass

    # 5. 兜底：latin-1 一定能解码，但可能乱码
    return data.decode("latin-1", errors="replace"), False


class DocumentEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._encoding = "utf-8"
        self._is_binary = False
        self._is_editable = False
        self._modified = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 工具栏 ──────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("docEditorToolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 6, 8, 6)
        tb_layout.setSpacing(8)

        self.path_label = QLabel("未打开文件")
        self.path_label.setObjectName("docEditorPath")
        tb_layout.addWidget(self.path_label)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #8B949E; font-size: 11px;")
        tb_layout.addWidget(self.status_label)

        tb_layout.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                padding: 3px 12px; border-radius: 5px; font-size: 11px;
            }
            QPushButton:checked {
                background-color: #388BFD26; border: 1px solid #58A6FF; color: #58A6FF;
            }
            QPushButton:hover { background-color: #30363D; }
            QPushButton:disabled { color: #6E7681; border-color: #21262D; }
        """)
        self.edit_btn.toggled.connect(self._on_edit_toggled)
        tb_layout.addWidget(self.edit_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: #FFFFFF; border: 1px solid #238636;
                padding: 3px 12px; border-radius: 5px; font-size: 11px;
            }
            QPushButton:hover { background-color: #2EA043; }
            QPushButton:disabled { background-color: #1F4D2E; color: #8B949E; border-color: #1F4D2E; }
        """)
        self.save_btn.clicked.connect(self.save_current)
        tb_layout.addWidget(self.save_btn)

        layout.addWidget(toolbar)

        # ── 编辑区 ──────────────────────────────
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(QFont("Cascadia Code", 10))
        self.editor.setObjectName("docEditor")
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def _on_edit_toggled(self, checked: bool):
        self._is_editable = checked
        self.editor.setReadOnly(not checked)
        self.save_btn.setEnabled(checked and self._modified)
        self.edit_btn.setText("编辑中" if checked else "编辑")
        if checked:
            self.status_label.setText("[编辑模式]")
        else:
            self.status_label.setText("[只读]")

    def _on_text_changed(self):
        if not self._path or self._is_binary:
            return
        self._modified = True
        if self._is_editable:
            self.save_btn.setEnabled(True)

    def open_file(self, path: str) -> bool:
        self.clear()
        self._path = path
        self.path_label.setText(path)
        self.path_label.setToolTip(path)

        if not os.path.exists(path):
            self._show_placeholder(f"文件不存在: {path}")
            return False

        if os.path.isdir(path):
            self._show_placeholder(f"路径是目录，无法编辑: {path}")
            return False

        size = os.path.getsize(path)
        # 大文件提示
        if size > 5 * 1024 * 1024:
            reply = QMessageBox.question(
                self, "文件较大",
                f"文件大小为 {size / 1024 / 1024:.1f} MB，是否继续打开？\n（将只加载前 1 MB）",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self._show_placeholder("用户取消打开大文件")
                return False

        max_read = 1024 * 1024 if size > 5 * 1024 * 1024 else None
        try:
            with open(path, "rb") as f:
                data = f.read(max_read) if max_read else f.read()
        except Exception as e:
            self._show_placeholder(f"读取失败: {e}")
            return False

        text, is_binary = _detect_text_encoding(data)
        self._is_binary = is_binary

        if is_binary:
            self.editor.setPlainText(
                f"二进制文件，无法预览和编辑\n"
                f"路径: {path}\n"
                f"大小: {size} bytes\n"
            )
            self.edit_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.status_label.setText("[二进制]")
            return False

        self.editor.setPlainText(text)
        self._modified = False
        self._is_editable = False
        self.edit_btn.setChecked(False)
        self.edit_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        self.editor.setReadOnly(True)
        self.status_label.setText("[只读]")
        return True

    def _show_placeholder(self, message: str):
        self.editor.setPlainText(message)
        self.edit_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.status_label.setText("")

    def set_editable(self, enabled: bool):
        self.edit_btn.setChecked(enabled)

    def save_current(self):
        if not self._path or self._is_binary or not self._is_editable:
            return
        try:
            text = self.editor.toPlainText()
            with open(self._path, "w", encoding=self._encoding, errors="replace") as f:
                f.write(text)
            self._modified = False
            self.save_btn.setEnabled(False)
            self.status_label.setText("[已保存]")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def clear(self):
        self._path = ""
        self._encoding = "utf-8"
        self._is_binary = False
        self._is_editable = False
        self._modified = False
        self.editor.clear()
        self.path_label.setText("未打开文件")
        self.path_label.setToolTip("")
        self.status_label.setText("")
        self.edit_btn.setChecked(False)
        self.edit_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.editor.setReadOnly(True)
