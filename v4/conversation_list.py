"""
conversation_list.py — v4 会话列表

设计原则：
- 纯数据驱动：列表项由外部数据刷新，不主动维护状态
- 支持置顶：pinned 会话固定在最上方
- 支持重名：session_id 是唯一标识，标题不唯一
- 显示状态徽章：任务阶段（分析中/执行中/已完成等）
"""
from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
    QHBoxLayout, QPushButton, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .models import SessionMetadata


class ConversationListWidget(QWidget):
    """会话列表（纯数据驱动）

    信号：
    - new_conversation(conv_type: str): 用户请求新建会话（"chat" / "work"）
    - conversation_selected(session_id: str): 用户点击某个会话
    - conversation_deleted(session_id: str): 用户删除某个会话
    - conversation_pinned(session_id: str, pinned: bool): 用户置顶/取消置顶某个会话
    """

    new_conversation = Signal(str)
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)
    conversation_pinned = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions: dict[str, SessionMetadata] = {}
        self._badges: dict[str, str] = {}  # session_id → phase
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_layout = QHBoxLayout()
        self._btn_chat = self._make_btn("+ 纯对话", "chat")
        self._btn_work = self._make_btn("+ 项目对话", "work")
        btn_layout.addWidget(self._btn_chat)
        btn_layout.addWidget(self._btn_work)
        layout.addLayout(btn_layout)

        self._list = QListWidget()
        self._list.setObjectName("conversationList")
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._list)

    def _make_btn(self, text: str, conv_type: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.new_conversation.emit(conv_type))
        return btn

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
        prefix = "📌 " if metadata.pinned else ""
        icon = "💬" if metadata.session_type.value == "chat" else "🔧"
        env = f"  [{metadata.project_path}]" if metadata.project_path else ""
        text = f"{prefix}{icon} {metadata.title}{env}"

        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, metadata.session_id)
        if metadata.pinned:
            item.setBackground(QColor("#1C2128"))
        return item

    # ── 徽章更新 ──────────────────────────────────
    def update_badge(self, session_id: str, phase: str):
        """更新会话状态徽章。"""
        self._badges[session_id] = phase
        self._update_badge_text(session_id, phase)

    def _update_badge_text(self, session_id: str, phase: str):
        badge_map = {
            "idle": "",
            "analyzing": " 🔍",
            "confirming": " ⏸",
            "executing": " ⚙️",
            "verifying": " ✅",
            "archiving": " 📦",
            "completed": " ✓",
            "failed": " ✗",
            "cancelled": " ✗",
        }
        badge = badge_map.get(phase, "")

        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == session_id:
                text = item.text()
                for b in badge_map.values():
                    if b and text.endswith(b):
                        text = text[:-len(b)].rstrip()
                item.setText(text + badge)
                break

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
