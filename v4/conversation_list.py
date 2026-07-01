"""
conversation_list.py — v4 左栏会话列表

结构：
- Tab 行：功能 | 会话
- 工具行：搜索 / + 新会话 / ... 更多
- 内容区：功能占位页 或 分组折叠会话列表
- 底部：主题切换 / 设置

分组规则：按 project_path 基名分组，空路径归入「全局会话」。
"""
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMenu, QFrame, QStackedWidget, QButtonGroup, QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QFont

from .icons import svg_icon, svg_pixmap
from .models import SessionMetadata
from .repository import SessionRepository


DEFAULT_THEME = "dark"


class SessionItemWidget(QWidget):
    """单个会话项：标题 + 预览 + 时间。"""

    clicked = Signal(str)
    context_menu_requested = Signal(str, object)

    def __init__(self, session: SessionMetadata, preview: str, theme: dict, parent=None):
        super().__init__(parent)
        self._session_id = session.session_id
        self._pinned = session.pinned
        self._theme = theme
        self._setup_ui(session, preview)
        self._apply_theme()

    def _setup_ui(self, session: SessionMetadata, preview: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        title_text = ("📌 " if session.pinned else "") + (session.title or "新对话")
        self.title_label = QLabel(title_text[:24])
        self.title_label.setFont(self._font(12, bold=True))
        layout.addWidget(self.title_label)

        self.preview_label = QLabel(preview[:40] or "等待第一条消息...")
        self.preview_label.setFont(self._font(10))
        layout.addWidget(self.preview_label)

        self.time_label = QLabel(self._format_time(session.updated_at))
        self.time_label.setFont(self._font(9))
        layout.addWidget(self.time_label)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    @staticmethod
    def _font(size: int, bold: bool = False):
        from PySide6.QtGui import QFont
        f = QFont("Segoe UI", size)
        f.setBold(bold)
        return f

    @staticmethod
    def _format_time(ts: Optional[datetime]) -> str:
        if not ts:
            return ""
        now = datetime.now()
        if ts.date() == now.date():
            return ts.strftime("%H:%M")
        if ts.year == now.year:
            return ts.strftime("%m-%d")
        return ts.strftime("%Y-%m-%d")

    def _apply_theme(self):
        t = self._theme
        self.title_label.setStyleSheet(f"color: {t['text_primary']};")
        self.preview_label.setStyleSheet(f"color: {t['text_secondary']};")
        self.time_label.setStyleSheet(f"color: {t.get('text_muted', t['text_secondary'])};")
        # SVG: inactive bg=#16213e, border=#2a2a4a, rx=6
        self.setStyleSheet(
            f"SessionItemWidget {{ background-color: {t['bg_sidebar']}; border: 0.5px solid {t['border']}; "
            f"border-radius: 6px; }}"
            f"SessionItemWidget:hover {{ background-color: {t['bg_hover']}; }}"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def set_active(self, active: bool):
        t = self._theme
        if active:
            self.setStyleSheet(
                f"SessionItemWidget {{ background-color: {t['bg_selected']}; "
                f"border: 0.5px solid {t['accent']}; border-radius: 6px; }}"
                f"SessionItemWidget:hover {{ background-color: {t['bg_selected']}; }}"
            )
        else:
            self._apply_theme()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._session_id)
        super().mousePressEvent(event)

    def _on_context_menu(self, pos):
        self.context_menu_requested.emit(self._session_id, self.mapToGlobal(pos))


class SessionGroupWidget(QWidget):
    """可折叠会话分组。"""

    toggled = Signal(str, bool)
    session_selected = Signal(str)
    session_context_menu_requested = Signal(str, object)

    def __init__(self, group_name: str, sessions: list, preview_provider, theme: dict, parent=None):
        super().__init__(parent)
        self._group_name = group_name
        self._expanded = True
        self._theme = theme
        self._preview_provider = preview_provider
        self._items: dict[str, SessionItemWidget] = {}
        self._setup_ui()
        self._apply_theme()
        self.update_sessions(sessions)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 分组头部
        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedSize(18, 18)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFlat(True)
        self.toggle_btn.clicked.connect(self._on_toggle)
        header_layout.addWidget(self.toggle_btn)

        self.name_label = QLabel(self._group_name)
        from PySide6.QtGui import QFont
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        self.name_label.setFont(f)
        header_layout.addWidget(self.name_label, 1)

        self.count_label = QLabel("0")
        self.count_label.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(self.count_label)

        self.header.mousePressEvent = self._header_clicked
        layout.addWidget(self.header)

        # 分隔线
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.HLine)
        self.sep.setFixedHeight(1)
        layout.addWidget(self.sep)

        # 会话列表
        self.items_layout = QVBoxLayout()
        self.items_layout.setContentsMargins(4, 4, 4, 4)
        self.items_layout.setSpacing(4)
        self.items_layout.addStretch()
        layout.addLayout(self.items_layout)

    def _header_clicked(self, event):
        self._on_toggle()

    def _on_toggle(self):
        self._expanded = not self._expanded
        self.toggle_btn.setText("▼" if self._expanded else "▶")
        for i in range(self.items_layout.count()):
            item = self.items_layout.itemAt(i).widget()
            if item:
                item.setVisible(self._expanded)
        self.toggled.emit(self._group_name, self._expanded)

    def _apply_theme(self):
        t = self._theme
        self.header.setStyleSheet(f"background-color: {t.get('bg_group_header', t['bg_sidebar'])}; border-radius: 4px;")
        self.name_label.setStyleSheet(f"color: {t['text_secondary']};")
        self.count_label.setStyleSheet(f"color: {t.get('text_muted', t['text_secondary'])};")
        self.toggle_btn.setStyleSheet(
            f"QPushButton {{ color: {t['text_secondary']}; background: transparent; border: none; font-size: 10px; }}"
        )
        self.sep.setStyleSheet(f"background-color: {t['border']};")

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()
        for item in self._items.values():
            item.set_theme(theme)

    def update_sessions(self, sessions: list[SessionMetadata]):
        # 清空旧项（保留 stretch）
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()

        for s in sessions:
            preview = self._preview_provider(s) if self._preview_provider else ""
            item = SessionItemWidget(s, preview, self._theme)
            item.clicked.connect(self.session_selected.emit)
            item.context_menu_requested.connect(self.session_context_menu_requested.emit)
            item.setVisible(self._expanded)
            self.items_layout.insertWidget(self.items_layout.count() - 1, item)
            self._items[s.session_id] = item

        self.count_label.setText(str(len(sessions)))

    def set_active_session(self, session_id: str):
        for sid, item in self._items.items():
            item.set_active(sid == session_id)


class FunctionPageWidget(QWidget):
    """「功能」Tab 页：工具 / MCP / 技能 / 自动化，带状态徽章。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._rows: list[tuple[QWidget, str, Optional[QLabel]]] = []
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        sections = [
            ("工具", [
                ("run_command", "开"),
                ("grep_files", "关"),
                ("write_file", "开"),
            ], "dot"),
            ("MCP", [
                ("GitHub", "已连接"),
                ("Notion", "未连接"),
            ], "dot"),
            ("技能", [
                ("archive", ""),
                ("handoff", ""),
                ("gitops", ""),
            ], "lightning"),
            ("自动化", [
                ("每日日报", "08:00"),
            ], "dot"),
        ]

        for title, items, icon_type in sections:
            header = QLabel(title)
            from PySide6.QtGui import QFont
            f = QFont("Segoe UI", 9)
            f.setBold(True)
            header.setFont(f)
            layout.addWidget(header)

            for name, status in items:
                row, badge = self._build_item_row(name, status, icon_type)
                layout.addWidget(row)
                self._rows.append((row, icon_type, badge))

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFixedHeight(1)
            layout.addWidget(line)
            self._rows.append((line, "sep", None))

        layout.addStretch()

    def _build_item_row(self, name: str, status: str, icon_type: str) -> tuple[QWidget, Optional[QLabel]]:
        row = QWidget()
        row.setFixedHeight(24)  # SVG: h=24
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 0, 10, 0)
        row_layout.setSpacing(8)

        if icon_type == "lightning":
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setAlignment(Qt.AlignCenter)
        else:
            dot = QLabel("●")
            dot.setFixedWidth(12)
        row_layout.addWidget(dot)

        label = QLabel(name)
        label.setFont(QFont("Segoe UI", 11))
        row_layout.addWidget(label, 1)

        badge: Optional[QLabel] = None
        if status:
            badge = QLabel(status)
            badge.setFont(QFont("Segoe UI", 9))
            row_layout.addWidget(badge)

        return row, badge

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_sidebar']};")
        icon_color = t.get("text_secondary", "#a0a0b0")
        accent = t.get("accent", "#007acc")
        muted = t.get("text_muted", t['text_secondary'])

        for widget, icon_type, badge in self._rows:
            if icon_type == "sep":
                widget.setStyleSheet(f"background-color: {t['border']};")
                continue
            row = widget.layout()
            dot = row.itemAt(0).widget()
            label = row.itemAt(1).widget()
            # SVG: row background fill=#0f3460 stroke=#2a2a4a rx=4
            widget.setStyleSheet(
                f"QWidget {{ background-color: {t.get('tag_bg', '#0f3460')}; "
                f"border: 0.5px solid {t['border']}; border-radius: 4px; }}"
            )
            if icon_type == "lightning":
                dot.setPixmap(svg_pixmap("lightning", icon_color, 10))
            else:
                dot.setStyleSheet(f"color: {accent}; background: transparent; border: none;")
            label.setStyleSheet(f"color: {t['text_secondary']}; background: transparent; border: none;")
            if badge is not None:
                text = badge.text()
                if text in ("开", "已连接"):
                    badge.setStyleSheet(f"color: {t.get('card_archive_border', '#4ec9b0')};")
                elif text in ("关", "未连接"):
                    badge.setStyleSheet(f"color: {muted};")
                else:
                    badge.setStyleSheet(f"color: {t['text_secondary']};")

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()


class ConversationListWidget(QWidget):
    """v4 左栏：Tab + 工具行 + 分组会话列表/功能页 + 底部控制。"""

    new_task_clicked = Signal()
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)
    conversation_pinned = Signal(str, bool)
    theme_changed = Signal(str)
    search_clicked = Signal()
    more_clicked = Signal()
    tab_changed = Signal(str)

    def __init__(self, theme: dict = None, repository: SessionRepository = None, parent=None):
        super().__init__(parent)
        self._theme = theme or {}
        self._repo = repository
        self._sessions: dict[str, SessionMetadata] = {}
        self._badges: dict[str, str] = {}
        self._active_session_id: str = ""
        self._current_tab = "会话"
        self.setFixedWidth(220)
        self._setup_ui()
        self._apply_theme()

    # ═══════════════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════════════
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Tab 行 ──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        self.function_tab_btn = QPushButton("功能")
        self.function_tab_btn.setCheckable(True)
        self.function_tab_btn.setCursor(Qt.PointingHandCursor)
        self.function_tab_btn.setMinimumWidth(80)
        self.function_tab_btn.clicked.connect(lambda: self._on_tab_changed("功能"))
        self.tab_group.addButton(self.function_tab_btn)
        tab_row.addWidget(self.function_tab_btn, 1)

        self.session_tab_btn = QPushButton("会话")
        self.session_tab_btn.setCheckable(True)
        self.session_tab_btn.setChecked(True)
        self.session_tab_btn.setCursor(Qt.PointingHandCursor)
        self.session_tab_btn.setMinimumWidth(80)
        self.session_tab_btn.clicked.connect(lambda: self._on_tab_changed("会话"))
        self.tab_group.addButton(self.session_tab_btn)
        tab_row.addWidget(self.session_tab_btn, 1)

        layout.addLayout(tab_row)

        # ── 工具行 ──
        tool_row = QHBoxLayout()
        tool_row.setSpacing(6)

        self.search_btn = QPushButton()
        self.search_btn.setFixedSize(28, 22)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setToolTip("搜索")
        self.search_btn.setIconSize(QSize(14, 14))
        self.search_btn.setIcon(svg_icon("search", self._theme.get("text_secondary", "#a0a0b0"), 14))
        self.search_btn.clicked.connect(self.search_clicked.emit)
        tool_row.addWidget(self.search_btn)

        self.new_task_btn = QPushButton("+ 新会话")
        self.new_task_btn.setFixedHeight(22)
        self.new_task_btn.setCursor(Qt.PointingHandCursor)
        self.new_task_btn.clicked.connect(self.new_task_clicked.emit)
        tool_row.addWidget(self.new_task_btn, 1)

        self.more_btn = QPushButton()
        self.more_btn.setFixedSize(28, 22)
        self.more_btn.setCursor(Qt.PointingHandCursor)
        self.more_btn.setToolTip("更多")
        self.more_btn.setIconSize(QSize(14, 14))
        self.more_btn.setIcon(svg_icon("more", self._theme.get("text_secondary", "#a0a0b0"), 14))
        self.more_btn.clicked.connect(self._on_more_clicked)
        tool_row.addWidget(self.more_btn)

        layout.addLayout(tool_row)

        # SVG: 工具行下分隔线 y=76 (stroke=#2a2a4a 0.5px)
        self.tool_sep = QFrame()
        self.tool_sep.setFrameShape(QFrame.HLine)
        self.tool_sep.setFixedHeight(1)
        layout.addWidget(self.tool_sep)

        # ── 内容区 ──
        self.stack = QStackedWidget()

        self.function_page = FunctionPageWidget(self._theme)
        self.stack.addWidget(self.function_page)

        self.session_container = QWidget()
        self.session_layout = QVBoxLayout(self.session_container)
        self.session_layout.setContentsMargins(0, 0, 0, 0)
        self.session_layout.setSpacing(8)
        self.session_layout.addStretch()
        self.stack.addWidget(self.session_container)

        layout.addWidget(self.stack, 1)

        # ── 底部控制 ──
        # SVG: 分隔线 y=700
        self.bottom_sep = QFrame()
        self.bottom_sep.setFrameShape(QFrame.HLine)
        self.bottom_sep.setFixedHeight(1)
        layout.addWidget(self.bottom_sep)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.addStretch()

        self.theme_btn = QPushButton("🌙" if self._is_dark() else "☀️")
        self.theme_btn.setFixedSize(32, 12)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("切换主题")
        self.theme_btn.clicked.connect(self._on_theme_clicked)
        bottom_row.addWidget(self.theme_btn)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 12)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("设置")
        bottom_row.addWidget(self.settings_btn)

        layout.addLayout(bottom_row)

        # 更多菜单
        self._setup_more_menu()

    def _setup_more_menu(self):
        self.more_menu = QMenu(self)
        self.action_export = QAction("导出当前会话", self)
        self.action_copy = QAction("复制会话内容", self)
        self.action_settings = QAction("打开设置", self)
        self.action_theme = QAction("切换主题", self)
        self.more_menu.addAction(self.action_export)
        self.more_menu.addAction(self.action_copy)
        self.more_menu.addSeparator()
        self.more_menu.addAction(self.action_settings)
        self.more_menu.addAction(self.action_theme)
        self.action_theme.triggered.connect(self._on_theme_clicked)

    def _on_more_clicked(self):
        self.more_clicked.emit()
        self.more_menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))

    def _on_tab_changed(self, tab_name: str):
        self._current_tab = tab_name
        if tab_name == "功能":
            self.stack.setCurrentIndex(0)
            self.function_tab_btn.setChecked(True)
        else:
            self.stack.setCurrentIndex(1)
            self.session_tab_btn.setChecked(True)
        self.tab_changed.emit(tab_name)

    # ═══════════════════════════════════════════════════
    # 主题
    # ═══════════════════════════════════════════════════
    def _is_dark(self) -> bool:
        bg = self._theme.get("bg_sidebar", "#252526").lower()
        return bg in ("#16213e", "#252526", "#1e1e1e", "#1a1a2e", "#0f1729")

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()
        self.function_page.set_theme(theme)
        for group in self._iter_groups():
            group.set_theme(theme)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_sidebar']};")

        tab_base = (
            f"QPushButton {{ background-color: {t['bg_sidebar']}; color: {t['text_secondary']}; "
            f"border: 0.5px solid {t['border']}; border-radius: 6px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 500; "
            f"min-width: 88px; max-width: 96px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
            f"QPushButton:checked {{ background-color: {t['accent']}; color: #ffffff; border-color: {t['accent']}; font-weight: 600; }}"
        )
        self.function_tab_btn.setStyleSheet(tab_base)
        self.session_tab_btn.setStyleSheet(tab_base)

        tool_btn_style = (
            f"QPushButton {{ background-color: {t['bg_primary']}; color: {t['text_secondary']}; "
            f"border: 0.5px solid {t['border']}; border-radius: 6px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        self.search_btn.setStyleSheet(tool_btn_style)
        self.search_btn.setIcon(svg_icon("search", t.get("text_secondary", "#a0a0b0"), 14))
        # SVG: "+ 新会话" 按钮带 accent 边框
        self.new_task_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['bg_primary']}; color: {t['text_secondary']}; "
            f"border: 0.5px solid {t['accent']}; border-radius: 6px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        self.more_btn.setStyleSheet(tool_btn_style)
        self.more_btn.setIcon(svg_icon("more", t.get("text_secondary", "#a0a0b0"), 14))

        bottom_style = (
            f"QPushButton {{ background-color: {t.get('tag_bg', t['bg_input'])}; color: {t.get('tag_text', t['text_secondary'])}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; font-size: 10px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        self.theme_btn.setStyleSheet(bottom_style)
        self.settings_btn.setStyleSheet(bottom_style)
        self.theme_btn.setText("🌙" if self._is_dark() else "☀️")
        # 分隔线
        self.tool_sep.setStyleSheet(f"background-color: {t['border']};")
        self.bottom_sep.setStyleSheet(f"background-color: {t['border']};")

    def _on_theme_clicked(self):
        new_theme = "light" if self._is_dark() else "dark"
        self.theme_changed.emit(new_theme)

    # ═══════════════════════════════════════════════════
    # 数据刷新
    # ═══════════════════════════════════════════════════
    def refresh(self, sessions: list[SessionMetadata]):
        self._sessions = {s.session_id: s for s in sessions}

        # 清空现有分组
        while self.session_layout.count() > 1:
            item = self.session_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 按 project_path 分组
        groups: dict[str, list[SessionMetadata]] = {}
        global_sessions = []
        for s in sessions:
            if s.pinned:
                # 置顶项仍然保留在对应组内，排序时靠前
                pass
            if s.project_path:
                name = self._group_name(s.project_path)
                groups.setdefault(name, []).append(s)
            else:
                global_sessions.append(s)

        # 排序：组内按 pinned 降序 + updated_at 降序
        def sort_key(s: SessionMetadata):
            ts = (s.updated_at or datetime.max).timestamp()
            return (not s.pinned, -ts)

        for name in sorted(groups.keys()):
            groups[name].sort(key=sort_key)
        global_sessions.sort(key=sort_key)

        # 先添加有项目的分组，再添加全局会话
        for name in sorted(groups.keys()):
            self._add_group(name, groups[name])
        if global_sessions:
            self._add_group("全局会话", global_sessions)

        self.set_active_session(self._active_session_id)

    def _group_name(self, project_path: str) -> str:
        import os
        return os.path.basename(project_path) or project_path

    def _add_group(self, name: str, sessions: list[SessionMetadata]):
        group = SessionGroupWidget(
            name, sessions, self._preview_text, self._theme, parent=self.session_container
        )
        group.session_selected.connect(self._on_session_selected)
        group.session_context_menu_requested.connect(self._on_session_context_menu)
        self.session_layout.insertWidget(self.session_layout.count() - 1, group)

    def _iter_groups(self):
        for i in range(self.session_layout.count()):
            w = self.session_layout.itemAt(i).widget()
            if isinstance(w, SessionGroupWidget):
                yield w

    def _preview_text(self, metadata: SessionMetadata) -> str:
        if self._repo:
            last_msg = self._repo.get_last_message(metadata.session_id)
            if last_msg:
                print(f"[DEBUG preview] sid={metadata.session_id[-8:]} role={last_msg.role} content={last_msg.content[:30]!r}", flush=True)
                return last_msg.content[:40]
        if metadata.project_path:
            return metadata.project_path[-30:] if len(metadata.project_path) > 30 else metadata.project_path
        return ""

    # ═══════════════════════════════════════════════════
    # 事件处理
    # ═══════════════════════════════════════════════════
    def _on_session_selected(self, session_id: str):
        self._active_session_id = session_id
        self.conversation_selected.emit(session_id)
        self.set_active_session(session_id)

    def _on_session_context_menu(self, session_id: str, global_pos):
        metadata = self._sessions.get(session_id)
        if not metadata:
            return
        menu = QMenu(self)
        pin_label = "📌 取消置顶" if metadata.pinned else "📌 置顶"
        pin_action = menu.addAction(pin_label)
        pin_action.triggered.connect(lambda: self.conversation_pinned.emit(session_id, not metadata.pinned))
        delete_action = menu.addAction("🗑 删除")
        delete_action.triggered.connect(lambda: self.conversation_deleted.emit(session_id))
        menu.exec(global_pos)

    def set_active_session(self, session_id: str):
        self._active_session_id = session_id
        for group in self._iter_groups():
            group.set_active_session(session_id)

    # ═══════════════════════════════════════════════════
    # 兼容旧 API（将逐步移除）
    # ═══════════════════════════════════════════════════
    def populate_models(self, providers: dict, current: str):
        pass

    def populate_modes(self, modes: list[str], current: str):
        pass

    def update_badge(self, session_id: str, phase: str):
        self._badges[session_id] = phase
