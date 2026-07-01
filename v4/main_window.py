"""
main_window.py — v4 主窗口（最终发布版三栏 UI）

布局：
- QSplitter 三栏：左 250px + 中 stretch + 右 320px
- 左栏：功能/会话 Tab + 工具行 + 分组折叠会话列表 + 底部控制
- 中栏：标题栏 + 卡片化消息流 + 新输入区
- 右栏：v4 架构 / 终端 / 文件编辑器 / 浏览器

主题：
- 支持 dark / light 两套配色，通过左栏底部主题按钮切换
- 主题状态持久化到 config.yaml 的 app.theme
"""
import html
import os
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QTextBrowser, QStyleFactory, QLineEdit,
    QMenu, QSplitter, QSizePolicy, QGraphicsView, QGraphicsProxyWidget,
    QGraphicsTextItem,
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QRectF
from PySide6.QtGui import (
    QPalette, QColor, QFont, QTextCursor, QShortcut, QKeySequence,
    QAction, QPainter,
)

from markdown import markdown as md

from .repository import SessionRepository, _get_app_root
from .event_bus import MessageBus
from .orchestrator import SessionOrchestrator
from .ui_renderer import UIRenderer
from .conversation_list import ConversationListWidget
from .input_area import InputAreaWidget
from .right_panel import RightPanelWidget
from .icons import svg_icon
from .chat_scene import ChatScene
from .chat_items import (
    CHAT_WIDTH, LEFT_MARGIN, CONTENT_WIDTH,
    C_BG_PRIMARY, C_BG_SIDEBAR, C_ACCENT, C_BORDER,
    C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED, C_TEXT_INVERSE,
    C_ACCENT_BLUE, C_GREEN, C_YELLOW,
    UserBubbleItem, FoldBlockItem, ToolEntryItem,
    PhasePanelItem, PhaseStepItem, PhaseBulletItem, PhaseTextItem,
    SystemCardItem, PHASE_COLORS, PHASE_TITLES, STEP_ICONS,
    _font, _mono_font,
)
from .events import (
    UserSendEvent, UserStopEvent,
    UserConfirmEvent, UserReanalyzeEvent, UserSkipVerifyEvent,
    SessionSwitchEvent, SessionDeleteEvent, SessionPinEvent,
)
from .worker_manager import WorkerManager
from services.config_service import ConfigService


def _md_to_html(text: str) -> str:
    raw_html = md(html.escape(text), extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'])
    return html.unescape(raw_html)


# ── 主题定义 ─────────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_sidebar": "#16213e",
        "bg_input": "#1a1a2e",
        "bg_right": "#0f1729",
        "bg_right_tab": "#0f1729",
        "bg_hover": "#2a2a4a",
        "bg_selected": "#0f3460",
        "bg_group_header": "#16213e",
        "bg_bubble_user": "#007acc",
        "bg_bubble_ai": "#16213e",
        "bg_system_card": "#16213e",
        "header_btn_bg": "#2a2a4a",
        "header_btn_hover": "#3a3a5a",
        "header_btn_active": "#0f3460",
        "border": "#2a2a4a",
        "border_bubble_ai": "#2a2a4a",
        "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0b0",
        "text_muted": "#6a6a8a",
        "text_inverse": "#ffffff",
        "accent": "#007acc",
        "accent_hover": "#1177bb",
        "send_btn": "#007acc",
        "send_btn_hover": "#1177bb",
        "stop_btn": "#2a2a4a",
        "stop_btn_hover": "#3a3a5a",
        "tag_bg": "#0f3460",
        "tag_text": "#a0a0b0",
        "card_analyze_bg": "#16213e",
        "card_analyze_border": "#569cd6",
        "card_execute_bg": "#16213e",
        "card_execute_border": "#dcdcaa",
        "card_verify_bg": "#16213e",
        "card_verify_border": "#c586c0",
        "card_archive_bg": "#16213e",
        "card_archive_border": "#4ec9b0",
        "card_tool_bg": "#16213e",
        "card_tool_border": "#4ec9b0",
        "card_output_bg": "#1a1a2e",
        "card_output_border": "#2a2a4a",
    },
    "light": {
        "bg_primary": "#f8f9fa",
        "bg_sidebar": "#e9ecef",
        "bg_input": "#ffffff",
        "bg_hover": "#e9ecef",
        "bg_selected": "#e7f1ff",
        "bg_group_header": "#e9ecef",
        "bg_bubble_user": "#007acc",
        "bg_bubble_ai": "#ffffff",
        "bg_system_card": "#f8f9fa",
        "header_btn_bg": "#e9ecef",
        "header_btn_hover": "#dee2e6",
        "header_btn_active": "#ced4da",
        "border": "#dee2e6",
        "border_bubble_ai": "#dee2e6",
        "text_primary": "#212529",
        "text_secondary": "#495057",
        "text_muted": "#adb5bd",
        "text_inverse": "#ffffff",
        "accent": "#007acc",
        "accent_hover": "#005a9e",
        "send_btn": "#007acc",
        "send_btn_hover": "#005a9e",
        "stop_btn": "#e5e5e5",
        "stop_btn_hover": "#d0d0d0",
        "tag_bg": "#e9ecef",
        "tag_text": "#6c757d",
        "card_analyze_bg": "#e8f4fd",
        "card_analyze_border": "#007acc",
        "card_execute_bg": "#fffbe6",
        "card_execute_border": "#ffc107",
        "card_verify_bg": "#f3e5f5",
        "card_verify_border": "#9c27b0",
        "card_archive_bg": "#e8f5e9",
        "card_archive_border": "#4caf50",
        "card_tool_bg": "#e8f5e9",
        "card_tool_border": "#4caf50",
        "card_output_bg": "#f5f5f5",
        "card_output_border": "#bdbdbd",
    },
}

DEFAULT_THEME = "dark"


class HeaderToolbar(QWidget):
    """会话区标题栏：左侧标题/环境信息 + 右侧三键操作（搜索/更多/展开）。"""

    expand_toggled = Signal()
    search_requested = Signal(str, bool)
    export_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._theme = THEMES[DEFAULT_THEME]
        self._title = ""
        self._env = ""
        self._search_visible = False
        self._icon_size = 14
        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 标题行（双行：title + env，右侧三按钮 + 垂直分隔线）──
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧：双行标题区（SVG: x=20 y=16/y=30）
        title_block = QVBoxLayout()
        title_block.setContentsMargins(20, 8, 0, 8)
        title_block.setSpacing(2)

        self.title_label = QLabel("")
        title_block.addWidget(self.title_label)

        self.env_label = QLabel("")
        title_block.addWidget(self.env_label)

        layout.addLayout(title_block, 1)

        # 垂直分隔线（SVG: x1=331 y1=8 x2=331 y2=32）
        vsep = QLabel()
        vsep.setFixedSize(1, 24)
        vsep.setStyleSheet(f"background-color: {self._theme.get('border', '#2a2a4a')};")
        layout.addWidget(vsep)
        self._vsep = vsep

        layout.addSpacing(6)

        # 右侧三按钮（SVG: search 337/8, more 359/8, expand 381/8）
        self.search_btn = self._icon_btn("search", "搜索 (Ctrl+F)")
        self.search_btn.clicked.connect(self._toggle_search)

        self.more_btn = self._icon_btn("more", "更多操作")
        self._setup_more_menu()

        self.expand_btn = self._icon_btn("collapse", "展开/收起面板 (Ctrl+B)")
        self.expand_btn.clicked.connect(self._toggle_expand)

        layout.addWidget(self.search_btn)
        layout.addWidget(self.more_btn)
        layout.addWidget(self.expand_btn)
        root_layout.addWidget(header)

        # ── 搜索条 ──
        self.search_bar = QWidget()
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(24, 4, 12, 8)
        search_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("在当前会话中搜索...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._find_next)
        search_layout.addWidget(self.search_input, 1)

        self.search_prev_btn = self._icon_btn("chevron-up", "上一个")
        self.search_prev_btn.clicked.connect(self._find_prev)
        self.search_next_btn = self._icon_btn("chevron-down", "下一个")
        self.search_next_btn.clicked.connect(self._find_next)
        self.search_close_btn = self._icon_btn("close", "关闭 (Esc)")
        self.search_close_btn.clicked.connect(self._hide_search)
        search_layout.addWidget(self.search_prev_btn)
        search_layout.addWidget(self.search_next_btn)
        search_layout.addWidget(self.search_close_btn)

        self.search_bar.setVisible(False)
        root_layout.addWidget(self.search_bar)

        self._apply_theme()

    def _icon_btn(self, icon_name: str, tooltip: str) -> QPushButton:
        """创建使用 SVG 图标的工具按钮，带背景色以匹配设计模板。"""
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFlat(True)
        btn.setFixedSize(18, 22)
        btn.setIconSize(QSize(self._icon_size, self._icon_size))
        btn.setIcon(svg_icon(icon_name, self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self._apply_icon_btn_style(btn)
        return btn

    def _apply_icon_btn_style(self, btn: QPushButton):
        """应用标题栏按钮 normal/hover/active 背景色。"""
        t = self._theme
        bg = t.get("header_btn_bg", t["bg_hover"])
        hover = t.get("header_btn_hover", t["border"])
        active = t.get("header_btn_active", t["bg_selected"])
        border = t.get("border", "#2a2a4a")
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; border: 0.5px solid {border}; border-radius: 3px; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
            f"QPushButton:pressed {{ background-color: {active}; }}"
        )

    def _setup_more_menu(self):
        self.more_menu = QMenu(self.more_btn)
        self.action_export = QAction("导出当前会话", self)
        self.action_copy = QAction("复制会话内容", self)
        self.action_settings = QAction("打开设置", self)
        self.more_menu.addAction(self.action_export)
        self.more_menu.addAction(self.action_copy)
        self.more_menu.addSeparator()
        self.more_menu.addAction(self.action_settings)
        self.more_btn.setMenu(self.more_menu)
        self.action_export.triggered.connect(self.export_requested.emit)
        self.action_copy.triggered.connect(self._copy_session_content)
        self.action_settings.triggered.connect(self.settings_requested.emit)

    def _copy_session_content(self):
        from PySide6.QtWidgets import QApplication
        text = ""
        if hasattr(self.parent(), "chat_scene"):
            for item in self.parent().chat_scene.items:
                if hasattr(item, "_text") and item._text:
                    text += item._text + "\n\n"
        QApplication.clipboard().setText(text)

    def _toggle_search(self):
        self._search_visible = not self._search_visible
        self.search_bar.setVisible(self._search_visible)
        if self._search_visible:
            self.search_input.setFocus()
        else:
            self.search_input.clear()

    def _hide_search(self):
        self._search_visible = False
        self.search_bar.setVisible(False)
        self.search_input.clear()

    def _on_search_text_changed(self, text: str):
        self.search_requested.emit(text, True)

    def _find_next(self):
        self.search_requested.emit(self.search_input.text(), True)

    def _find_prev(self):
        self.search_requested.emit(self.search_input.text(), False)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._refresh_expand_icon()
        self.expand_toggled.emit()

    def update_expand_state(self, expanded: bool):
        self._expanded = expanded
        self._refresh_expand_icon()

    def _refresh_expand_icon(self):
        icon_name = "collapse" if self._expanded else "expand"
        self.expand_btn.setIcon(svg_icon(icon_name, self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self.expand_btn.setToolTip("收起面板" if self._expanded else "展开面板")
        self._apply_icon_btn_style(self.expand_btn)

    def set_title(self, title: str, env: str = ""):
        self._title = title
        self._env = env
        self._render_title()

    def _render_title(self):
        t = self._theme
        # SVG: title at y=16 size=12 w=500 color=#e0e0e0
        self.title_label.setText(
            f'<span style="color:{t["text_primary"]};font-size:12px;font-weight:500;">{self._title}</span>'
        )
        # SVG: env at y=30 size=10 color=#6a6a8a
        self.env_label.setText(
            f'<span style="color:{t.get("text_muted", t["text_secondary"])};font-size:10px;">{self._env}</span>'
        )

    def set_theme(self, theme_name: str):
        self._theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self._apply_theme()
        self._render_title()
        self._vsep.setStyleSheet(f"background-color: {self._theme.get('border', '#2a2a4a')};")
        self.search_btn.setIcon(svg_icon("search", self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self.more_btn.setIcon(svg_icon("more", self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self._refresh_expand_icon()
        self._apply_icon_btn_style(self.search_btn)
        self._apply_icon_btn_style(self.more_btn)
        self._apply_icon_btn_style(self.expand_btn)
        self.search_prev_btn.setIcon(svg_icon("chevron-up", self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self.search_next_btn.setIcon(svg_icon("chevron-down", self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))
        self.search_close_btn.setIcon(svg_icon("close", self._theme.get("text_secondary", "#a0a0b0"), self._icon_size))

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']}; "
            f"border: 1px solid {t['border']}; border-radius: 4px; padding: 4px 8px; }}"
        )

    def focus_search(self):
        self._toggle_search()

    def key_escape(self):
        if self._search_visible:
            self._hide_search()
            return True
        return False


class SimpleChatArea(QWidget):
    """聊天区：QGraphicsView 像素级渲染，对齐 SVG 设计稿。

    架构：HeaderToolbar + QGraphicsView(ChatScene) + ConfirmBar + InputAreaWidget。
    用户气泡、折叠块、阶段面板均由 QPainter 逐像素绘制。
    AI 消息的富文本 body 通过 QGraphicsProxyWidget(QTextBrowser) 内嵌渲染。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = THEMES[DEFAULT_THEME]
        self._current_phase = ""
        self._streaming_active = False
        self._streaming_buffer = ""
        self._streaming_proxy = None  # 流式输出 proxy widget
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部：会话标题 + 三键操作
        self.header = HeaderToolbar()
        self.header.search_requested.connect(self._on_search)
        layout.addWidget(self.header)

        self.sep = QLabel()
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet(f"background-color: {self._theme['border']};")
        layout.addWidget(self.sep)

        # 消息流：QGraphicsView + ChatScene（替代 QTextBrowser）
        self.chat_view = QGraphicsView()
        self.chat_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.chat_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.chat_view.setFrameShape(QGraphicsView.NoFrame)
        self.chat_view.setStyleSheet("border: none; background: transparent;")
        self.chat_scene = ChatScene()
        self.chat_view.setScene(self.chat_scene)
        self.chat_scene.sceneRectChanged.connect(self._on_scene_changed)
        layout.addWidget(self.chat_view, 1)

        # 「帮我分析当前项目」按钮
        self.analyze_project_btn = QPushButton("帮我分析当前项目")
        self.analyze_project_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_project_btn.setVisible(False)
        self.analyze_project_btn.clicked.connect(self._on_analyze_project)
        layout.addWidget(self.analyze_project_btn)

        # 确认条
        self.confirm_bar = QWidget()
        confirm_layout = QHBoxLayout(self.confirm_bar)
        confirm_layout.setContentsMargins(24, 8, 24, 8)
        confirm_layout.setSpacing(12)
        self.confirm_label = QLabel("")
        self.confirm_label.setWordWrap(True)
        confirm_layout.addWidget(self.confirm_label, 1)
        self.confirm_btn = QPushButton("确认执行")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setFixedWidth(80)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedWidth(64)
        confirm_layout.addWidget(self.confirm_btn)
        confirm_layout.addWidget(self.cancel_btn)
        self.confirm_bar.setVisible(False)
        self.confirm_btn.clicked.connect(lambda: self._on_confirm(True))
        self.cancel_btn.clicked.connect(lambda: self._on_confirm(False))
        layout.addWidget(self.confirm_bar)

        # SVG: 输入区上方分隔线 (y=652, stroke=#2a2a4a, 0.5px)
        self.input_sep = QLabel()
        self.input_sep.setFixedHeight(1)
        self.input_sep.setStyleSheet(f"background-color: {self._theme['border']};")
        layout.addWidget(self.input_sep)

        # 输入区
        self.input_area = InputAreaWidget(self._theme)
        self.input_area.send_requested.connect(self._on_send)
        self.input_area.stop_requested.connect(self._on_stop)
        layout.addWidget(self.input_area)

        self._apply_theme_styles()

    def _on_scene_changed(self, rect: QRectF):
        """场景内容变化 → 自动滚到底部。"""
        vbar = self.chat_view.verticalScrollBar()
        if vbar:
            vbar.setValue(vbar.maximum())

    # 兼容旧引用
    @property
    def input_field(self):
        return self.input_area.text_edit

    def set_theme(self, theme_name: str):
        self._theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self._apply_theme_styles()
        self.header.set_theme(theme_name)
        self.sep.setStyleSheet(f"background-color: {self._theme['border']};")
        self.input_sep.setStyleSheet(f"background-color: {self._theme['border']};")
        self.input_area.set_theme(self._theme)
        self.chat_scene.setBackgroundBrush(QColor(self._theme["bg_primary"]))
        self.chat_view.setStyleSheet("border: none; background: transparent;")

    def _apply_theme_styles(self):
        t = self._theme
        self.analyze_project_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['bg_input']}; color: {t['accent']}; border: 0.5px solid {t['accent']};
                border-radius: 8px; padding: 8px 16px; font-size: 11px; font-weight: 600;
                margin: 0 20px 8px 20px;
            }}
            QPushButton:hover {{ background-color: {t['bg_hover']}; }}
        """)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['send_btn']}; color: {t['text_inverse']};
                border: 0.5px solid {t['send_btn']}; border-radius: 6px;
                padding: 4px 10px; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {t['send_btn_hover']}; }}
        """)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['stop_btn']}; color: {t['text_primary']};
                border: 0.5px solid {t['border']}; border-radius: 6px;
                padding: 4px 10px; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {t['stop_btn_hover']}; }}
        """)
        self.confirm_label.setStyleSheet(f"color: {t['text_primary']}; font-size: 11px;")
        self.setStyleSheet(f"background-color: {t['bg_primary']};")

    # ── 兼容 UIRenderer 接口 ──────────────────────────────────
    def _on_send(self):
        text = self.input_area.toPlainText().strip()
        if text and hasattr(self, '_send_callback'):
            self._send_callback(text)

    def _on_stop(self):
        if hasattr(self, '_stop_callback') and self._stop_callback:
            self._stop_callback()

    def _on_analyze_project(self):
        if hasattr(self, '_analyze_callback') and self._analyze_callback:
            self._analyze_callback()

    def set_send_callback(self, callback):
        self._send_callback = callback

    def set_stop_callback(self, callback):
        self._stop_callback = callback

    def set_confirm_callback(self, callback):
        self._confirm_callback = callback

    def set_analyze_callback(self, callback):
        self._analyze_callback = callback

    def set_analyze_button_visible(self, visible: bool):
        self.analyze_project_btn.setVisible(visible)

    def _on_confirm(self, confirmed: bool):
        if hasattr(self, '_confirm_callback') and self._confirm_callback:
            self._confirm_callback(confirmed)
        self.confirm_bar.setVisible(False)

    def clear_input(self):
        self.input_area.clear_input()

    def clear_chat(self):
        self._current_phase = ""
        self._streaming_buffer = ""
        self._streaming_active = False
        self._streaming_proxy = None
        self.chat_scene.clear()

    def set_header(self, title: str, env: str = ""):
        self.header.set_title(title, env)

    def _on_search(self, text: str, forward: bool = True):
        """搜索：在 ChatScene 中遍历 text items 高亮匹配。"""
        # 简化实现：搜索在 QGraphicsView 中没有原生支持，预留接口
        pass

    # ── 消息追加 API ────────────────────────────────
    def append_user(self, text: str):
        item = self.chat_scene.add_user_message(text)
        self.chat_view.viewport().update()

    def append_system(self, text: str):
        t = self._theme
        self.chat_scene.add_system_card(text)
        self.chat_view.viewport().update()

    def append_tool_fold(self, tool_html: str):
        """解析 ui_renderer 生成的 tool-fold HTML，创建 FoldBlockItem + ToolEntryItems。"""
        entries = self._parse_tool_html(tool_html)
        if not entries:
            # 回退：创建空工具折叠块
            fold = self.chat_scene.add_tool_fold(f"[{len(entries)} 工具]")
            return

        total_ms = sum(e.get("elapsed_ms", 0) for e in entries)
        status = f"[{len(entries)} 工具 · 共 {total_ms / 1000:.1f}s]"
        fold = self.chat_scene.add_tool_fold(status)
        self.chat_scene.add_tool_entries_to_fold(fold, entries)
        self.chat_view.viewport().update()

    def _parse_tool_html(self, html_str: str) -> list[dict]:
        """从 ui_renderer 的 tool HTML 中提取工具条目。"""
        entries = []
        # 匹配 tool-entry 行：tool-ok/tool-fail + 名称 + 时间
        pattern = re.compile(
            r'<span class="(tool-ok|tool-fail)">([^<]+)</span>'
            r'\s*<span class="tool-time">([^<]+)</span>'
        )
        for m in pattern.finditer(html_str):
            success = m.group(1) == "tool-ok"
            name = m.group(2).strip()
            time_str = m.group(3).strip().rstrip("ms")
            try:
                elapsed_ms = int(float(time_str) * 1000) if "s" in time_str else int(float(time_str))
            except ValueError:
                elapsed_ms = 0
            entries.append({"name": name, "elapsed_ms": elapsed_ms, "success": success})
        return entries

    def append_ai(self, text: str, phase: str = "", thinking_fold: str = ""):
        """AI 消息：可含思考折叠 + 阶段面板。"""
        effective_phase = phase or self._current_phase

        # 思考折叠
        if thinking_fold:
            think_status = self._extract_fold_status(thinking_fold)
            self.chat_scene.add_thinking_fold(think_status)

        if not text.strip():
            self.chat_view.viewport().update()
            return

        html_body = self._text_to_html(text)

        if effective_phase:
            panel = self.chat_scene.add_phase_panel(effective_phase)
            text_item = QGraphicsTextItem()
            text_item.setHtml(html_body)
            text_item.setTextWidth(CONTENT_WIDTH - 28)
            text_item.setPos(LEFT_MARGIN + 14, panel.HEADER_H + 12)
            self.chat_scene.add_phase_body(panel, [text_item], text_item.boundingRect().height() + 8)
        else:
            self.chat_scene.add_text_item(html_body)

        self.chat_view.viewport().update()

    def _text_to_html(self, text: str) -> str:
        """将 markdown 文本转为 HTML（用于 QGraphicsTextItem）。"""
        t = self._theme
        md_html = _md_to_html(text)
        return f"""
        <div style="color:{t['text_primary']};font-size:11px;line-height:1.6;">
            {md_html}
        </div>
        """

    def _extract_fold_status(self, think_html: str) -> str:
        """从思考折叠 HTML 中提取状态文本。"""
        m = re.search(r'\[([^\]]+)\]', think_html)
        return m.group(0) if m else ""

    def set_current_phase(self, phase: str):
        self._current_phase = phase

    # ── 流式 ──────────────────────────────────
    def append_chunk(self, chunk: str):
        if not chunk:
            return
        self._streaming_active = True
        self._streaming_buffer += chunk
        self._update_streaming()

    def finalize_stream(self):
        self._streaming_active = False
        self.input_area.set_streaming(False)
        text = self._streaming_buffer
        self._streaming_buffer = ""
        if not text.strip():
            return
        # 移除流式 text item
        if self._streaming_proxy:
            self.chat_scene.removeItem(self._streaming_proxy)
            self._streaming_proxy = None
        self.append_ai(text)

    def _update_streaming(self):
        """更新流式渲染：创建或更新 QGraphicsTextItem。"""
        html_body = self._text_to_html(self._streaming_buffer)
        if self._streaming_proxy is None:
            self._streaming_proxy = self.chat_scene.add_text_item(html_body)
        else:
            self._streaming_proxy.setHtml(html_body)
        self.chat_view.viewport().update()

    def set_streaming(self, active: bool):
        self._streaming_active = active
        self.input_area.set_streaming(active)
        if active:
            self._streaming_buffer = ""
            self._streaming_proxy = None

    def set_send_enabled(self, enabled: bool):
        self.input_area.set_send_enabled(enabled)

    # Phase UI
    def set_phase_indicator(self, phase: str, task_count: int = 0):
        pass

    def set_task_progress(self, current: int, total: int):
        pass

    def show_confirmation(self, task_list: list):
        if not task_list:
            return
        lines = ["等待确认：", ""]
        for idx, task in enumerate(task_list[:7], 1):
            desc = task.description if hasattr(task, "description") else str(task)
            lines.append(f"{idx}. {desc}")
        if len(task_list) > 7:
            lines.append(f"… 共 {len(task_list)} 项任务")
        self.confirm_label.setText("\n".join(lines))
        self.confirm_bar.setVisible(True)

    def hide_confirmation(self):
        self.confirm_bar.setVisible(False)

    def show_skip_verify(self):
        pass

    def hide_skip_verify(self):
        pass

    def clear_phase_ui(self):
        pass

    def append_phase_message(self, phase: str, text: str):
        self.append_system(text)

    # ── 向后兼容 ──────────────────────────────────
    def toPlainText(self) -> str:
        """收集场景中所有文本。"""
        texts = []
        for item in self.chat_scene.items:
            if isinstance(item, UserBubbleItem) and item._text:
                texts.append(item._text)
            elif isinstance(item, SystemCardItem) and item._text:
                texts.append(item._text)
        for item in self.chat_scene.items:
            for child in item.childItems():
                if isinstance(child, QGraphicsTextItem):
                    texts.append(child.toPlainText())
        return "\n".join(texts)

    def toHtml(self) -> str:
        """返回场景文本内容（兼容测试）。"""
        text = self.toPlainText()
        return f"<html><body>{html.escape(text)}</body></html>"



class MainWindow(QMainWindow):
    def __init__(self, worker_mgr=None):
        super().__init__()
        self.resize(1400, 900)
        self.setMinimumWidth(1200)
        self.setWindowTitle("Agent")

        # 1. 初始化配置与主题
        self._config = ConfigService(config_path="config/config.yaml")
        self._theme_name = self._config.get("app.theme", DEFAULT_THEME)
        if self._theme_name not in THEMES:
            self._theme_name = DEFAULT_THEME
        self._theme = THEMES[self._theme_name]

        # 2. 初始化 v4 核心组件
        self._repo = SessionRepository()
        self._bus = MessageBus(trace=False)
        self._bus.connect_dispatch()

        # ── 八引擎 + WorkerManager 初始化 ──
        self._engines = self._init_engines()
        self._worker_mgr = worker_mgr or WorkerManager(
            message_bus=self._bus,
            parent=self,
        )

        self._orchestrator = SessionOrchestrator(
            repository=self._repo,
            message_bus=self._bus,
            worker_manager=self._worker_mgr,
            parent=self,
        )

        self._apply_theme()
        self._setup_ui()

        self._ui_renderer = UIRenderer(
            message_bus=self._bus,
            chat_view=self.chat_area,
            conversation_list=self.conversation_list,
            right_panel=self.right_panel,
            current_session_provider=lambda: self._orchestrator.current_session_id or "",
            parent=self,
        )

        # 草稿窗口状态
        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._current_model_name = self._config.get("app.last_model", "tool-agent")
        self._current_mode = self._config.get("app.last_mode", "ask")

        self._connect_signals()
        self._init_default_session()

    def _get_project_path(self) -> str:
        """获取当前项目路径（当前可返回空字符串）。"""
        return ""

    def _setup_ui(self):
        """QSplitter 三栏布局：左 250 + 中 stretch + 右 320。"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        main_layout.addWidget(self.splitter)

        # 左栏
        self._left_panel = ConversationListWidget(theme=self._theme, repository=self._repo)
        self._left_panel.new_task_clicked.connect(self._on_new_task)
        self._left_panel.conversation_selected.connect(self._on_conversation_selected)
        self._left_panel.conversation_deleted.connect(self._on_conversation_deleted)
        self._left_panel.conversation_pinned.connect(self._on_conversation_pinned)
        self._left_panel.theme_changed.connect(self._on_theme_changed)
        self._left_panel.search_clicked.connect(self._on_search_clicked)
        self.conversation_list = self._left_panel
        self.splitter.addWidget(self._left_panel)

        # 中栏
        self._center_panel = SimpleChatArea()
        self._center_panel.set_theme(self._theme_name)
        self._center_panel.set_send_callback(self._on_send_message)
        self._center_panel.set_stop_callback(self._on_stop_generation)
        self._center_panel.set_confirm_callback(self._on_user_confirm)
        self._center_panel.set_analyze_callback(self._on_analyze_project)
        self._center_panel.header.expand_toggled.connect(self.toggle_panels)
        self._center_panel.header.export_requested.connect(self._on_export_session)
        self._center_panel.header.settings_requested.connect(self._on_open_settings)
        self.chat_area = self._center_panel
        self.splitter.addWidget(self._center_panel)

        # 右栏
        self._right_panel = RightPanelWidget(theme=self._theme)
        self._right_panel.set_project_root(self._get_project_path())
        self._right_panel.setFixedWidth(400)
        self.right_panel = self._right_panel
        self.splitter.addWidget(self._right_panel)

        # 设置初始尺寸：左 220 / 中 stretch / 右 400，匹配 UI 模板
        self.splitter.setSizes([220, 780, 400])

        # ── 全局快捷键 ──
        self._shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self._shortcut_search.activated.connect(self._center_panel.header.focus_search)
        self._shortcut_expand = QShortcut(QKeySequence("Ctrl+B"), self)
        self._shortcut_expand.activated.connect(self.toggle_panels)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._center_panel.header.key_escape():
                return
        super().keyPressEvent(event)

    def _apply_theme(self):
        t = THEMES[self._theme_name]
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))
        p = QPalette()
        p.setColor(QPalette.Window, QColor(t["bg_primary"]))
        p.setColor(QPalette.WindowText, QColor(t["text_primary"]))
        p.setColor(QPalette.Base, QColor(t["bg_primary"]))
        p.setColor(QPalette.Button, QColor(t["bg_sidebar"]))
        p.setColor(QPalette.Highlight, QColor(t["accent"]))
        app.setPalette(p)

    # ── 八引擎初始化 ──────────────────────────────
    def _init_engines(self) -> dict:
        from agent_engine.llm_registry import LLMRegistry
        from agent_engine.engines import (
            PromptEngine, InferenceEngine, ToolEngine,
            MemoryEngine, MetricsEngine, PolicyEngine,
        )
        config = self._config.config if self._config else {}
        registry = LLMRegistry("config/config.yaml", "config/config.yaml")
        policy = PolicyEngine(config.get("ai_engine", {}))
        metrics = MetricsEngine()
        engines = {
            "registry": registry, "policy": policy, "metrics": metrics,
            "prompt": PromptEngine(
                base_prompts={m: c.get("system_prompt", "") for m, c in config.get("manual_modes", {}).items()},
                user_rules=config.get("user_rules", []),
                app_version=config.get("app", {}).get("version", "v4.0"),
            ),
            "inference": InferenceEngine(policy_engine=policy, metrics_engine=metrics, llm_registry=registry),
            "tool": ToolEngine(),
            "memory": MemoryEngine(
                app_root=_get_app_root(),
                config=config.get("self_context", {}), policy_engine=policy,
            ),
        }
        return engines

    def _connect_signals(self):
        # 输入区 mode/model 变更
        self._center_panel.input_area.mode_changed.connect(self._on_mode_changed)
        self._center_panel.input_area.model_changed.connect(self._on_model_changed)

    def _init_default_session(self):
        """启动时不自动创建 DB 会话，直接进入草稿窗口状态。"""
        self._reset_to_draft()
        self.chat_area.set_header("Agent", "准备就绪")
        self._populate_model_selector()
        self._populate_mode_selector()

    def _populate_model_selector(self):
        """从 config 读取模型列表并填充下拉框。"""
        providers = self._config.get("llm_providers", {})
        self._center_panel.input_area.set_models(providers, self._current_model_name)

    def _populate_mode_selector(self):
        """从 config 读取模式列表并填充下拉框。"""
        modes = list(self._config.get("manual_modes", {}).keys())
        if not modes:
            modes = ["ask", "plan", "craft"]
        self._center_panel.input_area.set_modes(modes, self._current_mode)

    def _on_new_task(self):
        """点击「+ 新任务」：只重置为草稿窗口，不创建会话。"""
        self._reset_to_draft()
        self.chat_area.set_header("Agent", "准备就绪")

    def _reset_to_draft(self):
        """重置为草稿窗口：清空 UI、重置当前会话指针、聚焦输入框。"""
        self._draft_project_path = self._get_project_path()
        self._draft_session_type = "work" if self._draft_project_path else "chat"
        self._orchestrator.clear_current()
        self.chat_area.clear_chat()
        self.chat_area.set_analyze_button_visible(self._draft_session_type == "work")
        QTimer.singleShot(0, self.chat_area.input_field.setFocus)

    def _on_conversation_selected(self, session_id: str):
        self._bus.emit(SessionSwitchEvent(new_session_id=session_id))

    def _on_conversation_deleted(self, session_id: str):
        self._bus.emit(SessionDeleteEvent(session_id=session_id))

    def _on_conversation_pinned(self, session_id: str, pinned: bool):
        self._bus.emit(SessionPinEvent(session_id=session_id, pinned=pinned))

    def _on_search_clicked(self):
        self._center_panel.header.focus_search()

    def _on_theme_changed(self, theme_name: str):
        """用户切换主题：应用新主题并持久化到 config.yaml。"""
        if theme_name not in THEMES or theme_name == self._theme_name:
            return
        self._theme_name = theme_name
        self._theme = THEMES[theme_name]
        self._apply_theme()
        self.conversation_list.set_theme(self._theme)
        self.chat_area.set_theme(theme_name)
        self.right_panel.set_theme(self._theme)
        self._config.set("app.theme", theme_name)
        self._config.save()

    def toggle_panels(self):
        """切换左右面板可见性，展开键图标通过 HeaderToolbar 更新。"""
        left_visible = self._left_panel.isVisible()
        right_visible = self._right_panel.isVisible()
        if left_visible or right_visible:
            # 当前处于展开态，收起两侧
            self._left_panel.hide()
            self._right_panel.hide()
            self._center_panel.header.update_expand_state(expanded=False)
        else:
            # 当前处于收起态，展开两侧
            self._left_panel.show()
            self._right_panel.show()
            self._center_panel.header.update_expand_state(expanded=True)

    def _on_send_message(self, user_text: str):
        """发送消息：草稿窗口首条消息会触发 orchestrator 创建会话。"""
        self.chat_area.clear_input()
        self._bus.emit(UserSendEvent(
            session_id="",
            user_text=user_text,
            mode=self._current_mode,
            session_type=self._draft_session_type,
            project_path=self._draft_project_path,
            model=self._current_model_name,
        ))

    def _on_stop_generation(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserStopEvent(session_id=current_sid))

    def _on_user_confirm(self, confirmed: bool):
        """用户点击确认/取消按钮：通知 Orchestrator 继续或中止 Phase。"""
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserConfirmEvent(session_id=current_sid, confirmed=confirmed))

    def _on_analyze_project(self):
        """用户点击「帮我分析当前项目」：直接向当前/草稿会话发送用户消息。"""
        self._bus.emit(UserSendEvent(
            session_id=self._orchestrator.current_session_id or "",
            user_text="帮我分析当前项目",
            mode=self._current_mode,
            session_type=self._draft_session_type,
            project_path=self._draft_project_path,
            model=self._current_model_name,
        ))

    def _on_export_session(self):
        """导出当前会话内容到文本文件。"""
        from PySide6.QtWidgets import QFileDialog
        sid = self._orchestrator.current_session_id
        if not sid:
            return
        messages = self._repo.get_messages(sid)
        lines = []
        for m in messages:
            role_label = {"user": "我", "ai": "AI", "system": "系统"}.get(m.role, m.role)
            lines.append(f"[{role_label}] {m.content}")
        text = "\n\n".join(lines)
        path, _ = QFileDialog.getSaveFileName(self, "导出会话", f"session_{sid[-8:]}.txt", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception as e:
                print(f"导出会话失败: {e}", flush=True)

    def _on_open_settings(self):
        """打开设置：临时通过终端面板提示用户（设置对话框待后续实现）。"""
        self._right_panel.update_terminal("[设置] 设置对话框将在后续版本提供。")

    def _on_model_changed(self, model_name: str):
        """用户切换模型：更新当前模型并持久化到 config.yaml。"""
        if not model_name or model_name == self._current_model_name:
            return
        self._current_model_name = model_name
        self._config.set("app.last_model", model_name)
        self._config.save()

    def _on_mode_changed(self, mode: str):
        """用户切换模式：更新当前模式并持久化到 config.yaml。"""
        if not mode or mode == self._current_mode:
            return
        self._current_mode = mode
        self._config.set("app.last_mode", mode)
        self._config.save()
