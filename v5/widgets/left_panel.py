"""V5 左侧面板组件。"""
import os
from typing import Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QScrollArea, QStackedWidget, QListWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from .base import theme, V5_THEMES, C, font
from .window_frame import AppleMenu

# ══════════════════════════════════════════════════════════════
# 左栏：ConversationListPanel（220px）
# ══════════════════════════════════════════════════════════════

class SessionItem(QWidget):
    """单个会话项：精确对齐 ui-full-dark/light.svg。
       卡片 192×48 rx=6；标题/状态/时间按 SVG 坐标 x=24 左对齐。
    """
    clicked = Signal(int)
    action_requested = Signal(str, int)  # action, index

    def __init__(self, index: int, title: str, preview: str, time_str: str, parent=None):
        super().__init__(parent)
        self._index = index
        self._active = False
        self._hover = False
        self.setMinimumHeight(58)  # 高度随内容自适应，最低 58px
        self.setMinimumWidth(1)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 4)
        layout.setSpacing(5)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(font(12, bold=True))
        self._title_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setMinimumWidth(1)
        self._title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self._title_lbl)

        self._preview_lbl = QLabel(preview)
        self._preview_lbl.setFont(font(9))
        self._preview_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._preview_lbl.setWordWrap(True)
        self._preview_lbl.setMinimumWidth(1)
        self._preview_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self._preview_lbl)

        self._refresh_style()
        theme.changed.connect(self._refresh_style)
        # 清除可能残留的 QSS，由 paintEvent 全权绘制
        self.setStyleSheet("")

    def _refresh_style(self):
        """应用主题颜色到子标签，不直接设 SessionItem 样式（由 paintEvent 绘制）。"""
        if self._active:
            self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        else:
            self._title_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self.update()  # 触发 paintEvent 重绘圆角背景

    def paintEvent(self, event):
        """自定义绘制：单个圆角矩形背景（含 hover）+ 选中边框，统一包围全部内容。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        r = 6.0  # SVG rx=6

        # 背景填充（选中 > hover > 普通）
        if self._active:
            bg = C["bg_card_selected"]
        elif self._hover:
            bg = C["bg_hover"]
        else:
            bg = C["bg_card"]
        p.setBrush(QColor(bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, r, r)

        # 边框：1px 内缩确保笔完全在 widget 内，四边厚度一致（无裁切/无 sub-pixel 漂移）
        border_color = C["accent"] if self._active else C["border"]
        pen = QPen(QColor(border_color), 1.0, Qt.SolidLine)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        border_rect = QRectF(1.0, 1.0, rect.width() - 2.0, rect.height() - 2.0)
        border_r = max(r - 1.0, 0.5)
        p.drawRoundedRect(border_rect, border_r, border_r)

        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)

    def _show_context_menu(self, pos):
        """右键菜单：Apple 风格"""
        m = AppleMenu()
        new_item = m.add_item("新会话")
        proj_item = m.add_item("项目会话")
        m.add_separator()
        rename_item = m.add_item("重命名")
        m.add_separator()
        del_item = m.add_item("删除会话")
        # 点击 → 关闭菜单 → 下一帧执行业务（纯开关模式）
        new_item.clicked.connect(lambda: self._handle_menu_click("new"))
        proj_item.clicked.connect(lambda: self._handle_menu_click("project"))
        rename_item.clicked.connect(lambda: self._handle_menu_click("rename"))
        del_item.clicked.connect(lambda: self._handle_menu_click("delete"))
        m.show_at(self.mapToGlobal(pos))
        self._active_menu = m

    def _handle_menu_click(self, action: str):
        """菜单项点击 → close() → 下一帧执行，主循环不阻塞"""
        self._active_menu.close()
        QTimer.singleShot(0, lambda a=action: self._execute_menu_action(a))

    def _execute_menu_action(self, action: str):
        """菜单动作执行（菜单已关闭，主循环空闲）"""
        self.action_requested.emit(action, self._index)


class SessionGroup(QWidget):
    """可折叠会话分组：分组头 + 右侧计数。"""
    session_clicked = Signal(int)
    session_action_requested = Signal(str, int)
    new_session_requested = Signal(str)

    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._name = name
        self._count = count
        self._items: list[SessionItem] = []
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
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

        self._add_btn = QLabel("+")
        self._add_btn.setFont(font(11, bold=True))
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(f"color: {C['text_muted']}; background: transparent; padding: 0px 2px;")
        self._add_btn.mousePressEvent = lambda e: self.new_session_requested.emit("chat") if e.button() == Qt.LeftButton else None
        hl.addWidget(self._add_btn)

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
        self._add_btn.setStyleSheet(f"color: {C['text_muted']}; background: transparent; padding: 0px 2px;")

    def add_session(self, item: SessionItem):
        item.clicked.connect(self.session_clicked.emit)
        item.action_requested.connect(self._on_item_action)
        self._items.append(item)
        self._items_layout.addWidget(item)

    def _on_item_action(self, action: str, index: int):
        self.session_action_requested.emit(action, index)

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
    new_session_requested = Signal(str)         # session_type: "chat" | "work"
    session_action_requested = Signal(str, int)  # action, index
    search_text_changed = Signal(str)
    theme_toggled = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 宽度由外部 QSplitter 控制（MainWindow 中设置 min/max）
        self._current_tab = "会话"
        self._groups: list[SessionGroup] = []
        self._all_items: list[SessionItem] = []
        self._idx_to_sid: dict[int, str] = {}
        self._sid_to_idx: dict[str, int] = {}
        self._active_idx = 0
        self._file_mode = False
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
        stl.addWidget(self._new_btn, 1)  # 新会话按钮自适应剩余宽度
        stl.addWidget(self._more_btn)

        # 搜索框（初始隐藏，点击🔍后展开占满 new_btn + more_btn 宽度）
        self._search_input = QLineEdit()
        self._search_input.setFixedHeight(22)
        self._search_input.setPlaceholderText("搜索会话...")
        self._search_input.hide()
        stl.addWidget(self._search_input, 1)

        # 搜索关闭按钮（初始隐藏）
        self._search_close = self._make_small_btn("✕", 28, 22, C["text_muted"], 10)
        self._search_close.hide()
        stl.addWidget(self._search_close)

        self._search_btn.clicked.connect(self._toggle_search)
        self._search_close.clicked.connect(self._close_search)
        self._more_btn.clicked.connect(self._on_more_clicked)
        self._new_btn.clicked.connect(lambda: self.new_session_requested.emit("chat"))
        self._search_input.textChanged.connect(self.search_text_changed.emit)

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
        sess_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sess_widget.setMinimumWidth(1)
        self._sess_layout = QVBoxLayout(sess_widget)
        self._sess_layout.setContentsMargins(0, 0, 0, 0)
        self._sess_layout.setSpacing(6)

        self._empty_lbl = QLabel("暂无会话")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setFont(font(11))
        self._empty_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._empty_lbl.hide()
        self._sess_layout.addWidget(self._empty_lbl)

        self._sess_layout.addStretch()
        self._sess_scroll.setWidget(sess_widget)
        self._stack.addWidget(self._sess_scroll)

        # 文件管理器页面（索引 2）
        self._file_page = QWidget()
        fpl = QVBoxLayout(self._file_page)
        fpl.setContentsMargins(6, 4, 6, 4)
        fpl.setSpacing(6)
        path_row = QHBoxLayout()
        path_row.setSpacing(6)
        self._file_back_btn = QPushButton("←")
        self._file_back_btn.setFixedSize(28, 22)
        self._file_back_btn.setCursor(Qt.PointingHandCursor)
        self._file_path_lbl = QLabel("agent_workbench")
        self._file_path_lbl.setFont(font(10))
        self._file_path_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        path_row.addWidget(self._file_back_btn)
        path_row.addWidget(self._file_path_lbl, 1)
        fpl.addLayout(path_row)
        self._file_list = QListWidget()
        self._file_list.addItems(["📁 agent_engine", "📁 core", "📁 services", "📁 v5", "📁 experiments"])
        self._file_list.addItems(["📄 main.py", "📄 requirements.txt", "📄 README.md", "📄 CHANGELOG.md"])
        self._file_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; color: {C['text_primary']}; font-size: 11px; }}"
            f"QListWidget::item {{ padding: 4px 8px; border-radius: 4px; }}"
            f"QListWidget::item:hover {{ background: {C['bg_hover']}; }}"
        )
        fpl.addWidget(self._file_list)
        self._stack.addWidget(self._file_page)

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

        # 真实会话通过 MainWindow 调用 refresh_sessions 注入
        # self._populate_sessions()

        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        self._sep2.setStyleSheet(f"background-color: {C['border']};")
        # Tab 按钮恢复背景框 + 文字颜色
        for btn, active in [(self._func_btn, self._current_tab == "功能"),
                             (self._sess_btn, self._current_tab == "会话")]:
            bg = C["accent"] if active else C["btn_bg"]
            fg = C["text_inverse"] if active else C["text_secondary"]
            fw = 600 if active else 500
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )
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
        # 搜索输入框 & 关闭按钮（主题适配）
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; padding: 2px 8px; font-size: 11px; }}"
        )
        self._search_close.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_muted']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 10px; font-weight: 500; }}"
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
        self.theme_toggled.emit(new_theme)

    def _make_tab_btn(self, text: str, active: bool) -> QPushButton:
        """Tab 标签：SVG 92×22 rx=6 背景框，active=accent/#fff，inactive=btn_bg/text_secondary。"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(92, 22)
        bg = C["accent"] if active else C["btn_bg"]
        fg = C["text_inverse"] if active else C["text_secondary"]
        fw = 600 if active else 500
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: {fg}; "
            f"border: none; border-radius: 6px; padding: 2px 8px; "
            f"font-size: 11px; font-weight: {fw}; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
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
        """新会话按钮：bg_primary + accent 边框，宽度自适应左侧栏。"""
        btn = QPushButton("+ 新会话")
        btn.setMinimumWidth(80)
        btn.setFixedHeight(22)
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
        self._file_mode = False
        self._stack.setCurrentIndex(0 if is_func else 1)
        self._tool_stack.setCurrentIndex(0 if is_func else 1)
        self._func_btn.setChecked(is_func)
        self._sess_btn.setChecked(not is_func)
        for btn, active in [(self._func_btn, is_func), (self._sess_btn, not is_func)]:
            bg = C["accent"] if active else C["btn_bg"]
            fg = C["text_inverse"] if active else C["text_secondary"]
            fw = 600 if active else 500
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )

    def _toggle_search(self):
        """展开/收起会话搜索框"""
        if self._new_btn.isVisible():
            self._new_btn.hide()
            self._more_btn.hide()
            self._search_input.show()
            self._search_close.show()
            self._search_input.setFocus()
        else:
            self._close_search()

    def _close_search(self):
        """关闭搜索框，恢复工具行"""
        self._search_input.clear()
        self._search_input.hide()
        self._search_close.hide()
        self._new_btn.show()
        self._more_btn.show()

    def _on_more_clicked(self):
        """切换文件管理器 / 会话列表"""
        if self._file_mode:
            self._file_mode = False
            self._stack.setCurrentIndex(1)
        else:
            self._file_mode = True
            self._stack.setCurrentIndex(2)

    def _on_session_clicked(self, idx: int):
        self._select_session(idx)
        self.session_selected.emit(idx)

    def _select_session(self, idx: int):
        self._active_idx = idx
        for g in self._groups:
            g.set_active(idx)

    # ══════════════════════════════════════════════════════════════
    # UIRenderer 桥接 API（P3.4 已实现真实逻辑）
    # ══════════════════════════════════════════════════════════════

    def refresh(self, sessions):
        """根据后端 SessionMetadata 列表重建会话分组，保留已有 preview 避免 badge 被覆盖。"""
        # 重建前保存当前 preview 与激活状态
        old_previews: dict[str, str] = {}
        old_active: str = ""
        for item in self._all_items:
            sid = self._idx_to_sid.get(item._index)
            if sid:
                old_previews[sid] = item._preview_lbl.text()
                if item._active:
                    old_active = sid

        # 清理旧分组
        for g in self._groups:
            g.deleteLater()
        self._groups.clear()
        self._all_items.clear()
        self._idx_to_sid.clear()
        self._sid_to_idx.clear()
        self._empty_lbl.hide()

        if not sessions:
            self._empty_lbl.show()
            return

        # 按 project_path 分组
        grouped: dict[str, list[tuple[int, Any]]] = {}
        for idx, sess in enumerate(sessions):
            sid = getattr(sess, "session_id", str(sess))
            self._idx_to_sid[idx] = sid
            self._sid_to_idx[sid] = idx
            path = getattr(sess, "project_path", "") or ""
            group_name = os.path.basename(path) if path else "全局会话"
            grouped.setdefault(group_name, []).append((idx, sess))

        for group_name, items in grouped.items():
            group = SessionGroup(group_name, len(items))
            for idx, sess in items:
                title = getattr(sess, "title", "未命名")
                pinned = getattr(sess, "pinned", False)
                if pinned:
                    title = f"📌 {title}"
                sid = self._idx_to_sid[idx]
                # 列表预览以最后消息摘要为权威来源；仅当无消息时保留旧临时状态
                preview = getattr(sess, "last_preview", "")
                if not preview:
                    preview = old_previews.get(sid) or getattr(sess, "mode", "") or "等待第一条消息..."
                updated = getattr(sess, "updated_at", None)
                try:
                    time_str = updated.strftime("%H:%M") if updated else ""
                except Exception:
                    time_str = str(updated)
                item = SessionItem(idx, title, preview, time_str)
                group.add_session(item)
                self._all_items.append(item)
            self._groups.append(group)
            self._sess_layout.insertWidget(self._sess_layout.count() - 1, group)
            group.session_clicked.connect(self._on_session_clicked)
            group.new_session_requested.connect(self.new_session_requested.emit)
            group.session_action_requested.connect(self.session_action_requested.emit)

        active_idx = self._sid_to_idx.get(old_active, 0)
        self._select_session(active_idx)

    def set_active_session(self, active_session_id: str):
        """根据 session_id 高亮对应会话项。"""
        idx = self._sid_to_idx.get(active_session_id)
        if idx is not None:
            self._select_session(idx)

    def update_badge(self, session_id: str, phase: str):
        """更新指定会话的状态徽章（使用 preview 文本展示阶段）。"""
        idx = self._sid_to_idx.get(session_id)
        if idx is None:
            return
        for item in self._all_items:
            if item._index == idx:
                item._preview_lbl.setText(phase or "")
                break

    def filter_sessions(self, text: str):
        """按文本过滤会话列表，匹配标题与预览内容；空文本恢复全部显示。"""
        needle = text.strip().lower()
        for group in self._groups:
            visible_count = 0
            for item in group._items:
                title = item._title_lbl.text().lower()
                preview = item._preview_lbl.text().lower()
                matched = (needle in title) or (needle in preview)
                item.setVisible(matched)
                if matched:
                    visible_count += 1
            group.setVisible(visible_count > 0 or not needle)
            group._cnt_lbl.setText(str(visible_count if needle else len(group._items)))

