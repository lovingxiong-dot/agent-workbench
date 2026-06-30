"""
conversation_list.py — v4 会话列表（Solo 极简风格 + 主题切换）

左栏只包含：
- 顶部小标题 + 模型下拉 + 🌙/☀️ 主题切换
- 中间「+ 新任务」按钮
- 下方会话列表（标题 + 简短预览 + 时间）
"""
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLabel, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .models import SessionMetadata


THEMES = {
    "dark": {
        "bg_sidebar": "#252526",
        "bg_widget": "#252526",
        "bg_input": "#2d2d30",
        "bg_hover": "#2a2d2e",
        "bg_selected": "#37373d",
        "border": "#3e3e42",
        "text_primary": "#cccccc",
        "text_secondary": "#858585",
        "accent": "#007acc",
        "accent_hover": "#1177bb",
        "new_task_btn": "#2d2d30",
        "new_task_hover": "#3e3e42",
    },
    "light": {
        "bg_sidebar": "#f3f3f3",
        "bg_widget": "#f3f3f3",
        "bg_input": "#ffffff",
        "bg_hover": "#e8e8e8",
        "bg_selected": "#e0e0e0",
        "border": "#e5e5e5",
        "text_primary": "#333333",
        "text_secondary": "#666666",
        "accent": "#007acc",
        "accent_hover": "#005a9e",
        "new_task_btn": "#ffffff",
        "new_task_hover": "#e8e8e8",
    },
}

DEFAULT_THEME = "dark"


class ConversationListWidget(QWidget):
    """Solo 风格会话列表

    信号：
    - new_task_clicked(): 用户点击「+ 新任务」
    - conversation_selected(session_id: str): 用户点击某个会话
    - conversation_deleted(session_id: str): 用户删除某个会话
    - conversation_pinned(session_id: str, pinned: bool): 用户置顶/取消置顶
    - model_changed(model_name: str): 用户切换模型
    - theme_changed(theme_name: str): 用户切换主题
    """

    new_task_clicked = Signal()
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)
    conversation_pinned = Signal(str, bool)
    model_changed = Signal(str)
    mode_changed = Signal(str)
    theme_changed = Signal(str)

    def __init__(self, theme: str = DEFAULT_THEME, parent=None):
        super().__init__(parent)
        self._theme_name = theme if theme in THEMES else DEFAULT_THEME
        self._theme = THEMES[self._theme_name]
        self._sessions: dict[str, SessionMetadata] = {}
        self._badges: dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(280)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 顶部：小标题 + 主题切换
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        header = QLabel("Agent")
        header.setStyleSheet(
            f"color: {self._theme['text_primary']}; font-size: 16px; font-weight: 600;"
        )
        top_row.addWidget(header)
        top_row.addStretch()

        self.theme_btn = QPushButton("🌙" if self._theme_name == "dark" else "☀️")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("切换主题")
        self.theme_btn.clicked.connect(self._on_theme_clicked)
        top_row.addWidget(self.theme_btn)
        layout.addLayout(top_row)

        # 模型下拉
        self.model_selector = QComboBox()
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_selector)

        # 模式下拉
        self.mode_selector = QComboBox()
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_selector)

        # 中间：+ 新任务
        self.new_task_btn = QPushButton("+ 新任务")
        self.new_task_btn.setCursor(Qt.PointingHandCursor)
        self.new_task_btn.clicked.connect(self.new_task_clicked.emit)
        layout.addWidget(self.new_task_btn)

        # 下方：会话列表
        self._list = QListWidget()
        self._list.setObjectName("conversationList")
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._list, 1)

        self._apply_theme_styles()

    def set_theme(self, theme_name: str):
        """切换主题并即时重绘样式。"""
        self._theme_name = theme_name if theme_name in THEMES else DEFAULT_THEME
        self._theme = THEMES[self._theme_name]
        self.theme_btn.setText("🌙" if self._theme_name == "dark" else "☀️")
        self._apply_theme_styles()
        self.refresh(list(self._sessions.values()))

    def _apply_theme_styles(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_sidebar']};")

        combo_style = f"""
            QComboBox {{
                background-color: {t['bg_input']}; color: {t['text_primary']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 6px 10px; font-size: 13px;
            }}
            QComboBox:hover {{ border: 1px solid {t['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{
                background-color: {t['bg_widget']}; color: {t['text_primary']};
                border: 1px solid {t['border']};
                selection-background-color: {t['accent']}33;
            }}
        """
        self.model_selector.setStyleSheet(combo_style)
        self.mode_selector.setStyleSheet(combo_style)

        self.new_task_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['new_task_btn']}; color: {t['text_primary']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 10px; font-size: 13px; font-weight: 500;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {t['new_task_hover']};
                border: 1px solid {t['accent']};
            }}
        """)

        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {t['text_secondary']};
                border: none; border-radius: 6px; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {t['bg_hover']}; color: {t['text_primary']}; }}
        """)

        self._list.setStyleSheet(f"""
            QListWidget {{
                background-color: {t['bg_sidebar']}; border: none; outline: none;
                color: {t['text_primary']}; font-size: 13px;
            }}
            QListWidget::item {{
                border-radius: 8px; padding: 10px 12px; margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background-color: {t['bg_selected']};
                border-left: 3px solid {t['accent']};
            }}
            QListWidget::item:hover {{
                background-color: {t['bg_hover']};
            }}
        """)

    def _on_theme_clicked(self):
        new_theme = "light" if self._theme_name == "dark" else "dark"
        self.theme_changed.emit(new_theme)

    def populate_models(self, providers: dict, current: str):
        """填充模型下拉框。"""
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        for name, cfg in providers.items():
            self.model_selector.addItem(f"{name}  ({cfg.get('model', '?')})", name)
        idx = self.model_selector.findData(current)
        if idx >= 0:
            self.model_selector.setCurrentIndex(idx)
        self.model_selector.blockSignals(False)

    # ── 数据刷新（全量）─────────────────────────────────
    def refresh(self, sessions: list[SessionMetadata]):
        """接收 SessionMetadata 列表，全量重建列表项，保持当前选中项。"""
        self._sessions = {s.session_id: s for s in sessions}

        current_sid = None
        current_item = self._list.currentItem()
        if current_item:
            current_sid = current_item.data(Qt.UserRole)

        self._list.clear()
        for s in sessions:
            item = self._create_item(s)
            self._list.addItem(item)
            if s.session_id == current_sid:
                self._list.setCurrentItem(item)

        for sid, phase in self._badges.items():
            self._update_badge_text(sid, phase)

    def _create_item(self, metadata: SessionMetadata) -> QListWidgetItem:
        title = metadata.title or "新对话"
        pin = "📌 " if metadata.pinned else ""
        preview = self._preview_text(metadata)
        time_str = self._format_time(metadata.updated_at)
        text = f"{pin}{title}\n{preview} · {time_str}"

        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, metadata.session_id)
        item.setToolTip(title)
        if metadata.pinned:
            item.setBackground(QColor(self._theme["bg_selected"]))
        return item

    def _preview_text(self, metadata: SessionMetadata) -> str:
        """生成简短预览。"""
        if metadata.project_path:
            return metadata.project_path[-30:] if len(metadata.project_path) > 30 else metadata.project_path
        return "新对话"

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

    # ── 徽章更新 ──────────────────────────────────
    def update_badge(self, session_id: str, phase: str):
        """更新会话状态徽章。"""
        self._badges[session_id] = phase
        self._update_badge_text(session_id, phase)

    def _update_badge_text(self, session_id: str, phase: str):
        """Solo 极简风格：不在列表项中显示 Phase 徽章。"""
        pass

    # ── 事件处理 ──────────────────────────────────
    def _on_item_clicked(self, item: QListWidgetItem):
        sid = item.data(Qt.UserRole)
        if sid:
            self.conversation_selected.emit(sid)

    def set_active_session(self, session_id: str):
        """设置当前选中项（不触发 itemClicked 信号）。"""
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self._list.blockSignals(True)
                self._list.setCurrentItem(item)
                self._list.blockSignals(False)
                break

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return

        sid = item.data(Qt.UserRole)
        metadata = self._sessions.get(sid)
        if not metadata:
            return

        menu = QMenu(self)
        pin_label = "📌 取消置顶" if metadata.pinned else "📌 置顶"
        pin_action = menu.addAction(pin_label)
        pin_action.triggered.connect(lambda: self.conversation_pinned.emit(sid, not metadata.pinned))

        delete_action = menu.addAction("🗑 删除")
        delete_action.triggered.connect(lambda: self.conversation_deleted.emit(sid))

        menu.exec(self._list.viewport().mapToGlobal(pos))

    def _on_model_changed(self, text: str):
        name = self.model_selector.currentData()
        if name:
            self.model_changed.emit(name)

    def populate_modes(self, modes: list[str], current: str):
        """填充模式下拉框。"""
        self.mode_selector.blockSignals(True)
        self.mode_selector.clear()
        for mode in modes:
            display = {"ask": "问答", "plan": "规划", "craft": "执行"}.get(mode, mode)
            self.mode_selector.addItem(display, mode)
        idx = self.mode_selector.findData(current)
        if idx >= 0:
            self.mode_selector.setCurrentIndex(idx)
        self.mode_selector.blockSignals(False)

    def _on_mode_changed(self, text: str):
        mode = self.mode_selector.currentData()
        if mode:
            self.mode_changed.emit(mode)
