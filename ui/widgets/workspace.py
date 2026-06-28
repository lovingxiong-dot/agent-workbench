"""
右侧工作区组件
- 顶部标签栏：终端 / 活动 / 文档
- 集中管理终端、结构化活动、文档编辑器的显示与交互
"""
from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QTextEdit,
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt, Signal

from .terminal import TerminalWidget
from .document_editor import DocumentEditor
from .activity_panel import ActivityWidget
from .shared_output import SharedOutputWidget


class WorkspaceWidget(QTabWidget):
    document_opened = Signal(str, str, int)   # path, preview, size
    document_activated = Signal(str)          # path（已打开文件被激活/重新聚焦）
    document_closed = Signal(str)             # path

    def __init__(self, parent=None, interpreter_service=None):
        super().__init__(parent)
        self._max_log_lines = 500
        self._interpreter_service = interpreter_service
        self.setObjectName("workspace")
        self.setTabPosition(QTabWidget.North)
        self._setup_tabs()
        self.currentChanged.connect(self._on_tab_changed)

    def _setup_tabs(self):
        # ── 终端 ────────────────────────────────
        self.terminal = TerminalWidget(interpreter_service=self._interpreter_service)
        self.addTab(self.terminal, "终端")

        # ── 执行输出（共享文档）───────────────────
        self.shared_output = SharedOutputWidget()
        self.addTab(self.shared_output, "执行输出")

        # ── 活动 ────────────────────────────────
        self.activity_panel = ActivityWidget()
        self.addTab(self.activity_panel, "活动")

        # ── 保留一个最小化的原始日志区（用于调试，不加入 Tab）──
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Cascadia Code", 9))
        self.log_area.setObjectName("logArea")

        # ── 文档 ────────────────────────────────
        self.document_editor = DocumentEditor()
        self.document_editor.document_opened.connect(self.document_opened.emit)
        self.document_editor.document_activated.connect(self.document_activated.emit)
        self.document_editor.document_closed.connect(self.document_closed.emit)
        self.addTab(self.document_editor, "文档")

    def _on_tab_changed(self, index):
        """切换到文档标签时，把当前文档标记为 active"""
        widget = self.widget(index)
        if widget is self.document_editor and self.document_editor._path:
            self.document_activated.emit(self.document_editor._path)

    def add_log(self, text: str, is_header: bool = False):
        """保留原始日志追加能力，用于内部调试"""
        from datetime import datetime
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

    def set_project_path(self, path: str):
        """同步当前项目路径到活动面板"""
        self.activity_panel.set_project_path(path)

    def refresh_activities(self, activities: list):
        """刷新活动面板数据"""
        self.activity_panel.set_activities(activities)

    def get_active_document_path(self) -> str:
        """返回当前文档编辑器打开的文件路径；若当前不是文档标签则返回空"""
        if self.currentWidget() is self.document_editor:
            return self.document_editor._path or ""
        return ""

    def get_open_document_path(self) -> str:
        """返回文档编辑器当前打开的文件路径（不论是否在文档标签）"""
        return self.document_editor._path or ""
