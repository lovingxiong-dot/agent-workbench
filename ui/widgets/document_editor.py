"""
文档编辑器组件
- 默认只读模式
- 文本文件可切换编辑模式并保存
- 图片文件直接预览
- 二进制文件显示文件信息 + 十六进制预览
- 双击文本区进入编辑模式
"""
import os
import mimetypes

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox,
)
from PySide6.QtGui import QFont, QImageReader, QPixmap, QKeySequence, QAction
from PySide6.QtCore import Qt, Signal


def _detect_text_encoding(data: bytes) -> tuple[str, bool]:
    """尝试将 bytes 解码为文本。返回 (text, is_binary)"""
    if not data:
        return "", False
    if b"\x00" in data[:8192]:
        return "", True
    try:
        return data.decode("utf-8", errors="strict"), False
    except UnicodeDecodeError:
        pass
    try:
        import chardet
        result = chardet.detect(data[:8192])
        enc = result.get("encoding")
        conf = result.get("confidence", 0)
        if enc and conf and conf > 0.5:
            return data.decode(enc, errors="replace"), False
    except Exception:
        pass
    return data.decode("latin-1", errors="replace"), False


def _format_hex_preview(data: bytes, max_bytes: int = 512) -> str:
    """生成十六进制预览文本"""
    chunk = data[:max_bytes]
    lines = []
    for i in range(0, len(chunk), 16):
        hex_part = " ".join(f"{b:02x}" for b in chunk[i:i+16])
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[i:i+16])
        lines.append(f"{i:08x}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)


class DocumentEditor(QWidget):
    document_opened = Signal(str, str, int)   # path, preview, size
    document_closed = Signal(str)             # path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._encoding = "utf-8"
        self._file_type = "none"   # text / image / binary / none
        self._original_text = ""   # 用于取消编辑恢复
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

        # 编辑按钮（只读模式显示）
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setObjectName("docEditorEditBtn")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._enter_edit_mode)
        tb_layout.addWidget(self.edit_btn)

        # 取消按钮（编辑模式显示）
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("docEditorCancelBtn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_edit)
        tb_layout.addWidget(self.cancel_btn)

        # 保存按钮（编辑模式显示）
        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("docEditorSaveBtn")
        self.save_btn.setVisible(False)
        self.save_btn.clicked.connect(self.save_current)
        tb_layout.addWidget(self.save_btn)

        layout.addWidget(toolbar)

        # ── 编辑区 ──────────────────────────────
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(QFont("Cascadia Code", 10))
        self.editor.setObjectName("docEditor")
        self.editor.textChanged.connect(self._on_text_changed)
        # 双击进入编辑模式
        self.editor.mouseDoubleClickEvent = self._on_editor_double_click
        layout.addWidget(self.editor)

        # 快捷键：Ctrl+S 保存、Esc 取消编辑
        self._save_action = QAction("保存", self)
        self._save_action.setShortcut(QKeySequence("Ctrl+S"))
        self._save_action.triggered.connect(self.save_current)
        self.addAction(self._save_action)

        self._cancel_action = QAction("取消编辑", self)
        self._cancel_action.setShortcut(QKeySequence("Escape"))
        self._cancel_action.triggered.connect(self._cancel_edit)
        self.addAction(self._cancel_action)

    def _on_editor_double_click(self, event):
        """双击文本区进入编辑模式（仅文本文件）"""
        if self._file_type == "text" and not self._is_editable:
            self._enter_edit_mode()
        # 调用父类默认双击行为（选中文本）
        QTextEdit.mouseDoubleClickEvent(self.editor, event)

    def _enter_edit_mode(self):
        if self._file_type != "text" or not self._path:
            return
        self._is_editable = True
        self.editor.setReadOnly(False)
        self._original_text = self.editor.toPlainText()
        self._update_button_state()
        self.status_label.setText("[编辑模式]")

    def _cancel_edit(self):
        """取消编辑，恢复原始内容"""
        self._is_editable = False
        self._modified = False
        self.editor.setPlainText(self._original_text)
        self.editor.setReadOnly(True)
        self._update_button_state()
        self.status_label.setText("[只读]")

    def _on_text_changed(self):
        if not self._path or self._file_type != "text" or not self._is_editable:
            return
        self._modified = True
        self.save_btn.setEnabled(True)

    def _update_button_state(self):
        """根据编辑状态更新按钮可见性"""
        if self._is_editable:
            self.edit_btn.setVisible(False)
            self.cancel_btn.setVisible(True)
            self.save_btn.setVisible(True)
            self.save_btn.setEnabled(self._modified)
        else:
            self.edit_btn.setVisible(True)
            self.edit_btn.setEnabled(self._file_type == "text")
            self.cancel_btn.setVisible(False)
            self.save_btn.setVisible(False)
            self.save_btn.setEnabled(False)

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
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "application/octet-stream"

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

        # 图片文件预览
        if mime.startswith("image/"):
            return self._open_image(path, mime, size)

        # 文本 vs 二进制
        text, is_binary = _detect_text_encoding(data)
        if is_binary:
            ok = self._open_binary(path, mime, size, data)
            self._emit_document_opened(path, "", size)
            return ok

        ok = self._open_text(path, text, size)
        preview = text[:500] if ok else ""
        self._emit_document_opened(path, preview, size)
        return ok

    def _emit_document_opened(self, path: str, preview: str, size: int):
        """统一发射文档打开信号"""
        try:
            self.document_opened.emit(path, preview, size)
        except Exception:
            pass

    def _open_text(self, path: str, text: str, size: int) -> bool:
        self._file_type = "text"
        self._encoding = "utf-8"
        self._original_text = text
        self.editor.setPlainText(text)
        self._modified = False
        self._is_editable = False
        self.editor.setReadOnly(True)
        self.status_label.setText(f"[只读] {size} bytes")
        self._update_button_state()
        return True

    def _open_image(self, path: str, mime: str, size: int) -> bool:
        self._file_type = "image"
        reader = QImageReader(path)
        if not reader.canRead():
            ok = self._open_binary(path, mime, size, b"")
            self._emit_document_opened(path, "", size)
            return ok
        # 在 QTextEdit 中显示图片，限制最大宽度为编辑区宽度
        pixmap = QPixmap.fromImageReader(reader)
        if pixmap.isNull():
            ok = self._open_binary(path, mime, size, b"")
            self._emit_document_opened(path, "", size)
            return ok

        max_width = 800
        if pixmap.width() > max_width:
            pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

        self.editor.setHtml(
            f"<div style='color:#8B949E; padding:8px;'>"
            f"<p>图片预览 ({mime})</p>"
            f"<p>大小: {size} bytes</p>"
            f"<img src='{path.replace(chr(92), '/')}' width='{pixmap.width()}' />"
            f"</div>"
        )
        self.status_label.setText(f"[图片] {size} bytes")
        self._update_button_state()
        self._emit_document_opened(path, "", size)
        return True

    def _open_binary(self, path: str, mime: str, size: int, data: bytes) -> bool:
        self._file_type = "binary"
        hex_preview = _format_hex_preview(data) if data else "无内容"
        info = (
            f"二进制文件，无法直接编辑\n"
            f"路径: {path}\n"
            f"类型: {mime}\n"
            f"大小: {size} bytes\n"
            f"\n前 {min(len(data), 512)} 字节十六进制预览:\n"
            f"{hex_preview}"
        )
        self.editor.setPlainText(info)
        self.status_label.setText(f"[二进制] {size} bytes")
        self._update_button_state()
        return False

    def _show_placeholder(self, message: str):
        self._file_type = "none"
        self.editor.setPlainText(message)
        self.status_label.setText("")
        self._update_button_state()

    def set_editable(self, enabled: bool):
        """外部调用进入/退出编辑模式"""
        if enabled:
            self._enter_edit_mode()
        else:
            self._cancel_edit()

    def save_current(self):
        if not self._path or self._file_type != "text" or not self._is_editable:
            return
        try:
            text = self.editor.toPlainText()
            with open(self._path, "w", encoding=self._encoding, errors="replace") as f:
                f.write(text)
            self._modified = False
            self._original_text = text
            self.save_btn.setEnabled(False)
            self.status_label.setText("[已保存]")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def clear(self):
        closed_path = self._path
        self._path = ""
        self._encoding = "utf-8"
        self._file_type = "none"
        self._original_text = ""
        self._is_editable = False
        self._modified = False
        self.editor.clear()
        self.path_label.setText("未打开文件")
        self.path_label.setToolTip("")
        self.status_label.setText("")
        self._update_button_state()
        if closed_path:
            try:
                self.document_closed.emit(closed_path)
            except Exception:
                pass
