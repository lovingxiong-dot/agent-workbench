"""
ui_template.py — Agent Workbench 纯 UI 模版（零业务逻辑）

三栏 QSplitter 布局，精确对齐 SVG 设计稿（ui-full-dark.svg 1024×720）：
  左 220px | 中 stretch | 右 400px

交互：
  - 左栏 Tab 切换（功能/会话）+ 会话项动态选中 + 分组折叠
  - 中栏标题栏三按钮 + 聊天区 QGraphicsView 像素级 Demo 内容
  - 右栏标签栏 + 最近文件 + 终端/编辑器占位
  - 左栏/右栏独立折叠展开

纯 UI 层，所有数据为 Demo 硬编码。
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QSplitter, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QSizePolicy,
    QFrame, QScrollArea, QMenu,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QSize, QTimer, QObject
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPalette, QAction, QIcon, QPixmap, QLinearGradient,
)

# ══════════════════════════════════════════════════════════════
# 主题系统（深色/浅色，精确来自 ui-full-dark.svg / ui-full-light.svg）
# ══════════════════════════════════════════════════════════════
_THEMES = {
    "dark": {
        "bg_primary":        "#1a1a2e",
        "bg_sidebar":        "#16213e",
        "bg_right":          "#0f1729",
        "bg_darker":         "#1a1a2e",
        "bg_card":           "#16213e",
        "bg_card_selected":  "#0f3460",
        "bg_file_row":       "#16213e",
        "bg_input":          "#16213e",
        "bg_tab_active":     "#1a1a2e",
        "accent":            "#007acc",
        "accent_blue":       "#569cd6",
        "accent_light":      "#0f3460",
        "border":            "#2a2a4a",
        "text_primary":      "#e0e0e0",
        "text_secondary":    "#a0a0b0",
        "text_muted":        "#6a6a8a",
        "text_inverse":      "#ffffff",
        "text_label":        "#6a6a8a",
        "green":             "#4ec9b0",
        "yellow":            "#dcdcaa",
        "mono_text":         "#d4d4d4",
        "tag_bg":            "#0f3460",
        "gray":              "#858585",
        "purple":            "#c586c0",
        "btn_bg":            "#2a2a4a",
        "btn_hover":         "#3a3a5a",
        "bg_hover":          "#2a2a4a",
        "bg_selected":       "#0f3460",
        "window_shadow":     "#000000",
    },
    "light": {
        "bg_primary":        "#f8f9fa",
        "bg_sidebar":        "#e9ecef",
        "bg_right":          "#ffffff",
        "bg_darker":         "#f1f3f5",
        "bg_card":           "#ffffff",
        "bg_card_selected":  "#e7f1ff",
        "bg_file_row":       "#f8f9fa",
        "bg_input":          "#ffffff",
        "bg_tab_active":     "#ffffff",
        "accent":            "#007acc",
        "accent_blue":       "#007acc",
        "accent_light":      "#e7f1ff",
        "border":            "#dee2e6",
        "text_primary":      "#212529",
        "text_secondary":    "#495057",
        "text_muted":        "#adb5bd",
        "text_inverse":      "#ffffff",
        "text_label":        "#6c757d",
        "green":             "#198754",
        "yellow":            "#856404",
        "mono_text":         "#212529",
        "tag_bg":            "#e7f1ff",
        "gray":              "#adb5bd",
        "purple":            "#7952b3",
        "btn_bg":            "#e9ecef",
        "btn_hover":         "#dee2e6",
        "bg_hover":          "#e9ecef",
        "bg_selected":       "#e7f1ff",
        "window_shadow":     "#adb5bd",
    },
}


class ThemeManager(QObject):
    """全局主题管理器。切换主题时发出 changed 信号，各组件接到后刷新样式。"""
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._name = "dark"
        self.C = dict(_THEMES[self._name])

    def set_theme(self, name: str):
        if name == self._name or name not in _THEMES:
            return
        self._name = name
        self.C.clear()
        self.C.update(_THEMES[name])
        self.changed.emit(name)

    @property
    def name(self) -> str:
        return self._name


theme = ThemeManager()
C = theme.C
# CHAT_W / CONTENT_W / LEFT_MARGIN 迁移为 ChatScene 类属性（支持动态宽度）


def qcolor(hex_str: str) -> QColor:
    return QColor(hex_str)


def svg_icon(svg_str: str, w: int, h: int) -> QPixmap:
    """将 SVG 字符串渲染为 QPixmap。"""
    from PySide6.QtSvg import QSvgRenderer
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    renderer = QSvgRenderer(bytes(svg_str, "utf-8"))
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return pm


def font(size: int, bold: bool = False, family: str = "Segoe UI") -> QFont:
    f = QFont(family, size)
    f.setBold(bold)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


def mono_font(size: int) -> QFont:
    f = QFont("Cascadia Code", size)
    f.setStyleHint(QFont.Monospace)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


# ══════════════════════════════════════════════════════════════
# 左栏：ConversationListPanel（220px）
# ══════════════════════════════════════════════════════════════

class SessionItem(QWidget):
    """单个会话项：精确对齐 ui-full-dark/light.svg。
       卡片 192×48 rx=6；标题/状态/时间按 SVG 坐标 x=24 左对齐。
    """
    clicked = Signal(int)

    def __init__(self, index: int, title: str, preview: str, time_str: str, parent=None):
        super().__init__(parent)
        self._index = index
        self._active = False
        # 48px 放不下三行文字，时间会被裁掉；调整为 54px
        self.setFixedHeight(54)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 5)
        layout.setSpacing(1)

        self._title_lbl = QLabel(title[:24])
        self._title_lbl.setFont(font(12))
        layout.addWidget(self._title_lbl)

        self._preview_lbl = QLabel(preview[:40])
        self._preview_lbl.setFont(font(10))
        layout.addWidget(self._preview_lbl)

        self._time_lbl = QLabel(time_str)
        self._time_lbl.setFont(font(9))
        layout.addWidget(self._time_lbl)

        self._refresh_style()
        theme.changed.connect(self._refresh_style)

    def _refresh_style(self):
        # SVG ui-full-dark.svg line 31-44：active 标题 #e0e0e0、预览 #a0a0b0；inactive 标题 #a0a0b0、预览 #6a6a8a
        if self._active:
            self.setStyleSheet(
                f"SessionItem {{ background-color: {C['bg_card_selected']}; "
                f"border: 0.5px solid {C['accent']}; border-radius: 6px; }}"
            )
            self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        else:
            self.setStyleSheet(
                f"SessionItem {{ background-color: {C['bg_card']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 6px; }}"
                f"SessionItem:hover {{ background-color: {C['bg_hover']}; }}"
            )
            self._title_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._time_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)


class SessionGroup(QWidget):
    """可折叠会话分组：分组头 + 右侧计数。"""
    session_clicked = Signal(int)

    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._name = name
        self._count = count
        self._items: list[SessionItem] = []
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(4)

        # 分组头（SVG: h=20 rx=4 fill=bg_sidebar）
        self._hdr = QWidget()
        self._hdr.setFixedHeight(20)
        self._hdr.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(6)

        self._toggle_btn = QLabel("▼")
        self._toggle_btn.setFont(font(9, bold=True))
        self._toggle_btn.setFixedSize(16, 16)
        self._toggle_btn.setAlignment(Qt.AlignCenter)
        self._toggle_btn.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(self._toggle_btn)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(10, bold=True))
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(self._name_lbl, 1)

        self._cnt_lbl = QLabel(str(self._count))
        self._cnt_lbl.setFont(font(9))  # SVG font-size=9
        self._cnt_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(self._cnt_lbl)

        self._hdr.mousePressEvent = lambda e: self._toggle() if e.button() == Qt.LeftButton else None
        layout.addWidget(self._hdr)

        # 项容器
        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(4, 0, 4, 0)
        self._items_layout.setSpacing(4)
        layout.addLayout(self._items_layout)
        self._refresh_style()

    def _refresh_style(self):
        self._hdr.setStyleSheet(
            f"background-color: {C['bg_sidebar']}; border-radius: 4px;"
        )
        self._toggle_btn.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._cnt_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")

    def add_session(self, item: SessionItem):
        item.clicked.connect(self.session_clicked.emit)
        self._items.append(item)
        self._items_layout.addWidget(item)

    def set_active(self, index: int):
        for it in self._items:
            it.set_active(it._index == index)

    def _toggle(self):
        self._expanded = not self._expanded
        self._toggle_btn.setText("▼" if self._expanded else "▶")
        for it in self._items:
            it.setVisible(self._expanded)


class _FuncRow(QWidget):
    """功能页通用行：自动监听主题变化。"""
    def __init__(self, height: int = 24, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        theme.changed.connect(self._refresh_style)

    def _base_style(self):
        return (
            f"QWidget {{ background-color: {C['tag_bg']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
            f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
        )

    def _refresh_style(self):
        self.setStyleSheet(self._base_style())


class _ToolRow(_FuncRow):
    def __init__(self, name: str, enabled: bool, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._enabled = enabled
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._status = QLabel("开" if self._enabled else "关")
        self._status.setFont(font(9))
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setFixedSize(26, 12)
        hl.addWidget(self._status)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        dot_color = C["green"] if self._enabled else C["gray"]
        name_color = C["text_primary"] if self._enabled else C["text_secondary"]
        status_color = C["green"] if self._enabled else C["gray"]
        self._dot.setStyleSheet(f"color: {dot_color}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {name_color}; background: transparent;")
        self._status.setStyleSheet(
            f"color: {status_color}; background-color: {status_color}33; "
            f"border-radius: 6px; padding: 0 2px;"
        )


class _McpRow(_FuncRow):
    def __init__(self, name: str, connected: bool, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._connected = connected
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._status = QLabel("已连接" if self._connected else "未连接")
        self._status.setFont(font(9))
        self._status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(self._status)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        dot_color = C["green"] if self._connected else C["gray"]
        name_color = C["text_primary"] if self._connected else C["text_secondary"]
        status_color = C["green"] if self._connected else C["gray"]
        self._dot.setStyleSheet(f"color: {dot_color}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {name_color}; background: transparent;")
        self._status.setStyleSheet(f"color: {status_color}; background: transparent;")


class _SkillRow(_FuncRow):
    def __init__(self, name: str, parent=None):
        super().__init__(26, parent)
        self._name = name
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(4)

        self._icon = QLabel("⚡")
        self._icon.setFont(font(11))
        hl.addWidget(self._icon)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        self._icon.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")


class _AutoRow(_FuncRow):
    def __init__(self, name: str, time_str: str, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._time_str = time_str
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._time = QLabel(self._time_str)
        self._time.setFont(font(9))
        self._time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(self._time)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        self._dot.setStyleSheet(f"color: {C['yellow']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._time.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")


class FunctionPage(QWidget):
    """功能页：按 ui-left-function.svg 精确绘制（工具 / MCP / 技能 / 自动化）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(14, 0, 14, 0)
        self._cl.setSpacing(0)

        # 工具区
        tool_box = self._make_section("工具", [
            _ToolRow("run_command", True),
            _ToolRow("grep_files", False),
            _ToolRow("write_file", True),
        ])
        self._cl.addWidget(tool_box)
        self._cl.addSpacing(12)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # MCP 区
        mcp_box = self._make_section("MCP", [
            _McpRow("GitHub", True),
            _McpRow("Notion", False),
        ])
        self._cl.addWidget(mcp_box)
        self._cl.addSpacing(18)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # 技能区（行高 26）
        skill_box = self._make_section("技能", [
            _SkillRow("archive"),
            _SkillRow("handoff"),
            _SkillRow("gitops"),
        ], row_spacing=4)
        self._cl.addWidget(skill_box)
        self._cl.addSpacing(18)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # 自动化区
        auto_box = self._make_section("自动化", [
            _AutoRow("每日日报", "08:00"),
        ])
        self._cl.addWidget(auto_box)

        self._cl.addStretch()
        self._scroll.setWidget(content)
        layout.addWidget(self._scroll)
        self._refresh_theme()

    def _make_section(self, title: str, rows: list, row_spacing: int = 4) -> QWidget:
        box = QWidget()
        vl = QVBoxLayout(box)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)
        hdr = self._section_header(title)
        hdr.setObjectName("func_section_header")
        vl.addWidget(hdr)
        for r in rows:
            vl.addWidget(r)
            vl.setSpacing(row_spacing)
        return box

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {C['bg_sidebar']}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        for hdr in self.findChildren(QLabel, "func_section_header"):
            hdr.setStyleSheet(
                f"color: {C['text_label']}; font-size: 9px; font-weight: 600; "
                f"letter-spacing: 0.5px; padding: 0 0 2px 0; background: transparent;"
            )
        for sep in self.findChildren(QFrame, "func_sep"):
            sep.setStyleSheet(f"background-color: {C['border']};")

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font(9, bold=True))
        return lbl

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("func_sep")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        return sep


class LeftPanel(QWidget):
    """左栏面板：Tab切换 + 分组会话列表 + 底部控制 + 主题切换。"""
    session_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._current_tab = "会话"
        self._groups: list[SessionGroup] = []
        self._all_items: list[SessionItem] = []
        self._active_idx = 0
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ── Tab 行（SVG: 92×22 rx=6, active=#007acc 未选中=bg_tab 或透明）──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)

        self._func_btn = self._make_tab_btn("功能", active=False)
        self._sess_btn = self._make_tab_btn("会话", active=True)
        self._func_btn.clicked.connect(lambda: self._switch_tab("功能"))
        self._sess_btn.clicked.connect(lambda: self._switch_tab("会话"))

        tab_row.addWidget(self._func_btn, 1)
        tab_row.addWidget(self._sess_btn, 1)
        layout.addLayout(tab_row)

        # ── 工具行（按 Tab 切换）──
        self._tool_stack = QStackedWidget()
        self._tool_stack.setFixedHeight(22)

        # 功能页工具行（SVG ui-left-function.svg line 9-13: 搜索 156×22 + + 30×22）
        func_tools = QWidget()
        ftl = QHBoxLayout(func_tools)
        ftl.setContentsMargins(0, 0, 0, 0)
        ftl.setSpacing(6)
        self._func_search = QLineEdit()
        self._func_search.setPlaceholderText("🔍")
        self._func_search.setFixedSize(156, 22)
        self._func_add = QPushButton("+")
        self._func_add.setFixedSize(30, 22)
        self._func_add.setCursor(Qt.PointingHandCursor)
        self._func_add.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['accent']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        ftl.addWidget(self._func_search)
        ftl.addWidget(self._func_add)
        ftl.addStretch()
        self._tool_stack.addWidget(func_tools)

        # 会话页工具行（SVG ui-full-dark.svg line 18-23: 28×22 / 124×22 / 28×22）
        sess_tools = QWidget()
        stl = QHBoxLayout(sess_tools)
        stl.setContentsMargins(0, 0, 0, 0)
        stl.setSpacing(6)
        self._search_btn = self._make_small_btn("🔍", 28, 22, C["text_secondary"], 10)
        self._new_btn = self._make_new_btn()
        self._more_btn = self._make_small_btn("...", 28, 22, C["text_muted"], 11)
        stl.addWidget(self._search_btn)
        stl.addWidget(self._new_btn)
        stl.addWidget(self._more_btn)
        self._tool_stack.addWidget(sess_tools)

        layout.addWidget(self._tool_stack)

        # 工具行下分隔线（SVG: y=76）
        self._sep1 = QFrame()
        self._sep1.setFrameShape(QFrame.HLine)
        self._sep1.setFixedHeight(1)
        layout.addWidget(self._sep1)

        # ── 内容区（QStackedWidget：功能页 / 会话列表）──
        self._stack = QStackedWidget()

        # 功能页
        func_page = FunctionPage()
        self._stack.addWidget(func_page)

        # 会话列表（可滚动）
        self._sess_scroll = QScrollArea()
        self._sess_scroll.setWidgetResizable(True)
        self._sess_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sess_widget = QWidget()
        self._sess_layout = QVBoxLayout(sess_widget)
        self._sess_layout.setContentsMargins(0, 0, 0, 0)
        self._sess_layout.setSpacing(6)
        self._sess_layout.addStretch()
        self._sess_scroll.setWidget(sess_widget)
        self._stack.addWidget(self._sess_scroll)

        self._stack.setCurrentIndex(1)
        layout.addWidget(self._stack, 1)

        # ── 底部控制（SVG: 分隔线 y=700 + 主题/设置按钮 h=12）──
        self._sep2 = QFrame()
        self._sep2.setFrameShape(QFrame.HLine)
        self._sep2.setFixedHeight(1)
        layout.addWidget(self._sep2)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        self._theme_btn = self._make_bottom_btn("🌙")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._settings_btn = self._make_bottom_btn("⚙")
        bottom_row.addWidget(self._theme_btn)
        bottom_row.addWidget(self._settings_btn)
        bottom_row.addStretch()
        layout.addLayout(bottom_row)

        # 填充 Demo 会话数据
        self._populate_sessions()

        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        self._sep2.setStyleSheet(f"background-color: {C['border']};")
        self._sess_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {C['bg_sidebar']}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        # 功能页搜索框
        self._func_search.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 0 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border: 0.5px solid {C['accent']}; }}"
        )
        # 功能页 + 按钮
        self._func_add.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['accent']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        # 会话页工具行三按钮
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 10px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._new_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._more_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_muted']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        # 底部按钮
        self._theme_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._settings_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        # 刷新当前 Tab 按钮样式
        self._switch_tab(self._current_tab)

    def _toggle_theme(self):
        new_theme = "light" if theme.name == "dark" else "dark"
        theme.set_theme(new_theme)
        self._theme_btn.setText("☀️" if new_theme == "light" else "🌙")

    def _make_tab_btn(self, text: str, active: bool) -> QPushButton:
        """Tab 标签：全透明无背景，仅文字 + 选中态底部指示条。"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(92, 22)
        fg = C["accent"] if active else C["text_muted"]
        fw = 600 if active else 400
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {fg}; "
            f"border: none; padding: 2px 8px; "
            f"font-size: 11px; font-weight: {fw}; }}"
            f"QPushButton:hover {{ color: {C['text_primary']}; }}"
        )
        return btn

    def _make_small_btn(self, text: str, w: int, h: int, color: str = None, font_size: int = 10) -> QPushButton:
        """小图标按钮（SVG ui-full-dark.svg line 18-23）：bg_primary 背景 + border 边框圆角卡片。"""
        btn = QPushButton(text)
        btn.setFixedSize(w, h)
        btn.setCursor(Qt.PointingHandCursor)
        fg = color if color else C["text_secondary"]
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {fg}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: {font_size}px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _make_new_btn(self) -> QPushButton:
        """新会话按钮（SVG ui-full-dark.svg line 20-21）：bg_primary + accent 边框，124×22。"""
        btn = QPushButton("+ 新会话")
        btn.setFixedSize(124, 22)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _make_bottom_btn(self, text: str) -> QPushButton:
        """底部小标签（SVG ui-full-dark.svg line 70-73）：btn_bg 背景、text_secondary 字。"""
        btn = QPushButton(text)
        btn.setFixedSize(32, 12)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _switch_tab(self, tab: str):
        self._current_tab = tab
        is_func = (tab == "功能")
        self._stack.setCurrentIndex(0 if is_func else 1)
        self._tool_stack.setCurrentIndex(0 if is_func else 1)
        self._func_btn.setChecked(is_func)
        self._sess_btn.setChecked(not is_func)
        for btn, active in [(self._func_btn, is_func), (self._sess_btn, not is_func)]:
            fg = C["accent"] if active else C["text_muted"]
            fw = 600 if active else 400
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {fg}; "
                f"border: none; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ color: {C['text_primary']}; }}"
            )

    def _populate_sessions(self):
        """填充 Demo 分组会话数据（对应 SVG 设计稿）。"""
        g1 = SessionGroup("agent_workbench", 3)
        sessions_g1 = [
            ("v4 架构升级", "✓ 三个文件已修改并测试通过", "20:15"),
            ("量化策略回测", "△ 等待确认执行计划", "18:42"),
            ("API 接口设计", "等待第一条消息...", "15:30"),
        ]
        for i, (title, preview, t) in enumerate(sessions_g1):
            item = SessionItem(i, title, preview, t)
            g1.add_session(item)
            self._all_items.append(item)

        g2 = SessionGroup("全局会话", 5)
        sessions_g2 = [
            ("通用问答", "如何配置 Python 环境？", "14:20"),
            ("代码片段咨询", "Python 装饰器用法", "13:08"),
            ("翻译任务", "将 README 翻译为英文", "10:45"),
        ]
        for i, (title, preview, t) in enumerate(sessions_g2, start=3):
            item = SessionItem(i, title, preview, t)
            g2.add_session(item)
            self._all_items.append(item)

        self._groups = [g1, g2]
        for g in reversed(self._groups):
            self._sess_layout.insertWidget(self._sess_layout.count() - 1, g)
        for g in self._groups:
            g.session_clicked.connect(self._on_session_clicked)
        self._select_session(0)

    def _on_session_clicked(self, idx: int):
        self._select_session(idx)
        self.session_selected.emit(idx)

    def _select_session(self, idx: int):
        self._active_idx = idx
        for g in self._groups:
            g.set_active(idx)


# ══════════════════════════════════════════════════════════════
# 聊天区 QGraphicsItem 元素（像素级对齐 SVG）
# ══════════════════════════════════════════════════════════════

class ChatItem(QGraphicsItem):
    """所有聊天元素的基类。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._h = 0.0

    def height(self) -> float:
        return self._h

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class UserBubble(ChatItem):
    """SVG: x=240 y=56 w=148 h=26 rx=8 fill=#007acc, text x=365 text-anchor=end"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fm = QFontMetrics(font(11))
        tw = fm.horizontalAdvance(text)
        bw = max(60.0, min(float(ChatScene.CONTENT_W), tw + 24.0))
        bh = 26.0
        bx = ChatScene.CHAT_W - 14 - bw  # RIGHT_PAD=14
        self._brect = QRectF(bx, 0, bw, bh)
        self._trect = QRectF(bx + 12, 0, bw - 24, bh)
        self._h = bh + 8
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self._brect, 8, 8)
        painter.fillPath(path, qcolor(C["accent"]))
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_inverse"]))
        painter.drawText(self._trect, Qt.AlignRight | Qt.AlignVCenter, self._text)


class FoldBlock(ChatItem):
    """可折叠块。SVG收起: rx=4 h=22 fill=#16213e；展开: header h=20 fill=#1a1a2e + body。"""
    FOLD_H = 22.0
    HEADER_H = 20.0
    RX = 4.0

    def __init__(self, title: str, status: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._status = status
        self._expanded = False
        self._body_h = 0.0
        self._body_items: list[QGraphicsItem] = []
        self._h = self.FOLD_H + 4
        self.setAcceptHoverEvents(True)

    def set_body(self, items: list[QGraphicsItem], h: float):
        self._body_items = items
        self._body_h = h
        for item in items:
            item.setParentItem(self)
            item.setVisible(False)

    def toggle(self):
        if self._expanded:
            self._expanded = False
            self._h = self.FOLD_H + 4
            for item in self._body_items:
                item.setVisible(False)
        else:
            self._expanded = True
            self._h = self.HEADER_H + self._body_h + 4
            for item in self._body_items:
                item.setVisible(True)
        self.prepareGeometryChange()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y0 = 0.0

        if self._expanded:
            # 外层卡片（dark bg_card #16213e; light bg_card #ffffff）
            outer = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H + self._body_h)
            p = QPainterPath()
            p.addRoundedRect(outer, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))

            # Header bar
            hr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H)
            hp = QPainterPath()
            hp.addRoundedRect(hr, self.RX, self.RX)
            hp.addRect(ChatScene.LEFT_MARGIN, y0 + self.HEADER_H - self.RX, ChatScene.CONTENT_W, self.RX)
            painter.fillPath(hp, qcolor(C["bg_darker"]))

            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 10, y0 + 10, down=True)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)
        else:
            fr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.FOLD_H)
            p = QPainterPath()
            p.addRoundedRect(fr, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))
            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 12, y0 + 11, down=False)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)

    def _draw_chevron(self, painter, cx, cy, down):
        pen = QPen(qcolor(C["accent_blue"]), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath()
        if down:
            path.moveTo(cx - 2, cy - 1); path.lineTo(cx, cy + 2); path.lineTo(cx + 2, cy - 1)
        else:
            path.moveTo(cx - 1, cy - 2); path.lineTo(cx + 2, cy); path.lineTo(cx - 1, cy + 2)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
            if hr.contains(event.pos()):
                self.toggle()
                event.accept()
                return
        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
        self.setCursor(Qt.PointingHandCursor if hr.contains(event.pos()) else Qt.ArrowCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class ToolEntry(ChatItem):
    """SVG: 4px左bar + ✓ + 工具名 + 耗时 + ▶参数"""
    def __init__(self, name: str, elapsed: str, success: bool = True, parent=None):
        super().__init__(parent)
        self._name = name
        self._elapsed = elapsed
        self._icon = "✓" if success else "✗"
        self._success = success
        self._h = 16
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 1.0
        # 4px bar（SVG dark #2a2a4a=border; light #e9ecef=bg_sidebar）
        bar_color = C["border"] if theme.name == "dark" else C["bg_sidebar"]
        br = QRectF(ChatScene.LEFT_MARGIN + 10, y, 4, 14)
        bp = QPainterPath()
        bp.addRoundedRect(br, 2, 2)
        painter.fillPath(bp, qcolor(bar_color))
        # icon：运行时读取当前主题色，避免实例化时固定深色
        icon_color = C["green"] if self._success else "#f14c4c"
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(icon_color))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 22, y + 11), self._icon)
        # name
        painter.setPen(qcolor(C["mono_text"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 33, y + 11), self._name)
        # elapsed
        painter.setFont(mono_font(9))
        painter.setPen(qcolor(C["text_muted"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 134, y + 11), self._elapsed)
        # args chevron
        painter.setPen(qcolor(C["accent_blue"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 189, y + 11), "▶ 参数")


class PhasePanel(ChatItem):
    """阶段面板：rx=8卡片 + 4px accent bar + header + body。"""
    HEADER_H = 24.0
    RX = 8.0
    # 颜色键（避免类定义时捕获固定颜色）
    PHASE_COLORS = {
        "analyze": "accent_blue", "execute": "yellow",
        "archive": "green", "verify": "purple",
    }

    def __init__(self, title: str, accent_key: str, body_items: list = None, body_h: float = 0, parent=None):
        super().__init__(parent)
        self._title = title
        self._accent_key = accent_key
        self._body_h = body_h
        self._h = self.HEADER_H + body_h + 16
        if body_items:
            for item in body_items:
                item.setParentItem(self)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4.0
        card_h = self.HEADER_H + self._body_h + 8

        # 卡片（dark bg_sidebar #16213e; light bg_card #ffffff）
        cr = QRectF(ChatScene.LEFT_MARGIN, y, ChatScene.CONTENT_W, card_h)
        cp = QPainterPath()
        cp.addRoundedRect(cr, self.RX, self.RX)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        pen = QPen(qcolor(C["border"]), 0.5)
        painter.setPen(pen)
        painter.drawPath(cp)

        # accent bar：运行时读取当前主题色
        accent = C.get(self._accent_key, C["accent_blue"])
        ar = QRectF(ChatScene.LEFT_MARGIN, y, 4, card_h)
        ap = QPainterPath()
        ap.addRoundedRect(ar, 2, 2)
        painter.fillPath(ap, qcolor(accent))

        # header
        hr = QRectF(ChatScene.LEFT_MARGIN + 4, y, ChatScene.CONTENT_W - 4, self.HEADER_H)
        hp = QPainterPath()
        hp.addRoundedRect(hr, 6, 6)
        hp.addRect(ChatScene.LEFT_MARGIN + 4, y + self.HEADER_H - 6, ChatScene.CONTENT_W - 4, 6)
        painter.fillPath(hp, qcolor(C["bg_darker"]))
        painter.setPen(qcolor(C["text_primary"]))
        painter.setFont(font(12, bold=True))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 14, y + 17), self._title)


class BulletItem(ChatItem):
    """● + 文本"""
    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        self._h = 20

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        color = qcolor(C[self._color_key])
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(ChatScene.LEFT_MARGIN + 13, 14), 3, 3)
        painter.setFont(font(10))
        painter.setPen(color)
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 23, 17), self._text)


class StepItem(ChatItem):
    """执行步骤：✓/⟳/○ + 名称 + 详情"""
    ICONS = {"done": ("✓", "green"), "running": ("⟳", "yellow"),
             "pending": ("○", "text_muted"), "fail": ("✗", "#f14c4c")}

    def __init__(self, status: str, name: str, detail: str = "", parent=None):
        super().__init__(parent)
        self._icon, self._ic_key = self.ICONS.get(status, ("○", "text_muted"))
        self._name = name
        self._detail = detail
        self._h = 20

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4
        # 图标颜色运行时解析
        ic = C.get(self._ic_key, C["text_muted"]) if self._ic_key.startswith("#") is False else self._ic_key
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(ic))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 14, y + 12), self._icon)
        painter.setFont(font(10))
        painter.setPen(qcolor(C["text_primary"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 29, y + 12), self._name)
        if self._detail:
            painter.setFont(font(9))
            painter.setPen(qcolor(C["text_muted"]))
            fm = QFontMetrics(font(10))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 29 + fm.horizontalAdvance(self._name) + 8, y + 12), self._detail)


class TextItem(ChatItem):
    """纯文本行。"""
    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        self._h = 22

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(font(10))
        painter.setPen(qcolor(C[self._color_key]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 14, 15), self._text)


class SystemCard(ChatItem):
    """居中系统卡片。"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fm = QFontMetrics(font(11))
        lines = text.split("\n")
        lh = fm.height() + 2
        max_w = max(fm.horizontalAdvance(l) for l in lines)
        cw = min(ChatScene.CONTENT_W, max_w + 28 + 4)
        ch = len(lines) * lh + 20
        self._crect = QRectF((ChatScene.CHAT_W - cw) / 2, 4, cw, ch)
        self._lines = lines
        self._lh = lh
        self._h = ch + 8

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        cp = QPainterPath()
        cp.addRoundedRect(self._crect, 8, 8)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        painter.setPen(QPen(qcolor(C["border"]), 0.5))
        painter.drawPath(cp)
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_primary"]))
        y = self._crect.top() + 10
        for line in self._lines:
            painter.drawText(QPointF(self._crect.left() + 14, y + self._lh - 3), line)
            y += self._lh


# ══════════════════════════════════════════════════════════════
# 聊天场景
# ══════════════════════════════════════════════════════════════

class ChatScene(QGraphicsScene):
    CHAT_W = 402
    LEFT_MARGIN = 20
    CONTENT_W = 362

    @classmethod
    def set_width(cls, w: float):
        cls.CHAT_W = w
        cls.CONTENT_W = max(120.0, w - 40)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._y = 8.0
        self._items: list = []
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))

    def add_chat_item(self, item: ChatItem) -> ChatItem:
        self.addItem(item)
        item.setPos(0, self._y)
        self._y += item.height() + 8
        self._items.append(item)
        self._update_rect()
        return item

    def _update_rect(self):
        h = max(self._y + 40, 720)
        self.setSceneRect(QRectF(0, 0, ChatScene.CHAT_W, h))

    def clear_items(self):
        super().clear()
        self._items.clear()
        self._y = 8.0

    def refresh(self):
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))
        for item in self._items:
            item.update()


# ══════════════════════════════════════════════════════════════
# 标题栏
# ══════════════════════════════════════════════════════════════

class HeaderBar(QWidget):
    expand_toggled = Signal()
    search_clicked = Signal()
    more_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 双行标题（SVG: title y=16, env y=30）
        title_block = QVBoxLayout()
        title_block.setContentsMargins(20, 4, 0, 4)
        title_block.setSpacing(2)

        self._title_lbl = QLabel("v4 架构升级")
        self._title_lbl.setFont(font(12))
        title_block.addWidget(self._title_lbl)

        self._env_lbl = QLabel("F:\\Agent\\agent_workbench")
        self._env_lbl.setFont(font(10))
        title_block.addWidget(self._env_lbl)
        layout.addLayout(title_block, 1)

        # 垂直分隔线（SVG: x1=331）
        self._vsep = QLabel()
        self._vsep.setFixedSize(1, 24)
        layout.addWidget(self._vsep)
        layout.addSpacing(6)

        # 右上角三键容器：spacing=2 紧凑排列
        self._btn_block = QWidget()
        btn_hl = QHBoxLayout(self._btn_block)
        btn_hl.setContentsMargins(0, 0, 0, 0)
        btn_hl.setSpacing(2)

        self._search_btn = self._icon_btn("搜索")
        self._search_btn.clicked.connect(self.search_clicked.emit)
        self._more_btn = self._icon_btn("更多操作")
        self._more_btn.clicked.connect(self.more_clicked.emit)
        self._expand_btn = self._icon_btn("折叠右侧面板")
        self._expand_btn.clicked.connect(self.expand_toggled.emit)

        btn_hl.addWidget(self._search_btn)
        btn_hl.addWidget(self._more_btn)
        btn_hl.addWidget(self._expand_btn)
        layout.addWidget(self._btn_block)
        layout.addSpacing(12)
        self._refresh_theme()

    def _icon_btn(self, tooltip: str) -> QPushButton:
        """18×22 方形图标按钮：SVG fill=#2a2a4a rx=4。"""
        btn = QPushButton()
        btn.setFixedSize(18, 22)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        lbl = QLabel(btn)
        lbl.setObjectName("icon_lbl")
        lbl.move(0, 1)
        return btn

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._env_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._vsep.setStyleSheet(f"background-color: {C['border']};")

        stroke = C['text_secondary'] if theme.name == "dark" else C['text_label']
        # Apple 风格搜索图标: 偏心圆 + 粗短手柄
        search_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
            <circle cx="8" cy="7.5" r="4.5" fill="none" stroke="{stroke}" stroke-width="1.4"/>
            <line x1="11.2" y1="10.7" x2="15.5" y2="15" stroke="{stroke}" stroke-width="1.8" stroke-linecap="round"/>
        </svg>'''
        more_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
            <circle cx="6" cy="10" r="1.2" fill="{stroke}"/>
            <circle cx="10" cy="10" r="1.2" fill="{stroke}"/>
            <circle cx="14" cy="10" r="1.2" fill="{stroke}"/>
        </svg>'''
        # 右侧折叠图标: 窗格框体 + 纵向分割线，表达"右侧面板可折叠"
        expand_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
            <rect x="2" y="3" width="14" height="12" rx="2" fill="none" stroke="{stroke}" stroke-width="1.5"/>
            <line x1="12" y1="5.5" x2="12" y2="12.5" stroke="{stroke}" stroke-width="1.2" stroke-linecap="round"/>
        </svg>'''
        for btn, svg in [(self._search_btn, search_svg),
                         (self._more_btn, more_svg),
                         (self._expand_btn, expand_svg)]:
            lbl = btn.findChild(QLabel, "icon_lbl")
            if lbl:
                lbl.setPixmap(svg_icon(svg, 18, 22))
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {C['btn_bg']}; border: none; border-radius: 4px; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )


# ══════════════════════════════════════════════════════════════
# 输入区
# ══════════════════════════════════════════════════════════════

class InputArea(QWidget):
    send_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 8, 20, 8)
        root.setSpacing(6)

        # ── 输入框（SVG: x=241 y=660 w=362 h=56 rx=8；发送按钮叠在内部右侧）──
        input_container = QWidget()
        input_container.setFixedHeight(56)
        input_container.setStyleSheet("background-color: transparent;")
        self._text_edit = QTextEdit(input_container)
        self._text_edit.setPlaceholderText("输入 \"/\" 快速使用技能")
        self._text_edit.setGeometry(0, 0, 362, 56)
        self._text_edit.setFont(font(11))

        # ── 发送按钮 ──
        self._send_btn = QPushButton(input_container)
        self._send_btn.setFixedSize(24, 24)
        self._send_btn.move(330, 16)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        send_lbl = QLabel(self._send_btn)
        send_lbl.setObjectName("send_icon")
        send_lbl.move(0, 0)
        self._send_btn.clicked.connect(self.send_clicked.emit)

        root.addWidget(input_container)

        # ── 标签行（SVG: + r=10 at x=257,y=702; 模式 w=62 x=277; 模型 w=76 x=345）──
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(0, 0, 0, 0)
        tag_row.setSpacing(8)

        self._skill_btn = QPushButton("+")
        self._skill_btn.setFixedSize(20, 20)
        self._skill_btn.setCursor(Qt.PointingHandCursor)
        tag_row.addWidget(self._skill_btn)

        self._mode_tag = self._make_tag("模式", "ask", 62)
        self._model_tag = self._make_tag("模型", "flash", 76)
        tag_row.addWidget(self._mode_tag)
        tag_row.addWidget(self._model_tag)
        tag_row.addStretch()

        root.addLayout(tag_row)
        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._text_edit.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 8px; "
            f"padding: 8px 36px 8px 14px; font-size: 11px; }}"
        )
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background-color: #34d399; border-radius: 8px; border: none; }}"
            f"QPushButton:hover {{ background-color: #2ecc71; }}"
        )
        send_lbl = self._send_btn.findChild(QLabel, "send_icon")
        if send_lbl:
            send_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path d="M 12 7 L 16 15 L 13 15 L 13 19 L 11 19 L 11 15 L 8 15 Z" fill="#0f1729"/>
            </svg>'''
            send_lbl.setPixmap(svg_icon(send_svg, 24, 24))
        self._skill_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 10px; font-size: 14px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        for tag in (self._mode_tag, self._model_tag):
            tag.setStyleSheet(
                f"QWidget {{ background-color: {C['tag_bg']}; border: 0.5px solid {C['border']}; border-radius: 6px; }}"
                f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
            )

    def _make_tag(self, label: str, value: str, width: int) -> QWidget:
        """SVG: tag fill=tag_bg stroke=border rx=6, w=62/76 h=22。"""
        tag = QWidget()
        tag.setFixedSize(width, 22)
        tag.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(tag)
        hl.setContentsMargins(4, 0, 4, 0)
        hl.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(font(9))
        lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(lbl)

        val = QLabel(value)
        val.setFont(font(10))
        val.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(val)

        chev = QLabel("▾")
        chev.setFont(font(9))
        chev.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(chev)
        hl.addStretch()
        return tag


# ══════════════════════════════════════════════════════════════
# 聊天区
# ══════════════════════════════════════════════════════════════

class ChatArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialized = False
        self._setup_ui()
        self._populate_demo()
        self._initialized = True
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        self._header = HeaderBar()
        layout.addWidget(self._header)

        # 标题栏下分隔线（SVG: y=40）
        self._sep1 = QFrame()
        self._sep1.setFixedHeight(1)
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep1)

        # QGraphicsView 聊天区
        self._view = QGraphicsView()
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._view.setFrameShape(QGraphicsView.NoFrame)
        self._view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._view.setStyleSheet(
            "QGraphicsView { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        self._scene = ChatScene()
        self._view.setScene(self._scene)
        layout.addWidget(self._view, 1)

        # 输入区分隔线（SVG: y=652）
        self._sep2 = QFrame()
        self._sep2.setFixedHeight(1)
        self._sep2.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep2)

        # 输入区
        self._input = InputArea()
        layout.addWidget(self._input)
        self.setStyleSheet(f"background-color: {C['bg_primary']};")

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        self._sep2.setStyleSheet(f"background-color: {C['border']};")
        self._view.setStyleSheet(
            "QGraphicsView { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        self._scene.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._initialized:
            new_w = self._view.viewport().width() if self._view.viewport() else self.width()
            if abs(new_w - ChatScene.CHAT_W) > 4:
                self._rebuild_content(new_w)

    def _rebuild_content(self, width: float = None):
        """清除并重绘聊天区内容，适配新宽度。"""
        if width is not None:
            ChatScene.set_width(width)
        self._scene.clear_items()
        self._populate_demo()
        self._scene.refresh()

    def _populate_demo(self):
        """填充 Demo 聊天内容（精确对应 ui-chat-area.svg）。"""
        scene = self._scene

        # 用户气泡
        scene.add_chat_item(UserBubble("帮我分析当前项目"))

        # 思考过程折叠（收起）
        scene.add_chat_item(FoldBlock("思考过程", "[5/7 已完成]"))

        # 工具执行折叠（展开）
        tools = FoldBlock("工具执行", "[3 工具 · 共 2.1s]")
        entry1 = ToolEntry("run_command", "0.8s")
        entry2 = ToolEntry("grep_refs", "0.3s")
        entry3 = ToolEntry("pytest", "1.0s")
        # 定位子项
        entry1.setPos(0, tools.HEADER_H + 2)
        entry2.setPos(0, tools.HEADER_H + 18)
        entry3.setPos(0, tools.HEADER_H + 34)
        tools.set_body([entry1, entry2, entry3], 50)
        tools.toggle()  # 展开
        scene.add_chat_item(tools)

        # 内部命令输出折叠（收起）
        scene.add_chat_item(FoldBlock("内部命令输出", "[212 行]"))

        # 📋 分析结果面板
        b1 = BulletItem("项目采用 v4 单轨事件总线架构")
        b2 = BulletItem("193/193 全量测试通过")
        b1.setPos(0, PhasePanel.HEADER_H + 6)
        b2.setPos(0, PhasePanel.HEADER_H + 26)
        scene.add_chat_item(PhasePanel("📋 分析结果", "accent_blue", [b1, b2], 48))

        # 📝 执行计划面板
        s1 = StepItem("done", "修改 v4/events.py", "新增 model 字段")
        s2 = StepItem("running", "修改 v4/main_window.py", "模型下拉框 + 持久化")
        s3 = StepItem("pending", "运行全量测试", "pytest tests/ -v")
        s1.setPos(0, PhasePanel.HEADER_H + 6)
        s2.setPos(0, PhasePanel.HEADER_H + 26)
        s3.setPos(0, PhasePanel.HEADER_H + 46)
        scene.add_chat_item(PhasePanel("📝 执行计划", "yellow", [s1, s2, s3], 68))

        # ✅ 完成报告面板
        t1 = TextItem("v4.0.5-alpha 存档完成")
        t1.setPos(0, PhasePanel.HEADER_H + 6)
        scene.add_chat_item(PhasePanel("✅ 完成报告", "green", [t1], 30))

        # 滚动到底部
        QTimer.singleShot(100, lambda: self._view.verticalScrollBar().setValue(
            self._view.verticalScrollBar().maximum()))


# ══════════════════════════════════════════════════════════════
# 右栏（400px）
# ══════════════════════════════════════════════════════════════

class TabButton(QWidget):
    """右栏标签按钮：标签文本与关闭圆钮共用同一背景，实现 SVG 中的透明圆框高亮效果。
       SVG: rect rx=6 h=24; close circle r=5 fill=tab_bg 与标签同色。
    """
    clicked = Signal()
    close_clicked = Signal()

    def __init__(self, text: str, width: int, active: bool = False, closable: bool = True, parent=None):
        super().__init__(parent)
        self._text = text
        self._active = active
        self._closable = closable
        self.setFixedSize(width, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        self._lbl = QLabel(self._text, self)
        self._lbl.setFont(font(10))
        self._lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._lbl.setStyleSheet("background: transparent;")
        self._lbl.setGeometry(10, 0, self.width() - 28, 24)

        if self._closable:
            self._close = QPushButton("✕", self)
            self._close.setFixedSize(10, 10)
            self._close.setFont(font(9))
            self._close.setCursor(Qt.PointingHandCursor)
            self._close.setGeometry(self.width() - 17, 7, 10, 10)
            self._close.clicked.connect(self.close_clicked.emit)
        else:
            self._close = None
        self._refresh_style()

    def _refresh_style(self):
        is_dark = theme.name == "dark"
        bg = (C["bg_darker"] if is_dark else C["bg_card"]) if self._active else (C["bg_right"] if is_dark else C["bg_darker"])
        fg = C["text_primary"] if self._active else C["text_secondary"]
        fw = 600 if self._active else 500
        self.setStyleSheet(f"TabButton {{ background-color: {bg}; border-radius: 6px; }}")
        self._lbl.setStyleSheet(f"color: {fg}; background: transparent; font-weight: {fw};")
        if self._close:
            self._close.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {C['text_muted']}; "
                f"border-radius: 5px; font-size: 9px; border: none; }}"
                f"QPushButton:hover {{ color: {C['text_primary']}; }}"
            )

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._close is None or not self._close.geometry().contains(event.pos()):
                self.clicked.emit()
        super().mousePressEvent(event)


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self._active_tab = 0
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标签栏（SVG dark h=28 fill=#0f1729; light fill=#f1f3f5）──
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(28)
        tb_layout = QHBoxLayout(self._tab_bar)
        tb_layout.setContentsMargins(8, 2, 8, 2)
        tb_layout.setSpacing(2)

        # SVG: add btn circle r=7 (d=14) fill=#2a2a4a / #e9ecef
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(14, 14)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tb_layout.addWidget(self._add_btn)

        # 标签按钮（SVG ui-full-dark.svg line 198-214）
        # 宽度：v4 架构 86 / 终端 74 / 文件编辑器 100 / 浏览器 按内容；第一个不可关闭
        tab_defs = [("v4 架构", 86, False), ("终端", 74, True), ("文件编辑器", 100, True), ("浏览器", 74, True)]
        self._tab_btns: list[TabButton] = []
        for i, (name, width, closable) in enumerate(tab_defs):
            btn = TabButton(name, width, active=(i == 0), closable=closable)
            btn.clicked.connect(lambda idx=i: self._switch_tab(idx))
            btn.close_clicked.connect(lambda idx=i: self._on_close_tab(idx))
            tb_layout.addWidget(btn)
            self._tab_btns.append(btn)

        # SVG: 搜索按钮 x=930 y=6 w=16 h=16 rx=3 fill=#2a2a4a / #e9ecef
        self._search_btn = QPushButton("🔍")
        self._search_btn.setFixedSize(16, 16)
        self._search_btn.setCursor(Qt.PointingHandCursor)
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tb_layout.addSpacing(4)
        tb_layout.addWidget(self._search_btn)

        tb_layout.addStretch()

        # 窗口控制按钮容器（由 MainWindow 注入回调）
        self._win_btns = QWidget()
        win_hl = QHBoxLayout(self._win_btns)
        win_hl.setContentsMargins(0, 0, 8, 0)
        win_hl.setSpacing(2)
        self._win_hl = win_hl
        tb_layout.addWidget(self._win_btns)

        layout.addWidget(self._tab_bar)

        # 标签栏下分隔线
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep)

        # ── 内容区（QStackedWidget）──
        self._stack = QStackedWidget()

        # Tab0: v4 架构（最近文件）
        self._tab0 = QWidget()
        t0l = QVBoxLayout(self._tab0)
        t0l.setContentsMargins(16, 8, 16, 8)
        t0l.setSpacing(4)

        t0l.addWidget(self._make_section_header("最近文件"))
        self._file_rows: list[QWidget] = []
        for path, t in [("v4/main_window.py", "2h 前"), ("v4/worker.py", "4h 前"),
                         ("agent_engine/engines/prompt_engine.py", "昨天")]:
            row = self._make_file_row(path, t)
            t0l.addWidget(row)
            self._file_rows.append(row)
        t0l.addStretch()
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        self._stack.addWidget(self._tab0)

        # Tab1-3: 占位
        self._placeholders: list[QLabel] = []
        for text in ["终端", "文件编辑器", "浏览器"]:
            lbl = QLabel(f"{text}\n（功能待实现）")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px; background: transparent;")
            self._stack.addWidget(lbl)
            self._placeholders.append(lbl)

        layout.addWidget(self._stack, 1)
        self._switch_tab(0)
        self.setStyleSheet(f"background-color: {C['bg_right']};")

    def _make_section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 9px; font-weight: 600; "
            f"letter-spacing: 0.5px; padding: 0 0 4px 0;"
        )
        return lbl

    def _make_file_row(self, path: str, time_str: str) -> QWidget:
        row = QWidget()
        row.setFixedHeight(24)
        hl = QHBoxLayout(row)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        name_lbl = QLabel(path)
        name_lbl.setFont(font(11))
        name_lbl.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        hl.addWidget(name_lbl, 1)

        time_lbl = QLabel(time_str)
        time_lbl.setFont(font(9))
        time_lbl.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
        time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(time_lbl)

        # SVG dark: fill=#16213e stroke=#2a2a4a rx=4; light: fill=#f8f9fa stroke=#dee2e6
        row.setStyleSheet(
            f"QWidget {{ background-color: {C['bg_file_row']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
            f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return row

    def set_window_buttons(self, minimize_cb, maximize_cb, close_cb):
        """把系统最小化/最大化/关闭按钮嵌入右栏顶部状态栏最右侧，使用SVG图标。"""
        icons = [
            ("M 6 10 L 18 10", minimize_cb),   # 最小化：横线
            # 标准还原框：前后两个重叠矩形
            ("M 7 5 L 16 5 L 16 14 L 7 14 Z M 5 7 L 14 7 L 14 16 L 5 16 Z", maximize_cb),
            ("M 6 6 L 18 18 M 18 6 L 6 18", close_cb),       # 关闭：X
        ]
        for path, cb in icons:
            btn = QPushButton()
            btn.setFixedSize(28, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 用 QLabel 显示 SVG 路径图标
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="20" viewBox="0 0 24 20">
                <path d="{path}" fill="none" stroke="{C['text_secondary']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
            lbl = QLabel(btn)
            lbl.setPixmap(svg_icon(svg, 24, 20))
            lbl.move(2, 0)
            btn.clicked.connect(cb)
            self._win_hl.addWidget(btn)

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.set_active(i == idx)

    def _on_close_tab(self, idx: int):
        # Demo 关闭逻辑：关闭非首个标签后切回第一个
        if idx > 0 and idx < len(self._tab_btns):
            self._tab_btns[idx].setVisible(False)
            self._switch_tab(0)

    def _refresh_theme(self):
        is_dark = theme.name == "dark"
        tab_bar_bg = C["bg_right"] if is_dark else C["bg_darker"]
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._tab_bar.setStyleSheet(f"background-color: {tab_bar_bg};")
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        for lbl in self._placeholders:
            lbl.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px; background: transparent;")
        icon_fg = C['text_secondary'] if theme.name == "dark" else C['text_label']
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        for row in self._file_rows:
            row.setStyleSheet(
                f"QWidget {{ background-color: {C['bg_file_row']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
                f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 刷新内部 label 颜色
            for child in row.findChildren(QLabel):
                if child.alignment() & Qt.AlignRight:
                    child.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
                else:
                    child.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        # 刷新窗口控制按钮图标颜色
        for btn in self._win_btns.findChildren(QPushButton):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            lbl = btn.findChild(QLabel)
            if lbl:
                # 重新渲染图标（stroke 颜色更新）
                pass  # 图标在主题切换后颜色不变即可，此处省略重渲染
        self._switch_tab(self._active_tab)


# ══════════════════════════════════════════════════════════════
# 主窗口（QSplitter 三栏 + 独立折叠）
# ══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        self.resize(1024, 720)
        self.setMinimumWidth(800)
        self.setWindowTitle("Agent Workbench — UI Template")
        self._right_visible = True
        self._drag_pos = None
        self._corner_radius = 8
        self._setup_ui()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)

        # 左栏
        self._left = LeftPanel()
        self._splitter.addWidget(self._left)

        # 中栏
        self._center = ChatArea()
        self._center._header.expand_toggled.connect(self._toggle_right_panel)
        self._splitter.addWidget(self._center)

        # 右栏
        self._right = RightPanel()
        self._right.set_window_buttons(self.showMinimized, self._toggle_maximize, self.close)
        self._splitter.addWidget(self._right)

        self._splitter.setSizes([220, 404, 400])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        ml.addWidget(self._splitter)

        # 全局主题调色板
        theme.changed.connect(self._apply_theme_palette)
        self._apply_theme_palette()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _apply_rounded_mask(self):
        """Frameless窗口四角圆角遮罩。"""
        from PySide6.QtGui import QBitmap, QPainterPath, QPainter
        r = self._corner_radius
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, r, r)
        mask = QBitmap(self.size())
        mask.fill(Qt.color0)
        p = QPainter(mask)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillPath(path, Qt.color1)
        p.end()
        self.setMask(mask)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _apply_theme_palette(self):
        app = QApplication.instance()
        from PySide6.QtWidgets import QStyleFactory
        app.setStyle(QStyleFactory.create("Fusion"))
        p = QPalette()
        p.setColor(QPalette.Window, qcolor(C["bg_primary"]))
        p.setColor(QPalette.WindowText, qcolor(C["text_primary"]))
        p.setColor(QPalette.Base, qcolor(C["bg_primary"]))
        p.setColor(QPalette.Button, qcolor(C["bg_sidebar"]))
        p.setColor(QPalette.Highlight, qcolor(C["accent"]))
        app.setPalette(p)

    def _toggle_right_panel(self):
        """切换右侧面板显示/隐藏，中间聊天区自动延伸/收缩。"""
        if self._right_visible:
            self._right.hide()
            total = self.width()
            self._splitter.setSizes([220, total - 220, 0])
            self._right_visible = False
        else:
            self._right.show()
            self._splitter.setSizes([220, 404, 400])
            self._right_visible = True
        QApplication.processEvents()
        self._center._rebuild_content()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Workbench UI Template")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
