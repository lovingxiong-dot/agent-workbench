"""
SharedOutputWidget — AI 工具执行共享输出面板

展示 AI 在后台执行的工具命令及其结果，作为"共享文档"供用户查看。
不与用户终端 Widget 混合，保持前后端解耦。
"""
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor


class SharedOutputWidget(QWidget):
    """
    共享输出面板：按时间顺序显示 AI 工具执行记录。
    """

    MAX_LINES = 2000  # 防止内存无限增长

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标题栏
        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 4, 8, 4)
        header = QLabel("🖥 执行输出")
        header.setObjectName("panelHeader")
        header_row.addWidget(header)

        self.clear_btn = QPushButton("清除")
        self.clear_btn.setObjectName("fileTreeToolBtn")
        self.clear_btn.setFixedSize(40, 24)
        self.clear_btn.setToolTip("清除执行输出")
        self.clear_btn.clicked.connect(self.clear)
        header_row.addWidget(self.clear_btn)
        layout.addLayout(header_row)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setObjectName("panelSeparator")
        layout.addWidget(sep)

        # 输出区
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.output.setFont(QFont("Cascadia Code", 9))
        self.output.setObjectName("sharedOutput")
        self.output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.output)

        # 底部统计
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("fileTreePath")
        layout.addWidget(self.status_label)

    def append_execution(self, name: str, args: dict, result: str,
                         success: bool = True, elapsed_ms: int = 0):
        """追加一条工具执行记录"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if success else "❌"
        elapsed_text = f" ({elapsed_ms}ms)" if elapsed_ms > 0 else ""

        header = f"[{timestamp}] {status_icon} {name}{elapsed_text}"
        args_text = self._format_args(args)
        if args_text:
            header += f"  {args_text}"

        self.output.appendPlainText(header)

        result_text = (result or "").strip()
        if result_text:
            lines = result_text.splitlines()
            if len(lines) > 30:
                # 折叠长输出
                preview = "\n".join(lines[:15])
                collapsed = f"\n... ({len(lines) - 30} 行已折叠) ...\n"
                tail = "\n".join(lines[-15:])
                self.output.appendPlainText(preview + collapsed + tail)
            else:
                self.output.appendPlainText(result_text)
        else:
            self.output.appendPlainText("(无输出)")

        self.output.appendPlainText("—" * 40)
        self._trim_if_needed()
        self._update_status()
        self._scroll_to_bottom()

    def _format_args(self, args: dict) -> str:
        """将工具参数格式化为单行摘要"""
        if not args:
            return ""
        if isinstance(args, dict):
            items = []
            for k, v in args.items():
                text = str(v)
                if len(text) > 80:
                    text = text[:77] + "..."
                items.append(f"{k}={text}")
            return " | ".join(items)
        return str(args)[:80]

    def _trim_if_needed(self):
        """输出超过最大行数时截断头部"""
        doc = self.output.document()
        if doc.lineCount() > self.MAX_LINES:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.Down,
                QTextCursor.KeepAnchor,
                doc.lineCount() - self.MAX_LINES,
            )
            cursor.removeSelectedText()

    def _update_status(self):
        doc = self.output.document()
        self.status_label.setText(f"共 {doc.lineCount()} 行")

    def _scroll_to_bottom(self):
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self.output.clear()
        self.status_label.setText("就绪")
