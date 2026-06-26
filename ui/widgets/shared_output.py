"""
SharedOutputWidget — AI 工具执行共享输出面板（增强版）

展示 AI 在后台执行的工具命令及其结果，作为"共享文档"供用户查看。
支持：可折叠卡片、按工具名过滤、关键词搜索、导出 Markdown/TXT。
"""
import json
import os
from datetime import datetime
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea, QComboBox, QLineEdit,
    QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ExecutionRecord:
    """单条工具执行记录数据类"""

    def __init__(
        self,
        name: str,
        args: dict,
        result: str,
        success: bool = True,
        elapsed_ms: int = 0,
        timestamp: Optional[datetime] = None,
    ):
        self.name = name
        self.args = args or {}
        self.result = result or ""
        self.success = success
        self.elapsed_ms = elapsed_ms
        self.timestamp = timestamp or datetime.now()

    @property
    def summary(self) -> str:
        items = []
        for k, v in self.args.items():
            text = str(v)
            if len(text) > 40:
                text = text[:37] + "..."
            items.append(f"{k}={text}")
        return " ".join(items)


class ExecutionCard(QFrame):
    """可折叠的执行记录卡片"""

    def __init__(self, record: ExecutionRecord, parent=None):
        super().__init__(parent)
        self.record = record
        self._collapsed = False
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("executionCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # 头部
        header = QHBoxLayout()
        header.setSpacing(8)

        status = "✅" if self.record.success else "❌"
        self.title_btn = QPushButton(f"▼ {status} {self.record.name} ({self.record.elapsed_ms}ms)")
        self.title_btn.setObjectName("executionCardTitle")
        self.title_btn.setCursor(Qt.PointingHandCursor)
        self.title_btn.setStyleSheet("""
            QPushButton {
                text-align: left; border: none; background: transparent;
                color: #E6EDF3; font-weight: 600; font-size: 12px;
            }
        """)
        self.title_btn.clicked.connect(self._toggle)
        header.addWidget(self.title_btn, 1)

        time_label = QLabel(self.record.timestamp.strftime("%H:%M:%S"))
        time_label.setObjectName("executionCardTime")
        time_label.setStyleSheet("color: #8B949E; font-size: 10px;")
        header.addWidget(time_label)

        layout.addLayout(header)

        # 详情区
        self.detail = QWidget()
        detail_layout = QVBoxLayout(self.detail)
        detail_layout.setContentsMargins(4, 4, 4, 4)
        detail_layout.setSpacing(6)

        args_text = self.record.summary
        if args_text:
            args_label = QLabel(f"<b>参数:</b> {args_text}")
            args_label.setWordWrap(True)
            args_label.setStyleSheet("color: #E6EDF3; font-size: 11px;")
            args_label.setTextFormat(Qt.RichText)
            detail_layout.addWidget(args_label)

        result_text = self.record.result.strip()
        if result_text:
            result_box = QLineEdit()
            result_box.setReadOnly(True)
            display = result_text[:300] + ("..." if len(result_text) > 300 else "")
            result_box.setText(display)
            result_box.setFont(QFont("Cascadia Code", 9))
            result_box.setStyleSheet("""
                QLineEdit {
                    background-color: #0D1117;
                    color: #E6EDF3;
                    border: 1px solid #30363D;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                }
            """)
            detail_layout.addWidget(result_box)

        layout.addWidget(self.detail)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.detail.setVisible(not self._collapsed)
        status = "✅" if self.record.success else "❌"
        arrow = "▶" if self._collapsed else "▼"
        self.title_btn.setText(f"{arrow} {status} {self.record.name} ({self.record.elapsed_ms}ms)")

    def matches(self, text: str, tool_name: Optional[str] = None) -> bool:
        if tool_name and self.record.name != tool_name:
            return False
        if not text:
            return True
        low = text.lower()
        return (
            low in self.record.name.lower()
            or low in json.dumps(self.record.args, ensure_ascii=False).lower()
            or low in self.record.result.lower()
        )


class SharedOutputWidget(QWidget):
    """共享输出面板：按时间顺序显示 AI 工具执行记录（增强版）"""

    record_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: List[ExecutionRecord] = []
        self._cards: List[ExecutionCard] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标题栏 + 工具栏
        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 4, 8, 4)
        header_row.setSpacing(8)

        header = QLabel("🖥 执行输出")
        header.setObjectName("panelHeader")
        header_row.addWidget(header)

        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("sharedOutputFilter")
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.addItem("全部工具", "")
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        header_row.addWidget(self.filter_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("sharedOutputSearch")
        self.search_edit.setPlaceholderText("搜索...")
        self.search_edit.setFixedWidth(140)
        self.search_edit.textChanged.connect(self._apply_filter)
        header_row.addWidget(self.search_edit)

        self.export_btn = QPushButton("导出")
        self.export_btn.setObjectName("fileTreeToolBtn")
        self.export_btn.setFixedSize(40, 24)
        self.export_btn.setToolTip("导出为 Markdown/TXT")
        self.export_btn.clicked.connect(self._on_export)
        header_row.addWidget(self.export_btn)

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

        # 滚动区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setObjectName("sharedOutputScroll")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(6, 6, 6, 6)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # 底部统计
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("fileTreePath")
        layout.addWidget(self.status_label)

    def append_execution(
        self,
        name: str,
        args: dict,
        result: str,
        success: bool = True,
        elapsed_ms: int = 0,
    ):
        """追加一条工具执行记录"""
        record = ExecutionRecord(name, args, result, success, elapsed_ms)
        self._records.append(record)

        # 更新过滤下拉框
        existing = [self.filter_combo.itemData(i) for i in range(self.filter_combo.count())]
        if name not in existing:
            self.filter_combo.addItem(name, name)

        card = ExecutionCard(record, parent=self.container)
        self._cards.append(card)
        self.container_layout.insertWidget(self.container_layout.count() - 1, card)

        self._apply_filter()
        self._scroll_to_bottom()
        self._update_status()
        self.record_count_changed.emit(len(self._records))

    def _apply_filter(self):
        tool_filter = self.filter_combo.currentData() or ""
        search_text = self.search_edit.text().strip()
        visible_count = 0
        for card in self._cards:
            visible = card.matches(search_text, tool_filter or None)
            card.setVisible(visible)
            if visible:
                visible_count += 1
        self._update_status(visible_count)

    def _on_export(self):
        default_name = f"execution_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path, selected = QFileDialog.getSaveFileName(
            self,
            "导出执行输出",
            default_name,
            "Markdown (*.md);;Text (*.txt)",
        )
        if not path:
            return
        try:
            lines = [f"# 执行输出导出\n\n时间: {datetime.now().isoformat()}\n"]
            for record in self._records:
                if not self._is_visible(record):
                    continue
                lines.append(f"## {record.name} @ {record.timestamp.strftime('%H:%M:%S')}")
                lines.append(f"- 状态: {'成功' if record.success else '失败'}")
                lines.append(f"- 耗时: {record.elapsed_ms}ms")
                lines.append(f"- 参数: {json.dumps(record.args, ensure_ascii=False)}")
                lines.append(f"- 结果:\n```\n{record.result}\n```\n")
            content = "\n".join(lines)
            # 如果用户选择 txt，去掉 markdown 标题标记
            if selected == "Text (*.txt)" or path.lower().endswith(".txt"):
                content = content.replace("# ", "").replace("## ", "")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))

    def _is_visible(self, record: ExecutionRecord) -> bool:
        tool_filter = self.filter_combo.currentData() or ""
        search_text = self.search_edit.text().strip()
        if tool_filter and record.name != tool_filter:
            return False
        if not search_text:
            return True
        low = search_text.lower()
        return (
            low in record.name.lower()
            or low in json.dumps(record.args, ensure_ascii=False).lower()
            or low in record.result.lower()
        )

    def _scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_status(self, visible: Optional[int] = None):
        total = len(self._records)
        vis = visible if visible is not None else total
        self.status_label.setText(f"显示 {vis}/{total} 条")

    def clear(self):
        self._records.clear()
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("全部工具", "")
        self.filter_combo.blockSignals(False)
        self.search_edit.clear()
        self.status_label.setText("就绪")
        self.record_count_changed.emit(0)
