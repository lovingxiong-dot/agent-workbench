"""v6/ui/function_page.py — 功能页：工具/MCP/技能/自动化行，支持状态切换。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea

from v6.ui.base import C, font, theme


class FunctionRow(QWidget):
    """单一功能行：图标、名称、描述、操作按钮。"""

    toggled = Signal(str, bool)  # item_id, checked
    clicked = Signal(str)        # item_id

    _COLORS = {"tool": "accent_blue", "mcp": "green", "skill": "purple", "automation": "yellow"}

    def __init__(
        self,
        item_id: str,
        name: str,
        desc: str,
        kind: str,
        enabled: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._id = item_id
        self._kind = kind
        self._enabled = enabled
        self._hover = False
        self.setMouseTracking(True)
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(name, desc)
        self._style()
        theme.changed.connect(self._style)

    def _build(self, name: str, desc: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self._icon = QLabel("●")
        self._icon.setFont(font(12))
        self._name = QLabel(name)
        self._name.setFont(font(12, bold=True))
        self._name.setObjectName("name")
        self._desc = QLabel(desc)
        self._desc.setFont(font(10))
        self._desc.setObjectName("desc")
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(self._name)
        text.addWidget(self._desc)
        layout.addWidget(self._icon)
        layout.addLayout(text, 1)

        if self._kind == "skill":
            self._btn = QPushButton("运行")
            self._btn.setFixedSize(46, 26)
            self._btn.clicked.connect(lambda: self.clicked.emit(self._id))
        else:
            self._btn = QPushButton("ON" if self._enabled else "OFF")
            self._btn.setCheckable(True)
            self._btn.setChecked(self._enabled)
            self._btn.setFixedSize(40, 24)
            self._btn.toggled.connect(lambda checked: self.toggled.emit(self._id, checked))
        layout.addWidget(self._btn)

    def _style(self) -> None:
        bg = C["bg_hover"] if self._hover else "transparent"
        color = C.get(self._COLORS.get(self._kind, "text_primary"), C["text_primary"])
        self._icon.setStyleSheet(f"color: {color};")
        self.setStyleSheet(
            f"FunctionRow {{ background-color: {bg}; border-radius: 6px; }}"
            f"QLabel#name {{ color: {C['text_primary']}; }}"
            f"QLabel#desc {{ color: {C['text_secondary']}; }}"
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; }}"
            f"QPushButton:checked {{ background-color: {C['accent']}; color: {C['text_inverse']}; }}"
        )

    def enterEvent(self, event) -> None:
        self._hover = True
        self._style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._style()
        super().leaveEvent(event)


class FunctionPage(QScrollArea):
    """功能页：工具、MCP、技能、自动化。"""

    tool_toggled = Signal(str, bool)
    mcp_toggled = Signal(str, bool)
    skill_clicked = Signal(str)
    automation_toggled = Signal(str, bool)

    _SECTIONS = [
        ("tools", "工具", "tool", [
            ("web_search", "Web 搜索", "联网检索实时信息"),
            ("code_interpreter", "代码解释器", "执行 Python 脚本"),
            ("file_reader", "文件阅读器", "读取并分析本地文件"),
        ]),
        ("mcps", "MCP 服务", "mcp", [
            ("filesystem", "文件系统 MCP", "访问本地文件系统"),
            ("browser", "浏览器 MCP", "控制浏览器操作"),
        ]),
        ("skills", "技能", "skill", [
            ("refactor", "重构技能", "批量重构代码结构"),
            ("test_gen", "测试生成", "为选中代码生成测试"),
        ]),
        ("automations", "自动化", "automation", [
            ("auto_commit", "自动提交", "生成提交信息并提交"),
            ("sync_docs", "同步文档", "自动同步 README 与注释"),
        ]),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self.setWidget(container)
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(10)
        self._build_from_sections()

    # ── Phase 1-A: Pure Data Binding ──

    def _clear_rows(self) -> None:
        """清除容器中所有现有行，保留容器 widget 本身。"""
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _connect_row(self, row: FunctionRow, kind: str) -> None:
        """按类型连接 FunctionRow 信号。"""
        if kind == "tool":
            row.toggled.connect(self.tool_toggled.emit)
        elif kind == "mcp":
            row.toggled.connect(self.mcp_toggled.emit)
        elif kind == "skill":
            row.clicked.connect(self.skill_clicked.emit)
        else:
            row.toggled.connect(self.automation_toggled.emit)

    def _build_from_sections(self) -> None:
        """从 _SECTIONS 构建默认功能行（独立运行 fallback）。"""
        for sec_id, title, kind, items in self._SECTIONS:
            lbl = QLabel(title)
            lbl.setFont(font(11, bold=True))
            lbl.setStyleSheet(f"color: {C['text_label']}; padding-top: 4px;")
            self._layout.addWidget(lbl)
            for item_id, name, desc in items:
                row = FunctionRow(item_id, name, desc, kind)
                self._connect_row(row, kind)
                self._layout.addWidget(row)
        self._layout.addStretch(1)

    def bind_capabilities(self, capabilities: list) -> None:
        """从 CapabilityViewModel 列表重建功能行。

        替代硬编码 _SECTIONS，由外部数据源调用。
        保留 _SECTIONS 作为独立运行时的 fallback。

        参数 capabilities 应包含具有以下属性的对象：
        - id, name, description, category, is_enabled
        """
        self._clear_rows()
        # 按 category 分组
        groups: dict[str, list] = {}
        for cap in capabilities:
            cat = getattr(cap, 'category', 'tool') or 'tool'
            groups.setdefault(cat, []).append(cap)
        for cat_name, caps in groups.items():
            lbl = QLabel(cat_name.title())
            lbl.setFont(font(11, bold=True))
            lbl.setStyleSheet(f"color: {C['text_label']}; padding-top: 4px;")
            self._layout.addWidget(lbl)
            for cap in caps:
                row = FunctionRow(
                    item_id=cap.id,
                    name=cap.name,
                    desc=getattr(cap, 'description', ''),
                    kind=cat_name,
                    enabled=getattr(cap, 'is_enabled', False),
                )
                self._connect_row(row, cat_name)
                self._layout.addWidget(row)
        self._layout.addStretch(1)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    page = FunctionPage()
    page.tool_toggled.connect(lambda i, e: print("tool", i, e))
    page.skill_clicked.connect(lambda i: print("skill", i))
    page.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(1200, page.close)
    sys.exit(app.exec())
