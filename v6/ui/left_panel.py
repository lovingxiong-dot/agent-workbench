"""v6/ui/left_panel.py — 左栏面板。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QStackedWidget, QPushButton,
)

from v6.ui.base import C, font, theme
from v6.ui.session_group import SessionGroup
from v6.ui.function_page import FunctionPage
from v6.ui.recent_files import RecentFiles
from v6.ui.tab_button import TabButton
from v6.ui.apple_menu import AppleMenu


class LeftPanel(QWidget):
    """左栏：Tab 切换、会话分组、功能页、文件管理器占位、底部主题切换。"""

    session_selected = Signal(str)
    new_session_requested = Signal()
    session_action = Signal(str, str)       # action, sid
    search_text_changed = Signal(str)
    theme_toggled = Signal(str)
    file_selected = Signal(str)
    tool_toggled = Signal(str, bool)
    mcp_toggled = Signal(str, bool)
    skill_clicked = Signal(str)
    automation_toggled = Signal(str, bool)

    DEMO_SESSIONS = [
        ("today", "今天", [
            {"sid": "s1", "title": "V6 架构讨论", "preview": "讨论 UI 分层与信号契约", "time": "10:23"},
            {"sid": "s2", "title": "base.py 实现", "preview": "主题系统与基础工具", "time": "09:15"},
        ]),
        ("yesterday", "昨天", [
            {"sid": "s3", "title": "窗口无边框方案", "preview": "FramelessWindowHelper 与边缘拖拽", "time": "昨天"},
            {"sid": "s4", "title": "AppleMenu 设计", "preview": "圆角阴影弹出菜单", "time": "昨天"},
        ]),
        ("last7", "最近 7 天", [
            {"sid": "s5", "title": "pytest smoke 测试", "preview": "验证所有模块可导入", "time": "周一"},
            {"sid": "s6", "title": "主题切换动画", "preview": "深浅色主题即时切换", "time": "周日"},
        ]),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(380)
        self._groups: list[SessionGroup] = []
        self._build()
        self.update_sessions(self.DEMO_SESSIONS)
        self._style()
        theme.changed.connect(self._style)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Tabs
        tab_layout = QHBoxLayout()
        self._tab_chat = TabButton("会话")
        self._tab_files = TabButton("文件")
        self._tab_func = TabButton("功能")
        self._tabs = [self._tab_chat, self._tab_files, self._tab_func]
        for i, btn in enumerate(self._tabs):
            btn.clicked.connect(lambda checked=False, idx=i: self._set_tab(idx))
            tab_layout.addWidget(btn)
        layout.addLayout(tab_layout)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索会话 / 文件...")
        self._search.textChanged.connect(self.search_text_changed.emit)
        layout.addWidget(self._search)

        # Stack
        self._stack = QStackedWidget()
        self._session_page = QWidget()
        self._session_layout = QVBoxLayout(self._session_page)
        self._session_layout.setContentsMargins(0, 0, 0, 0)
        self._session_layout.setSpacing(6)
        self._session_layout.addStretch(1)
        self._file_page = RecentFiles()
        self._file_page.file_selected.connect(self.file_selected.emit)
        self._func_page = FunctionPage()
        self._func_page.tool_toggled.connect(self.tool_toggled.emit)
        self._func_page.mcp_toggled.connect(self.mcp_toggled.emit)
        self._func_page.skill_clicked.connect(self.skill_clicked.emit)
        self._func_page.automation_toggled.connect(self.automation_toggled.emit)
        self._stack.addWidget(self._session_page)
        self._stack.addWidget(self._file_page)
        self._stack.addWidget(self._func_page)
        layout.addWidget(self._stack, 1)

        # Bottom
        bottom = QHBoxLayout()
        self._new_btn = QPushButton("+ 新会话")
        self._new_btn.setFont(font(11))
        self._new_btn.clicked.connect(self.new_session_requested.emit)
        self._theme_btn = QPushButton("主题")
        self._theme_btn.setFont(font(11))
        self._theme_btn.setFixedWidth(56)
        self._theme_btn.clicked.connect(self._toggle_theme)
        bottom.addWidget(self._new_btn)
        bottom.addStretch(1)
        bottom.addWidget(self._theme_btn)
        layout.addLayout(bottom)

        self._set_tab(0)

    def update_sessions(self, sessions: list[tuple[str, str, list[dict]]]) -> None:
        """重建会话分组列表。"""
        while self._groups:
            old = self._groups.pop()
            old.deleteLater()
        # remove stretch, add groups, then stretch back
        item = self._session_layout.takeAt(self._session_layout.count() - 1)
        if item:
            item.widget().deleteLater() if item.widget() else None
        for gid, title, items in sessions:
            group = SessionGroup(gid, title, items)
            group.session_selected.connect(self.session_selected.emit)
            group.context_menu_requested.connect(self._on_session_context)
            self._groups.append(group)
            self._session_layout.addWidget(group)
        self._session_layout.addStretch(1)

    def _set_tab(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._tabs):
            btn.set_active(i == index)

    def _toggle_theme(self) -> None:
        new_theme = "light" if theme.name == "dark" else "dark"
        self.theme_toggled.emit(new_theme)

    def _on_session_context(self, sid: str, pos: object) -> None:
        menu = AppleMenu(self)
        menu.add_item("置顶").clicked.connect(lambda: self.session_action.emit("pin", sid))
        menu.add_item("重命名").clicked.connect(lambda: self.session_action.emit("rename", sid))
        menu.add_separator()
        menu.add_item("删除").clicked.connect(lambda: self.session_action.emit("delete", sid))
        menu.show_at(pos)

    def set_active_session(self, sid: str) -> None:
        for group in self._groups:
            group.set_active(sid)

    def _style(self) -> None:
        self.setStyleSheet(
            f"LeftPanel {{ background-color: {C['bg_sidebar']}; border-right: 1px solid {C['border']}; }}"
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 6px 8px; }}"
            f"QLineEdit::placeholder {{ color: {C['text_muted']}; }}"
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 6px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.resize(320, 720)
    panel = LeftPanel()
    panel.session_selected.connect(lambda sid: print("session", sid))
    panel.session_action.connect(lambda a, sid: print("action", a, sid))
    panel.tool_toggled.connect(lambda t, e: print("tool", t, e))
    panel.skill_clicked.connect(lambda s: print("skill", s))
    panel.file_selected.connect(lambda p: print("file", p))
    panel.theme_toggled.connect(lambda t: print("theme", t))
    win.setCentralWidget(panel)
    win.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(1500, win.close)
    sys.exit(app.exec())
