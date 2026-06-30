"""
main_window.py — v4 主窗口（薄编排层）

核心设计：
- 只做 UI 构建和信号路由，不做业务逻辑。
- 所有业务逻辑委托给 SessionOrchestrator，通过 MessageBus 事件驱动。
- 不保留任何 v2 Manager 状态。
- 会话切换不操作 Worker，只切 UI。
"""
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QStatusBar, QLabel, QStyleFactory,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QColor, QFont

from .repository import SessionRepository
from .event_bus import MessageBus
from .orchestrator import SessionOrchestrator
from .ui_renderer import UIRenderer
from .conversation_list import ConversationListWidget
from .events import (
    UserSendEvent, UserStopEvent,
    UserConfirmEvent, UserReanalyzeEvent, UserSkipVerifyEvent,
    SessionCreateEvent, SessionSwitchEvent, SessionDeleteEvent, SessionPinEvent,
)

# 接入现有 ChatView
from ui.chat_view import ChatView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1600, 950)
        self.setWindowTitle("AI Agent 工作台 v4.0")

        # 1. 初始化 v4 核心组件
        self._repo = SessionRepository()
        self._bus = MessageBus(trace=False)
        self._bus.connect_dispatch()
        self._orchestrator = SessionOrchestrator(
            repository=self._repo,
            message_bus=self._bus,
            parent=self,
        )

        self._apply_theme()
        self._setup_ui()

        self._ui_renderer = UIRenderer(
            message_bus=self._bus,
            chat_view=self.chat_view,
            status_indicator=self.status_indicator,
            conversation_list=self.conversation_list,
            capacity_label=self.capacity_label,
            queue_bar=self._queue_bar,
            current_session_provider=lambda: self._orchestrator.current_session_id or "",
            parent=self,
        )

        self._connect_signals()
        self._init_default_session()

    def _setup_ui(self):
        """布局：左侧会话列表、中间 ChatView、右侧工作区、底部状态栏。"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧会话列表
        self.conversation_list = ConversationListWidget()
        self.conversation_list.setFixedWidth(260)
        self.conversation_list.new_conversation.connect(self._on_new_conversation)
        self.conversation_list.conversation_selected.connect(self._on_conversation_selected)
        self.conversation_list.conversation_deleted.connect(self._on_conversation_deleted)
        self.conversation_list.conversation_pinned.connect(self._on_conversation_pinned)
        main_layout.addWidget(self.conversation_list)

        # 中间 ChatView
        self.chat_view = ChatView()
        self.chat_view.send_clicked.connect(self._on_send_message)
        self.chat_view.stop_requested.connect(self._on_stop_generation)
        self.chat_view.confirm_clicked.connect(self._on_confirm)
        self.chat_view.reanalyze_clicked.connect(self._on_reanalyze)
        self.chat_view.skip_verify_clicked.connect(self._on_skip_verify)
        main_layout.addWidget(self.chat_view, 1)

        # 右侧工作区
        self._workspace = QWidget()
        self._workspace.setMinimumWidth(300)
        main_layout.addWidget(self._workspace)

        # 底部状态栏
        self.status_bar = QStatusBar()
        self.status_indicator = QLabel("🟢 就绪")
        self.status_bar.addWidget(self.status_indicator, 1)
        self.capacity_label = QLabel("🟢 任务:0/5 | 槽位:0/5")
        self.status_bar.addPermanentWidget(self.capacity_label)
        self._queue_bar = QLabel("")
        self._queue_bar.setFont(QFont("Microsoft YaHei", 9))
        self._queue_bar.setStyleSheet("color: #888; padding: 2px 8px;")
        self._queue_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self._queue_bar)
        self.setStatusBar(self.status_bar)

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))
        p = QPalette()
        p.setColor(QPalette.Window, QColor("#0D1117"))
        p.setColor(QPalette.WindowText, QColor("#E6EDF3"))
        p.setColor(QPalette.Base, QColor("#161B22"))
        p.setColor(QPalette.Button, QColor("#21262D"))
        p.setColor(QPalette.Highlight, QColor("#58A6FF"))
        app.setPalette(p)

    def _connect_signals(self):
        self.chat_view.model_changed.connect(self._on_model_changed)
        self.chat_view.settings_clicked.connect(self._on_settings)

    def _init_default_session(self):
        """有会话则切换首个，无则发射 SessionCreateEvent 创建 chat 会话。"""
        sessions = self._repo.list_sessions()
        if sessions:
            self._on_conversation_selected(sessions[0].session_id)
        else:
            self._bus.emit(SessionCreateEvent(
                title="新对话",
                session_type="chat",
                project_path="",
                mode="ask",
                model="tool-agent",
            ))

    def _on_new_conversation(self, conv_type: str):
        """chat 则 project_path=''，work 则 project_path 来自 _get_project_path()。"""
        project_path = "" if conv_type == "chat" else self._get_project_path()
        self._bus.emit(SessionCreateEvent(
            title="新对话",
            session_type=conv_type,
            project_path=project_path,
            mode="ask",
            model="tool-agent",
        ))

    def _on_conversation_selected(self, session_id: str):
        self._bus.emit(SessionSwitchEvent(new_session_id=session_id))

    def _on_conversation_deleted(self, session_id: str):
        self._bus.emit(SessionDeleteEvent(session_id=session_id))

    def _on_conversation_pinned(self, session_id: str, pinned: bool):
        self._bus.emit(SessionPinEvent(session_id=session_id, pinned=pinned))

    def _on_send_message(self, user_text: str):
        """当前会话发送 UserSendEvent。"""
        current_sid = self._orchestrator.current_session_id
        if not current_sid:
            return
        self.chat_view.clear_input()
        self._bus.emit(UserSendEvent(
            session_id=current_sid,
            user_text=user_text,
            mode="ask",
        ))

    def _on_stop_generation(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserStopEvent(session_id=current_sid))

    def _on_confirm(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserConfirmEvent(session_id=current_sid, confirmed=True))

    def _on_reanalyze(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserReanalyzeEvent(session_id=current_sid))

    def _on_skip_verify(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserSkipVerifyEvent(session_id=current_sid))

    def _get_project_path(self) -> str:
        """获取当前项目路径（当前可返回空字符串）。"""
        return ""

    def _on_model_changed(self, model_name: str):
        pass

    def _on_settings(self):
        pass
