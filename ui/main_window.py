"""
主窗口 — AI Agent 工作台
整合所有模块化组件，管理全局状态
"""
import os
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QStackedWidget, QMessageBox, QLabel,
    QStyleFactory,
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPalette, QColor, QFont

from services.pending_queue import PendingQueue, PendingTask
from services.self_context import SelfContext

from agent_engine import ModeManager, LLMRegistry, MemoryManager
from agent_engine.phase_manager import PhaseManager, TaskItem
from services.app_context import AppContext
from services.config_service import ConfigService
from services.session_service import SessionService
from services.theme_service import ThemeService
from services.project_service import ProjectService
from services.activity_service import ActivityService
from services.context_service import ContextService
from services.interpreter_service import InterpreterService
from services.metrics_collector import MetricsCollector, TurnMetrics
from services.persistence_service import PersistenceService
from services.mcp_service import MCPRegistry
from agent_engine.tool_gateway import ToolGateway
from services.task_service import TaskService, ResourceError
from workers.agent_worker import AgentWorker, TOOL_DEFINITIONS
from workers.task_capacity import TaskCapacity
from workers.worker_pool import WorkerPool
from workers.session_task import SessionTask, TaskStatus
from tools import ARUN_MAP
from ui.widgets import (
    SidebarButton, FileTreeWidget, ConversationListWidget,
    TaskListWidget, TerminalWidget, StatusIndicator,
    WorkspaceWidget,
)
from ui.dialogs import SettingsDialog, ProviderFormDialog
from ui.chat_view import ChatView
from ui.managers.session_manager import SessionManager
from ui.managers.ui_renderer import UIRenderer
from core.event_bus import MessageBus
from core.events import (
    UserSendEvent,
    UserStopEvent,
    UserConfirmEvent,
    UserReanalyzeEvent,
    UserSkipVerifyEvent,
    SessionCreateEvent,
    SessionSwitchEvent,
    SessionDeleteEvent,
    UIAppendUserEvent,
    UIAppendAIEvent,
    UIAppendSystemEvent,
    UIStreamChunkEvent,
    UIFinalizeStreamEvent,
    UISetStreamingEvent,
    UIClearPhaseUIEvent,
    UIHideConfirmationEvent,
    UIHideSkipVerifyEvent,
)
from tools.system import run_command, run_as_admin
from tools.system import read_file, write_file, list_dir, web_fetch
from tools.system import clipboard_read, clipboard_write, send_notification
from tools.system import list_processes, kill_process
from tools.quant import fetch_stock_data, run_backtest
from tools.mt5 import mt5_get_price, mt5_place_order
from tools.external_apis import fetch_financial_news, fetch_macro_data


# ── 工具注册表 ──────────────────────────────────────
TOOL_MAP = {
    "run_command": run_command,
    "run_as_admin": run_as_admin,
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "web_fetch": web_fetch,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "send_notification": send_notification,
    "list_processes": list_processes,
    "kill_process": kill_process,
    "fetch_stock_data": fetch_stock_data,
    "run_backtest": run_backtest,
    "mt5_get_price": mt5_get_price,
    "mt5_place_order": mt5_place_order,
    "fetch_financial_news": fetch_financial_news,
    "fetch_macro_data": fetch_macro_data,
}


def resource_path(relative_path):
    """资源路径（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


class MainWindow(QMainWindow):
    def __init__(self, app_context=None, session_orchestrator=None):
        super().__init__()
        self.resize(1600, 950)

        # ── v3 注入点 ───────────────────────────
        self._app_ctx = app_context
        self._orchestrator = session_orchestrator

        # ── 基础路径与配置 ──────────────────────
        if self._app_ctx is not None:
            config_path = app_context.config_path
            config_write = app_context.writable_config_path
            self.config_service = app_context.config_service
            self.persistence_service = PersistenceService(self.config_service)
            self._app_storage_dir = app_context.storage_dir
            app_root = app_context.app_root
        else:
            config_path = resource_path("config.yaml")
            config_write = (
                os.path.join(os.path.dirname(sys.executable), "config.yaml")
                if getattr(sys, 'frozen', False)
                else config_path
            )
            self.config_service = ConfigService(config_path, writable_path=config_write)
            self.persistence_service = PersistenceService(self.config_service)
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self._app_storage_dir = (
                os.path.join(os.path.dirname(sys.executable), "storage")
                if getattr(sys, 'frozen', False)
                else os.path.join(app_root, "storage")
            )
            os.makedirs(self._app_storage_dir, exist_ok=True)

        # 窗口标题动态读取版本号（必须在 config_service 初始化之后）
        app_version = self.config_service.get("app.version", "v3.x")
        self.setWindowTitle(f"AI Agent 工作台 {app_version} · 手动模式")

        # ── 服务初始化 ──────────────────────────
        if self._app_ctx is not None:
            self.session_service = app_context.session_service
            self.project_service = app_context.project_service
            self._project_root = app_context.project_root()
            self.context_service = app_context.context_service
            self.interpreter_service = app_context.interpreter_service
            self.activity_service = app_context.activity_service
            self.theme_service = app_context.theme_service
            self.mode_manager = app_context.mode_manager
            self.llm_registry = app_context.llm_registry
            self.memory_manager = app_context.memory_manager
            self.metrics_collector = app_context.metrics_collector
            self.tool_gateway = app_context.tool_gateway
            self.mcp_registry = app_context.mcp_registry
        else:
            self.session_service = SessionService(os.path.join(self._app_storage_dir, "conversations.db"))
            self.project_service = ProjectService(self.session_service, self.config_service)

            # 先确定项目根目录，后续服务依赖它
            self._project_root = self.project_service.detect_current_project(app_root)

            self.context_service = ContextService(self.project_service, self)
            self.interpreter_service = InterpreterService(self._project_root, self.config_service)
            self.interpreter_service.discover()
            self.context_service.set_interpreter_service(self.interpreter_service)

            self.activity_service = ActivityService(os.path.join(self._app_storage_dir, "activities.json"))
            self.theme_service = ThemeService()
            self.mode_manager = ModeManager(config_path)
            self.llm_registry = LLMRegistry(config_path, config_write)
            self.memory_manager = MemoryManager(
                self.config_service.get("memory", {}),
                storage_dir=self._app_storage_dir,
            )
            self.metrics_collector = MetricsCollector()

            # ── 工具网关与外部能力接入点 ─────────────────────────────
            self.tool_gateway = ToolGateway()
            self.tool_gateway.register_local_tools(TOOL_MAP, ARUN_MAP, TOOL_DEFINITIONS)
            self.mcp_registry = MCPRegistry()
            self.tool_gateway.register_mcp_registry(self.mcp_registry)

        # 全局状态
        self._current_mode = "ask"
        self._current_llm = None
        self._current_tools = []
        self._current_model_name = "tool-agent"
        self._worker = None  # Active AgentWorker
        self._workers = {}   # session_id → AgentWorker (all active)
        self._tools_in_use = 0
        self._chunks_received = False
        self._pending_metrics = None  # 等待 AI 回复完成后显示的 metrics
        self._phase_manager = PhaseManager(self)
        self._current_phase = "idle"
        self._phase_task_list = []
        self._phase_results = []

        # ── 多任务管理系统 (v3.9) ────────────────────
        if self._app_ctx is not None:
            self.task_service = app_context.task_service
            self.worker_pool = None
            # 向 v3 WorkerManager 注入工具注册表
            app_context.worker_manager.set_tool_map(TOOL_MAP)
        else:
            self.task_service = TaskService(capacity=TaskCapacity.from_config(self.config_service))
            self.worker_pool = WorkerPool(
                max_workers=self.config_service.get("task", {}).get("capacity", {}).get("max_concurrent_tasks", 3)
            )
            self.task_service.set_pool(self.worker_pool)

        # ── 双槽位等待队列 + 自识别上下文 (v3.10) ──────
        self._pending_queue = PendingQueue(self)
        self._pending_queue.queue_changed.connect(self._on_queue_changed, Qt.QueuedConnection)
        self._pending_queue.task_started.connect(self._on_queue_task_started, Qt.QueuedConnection)

        self._self_context = SelfContext(
            context_service=self.context_service,
            task_service=self.task_service,
            config=self.config_service.get("self_context", {}),
        )
        self.context_service._self_context = self._self_context  # 注入到 ContextService

        # UI 配置
        ui_cfg = self.config_service.get("ui", {}).get("log_panel", {})
        self._log_panel_visible = ui_cfg.get("visible", True)
        self._log_max_lines = ui_cfg.get("max_lines", 500)

        # ── UI 构建 ─────────────────────────────
        self._apply_theme()
        self._setup_ui()

        # ── SessionManager（v3.11: 绞杀者模式，依赖 _setup_ui 创建的 conversation_list）──
        self._session_mgr = SessionManager(
            session_service=self.session_service,
            project_service=self.project_service,
            context_service=self.context_service,
            memory_manager=self.memory_manager,
            conversation_list_widget=self.conversation_list,
            parent=self,
        )

        # ── v3 Orchestrator 生命周期镜像 ──────────
        self._v3_enabled = self._orchestrator is not None
        self._ui_renderer = None
        if self._v3_enabled:
            self._ui_renderer = UIRenderer(
                message_bus=self._app_ctx.message_bus,
                chat_view=self.chat_view,
                status_indicator=self.status_indicator,
                conversation_list=self.conversation_list,
                capacity_label=self.capacity_label,
                queue_bar=self._queue_bar,
                current_session_provider=lambda: self._current_session,
                parent=self,
            )
            self._connect_orchestrator()

        # ── 连接信号 ────────────────────────────
        self.chat_view.model_changed.connect(self._on_model_changed)
        self.chat_view.settings_clicked.connect(self._open_settings)
        self.chat_view.stop_requested.connect(self._on_stop_generation)
        self.chat_view.log_panel_toggled.connect(self._toggle_log_panel)
        self.chat_view.set_log_panel_checked(self._log_panel_visible)
        self.chat_view.confirm_clicked.connect(self._on_phase_confirmed)
        self.chat_view.reanalyze_clicked.connect(self._on_phase_reanalyze)
        self.chat_view.skip_verify_clicked.connect(self._on_phase_skip_verify)
        self.context_service.context_changed.connect(self._on_context_changed)
        self.workspace.terminal.interpreter_changed.connect(self._on_interpreter_changed)
        self.workspace.document_opened.connect(self._on_document_opened)
        self.workspace.document_closed.connect(self._on_document_closed)

        # PhaseManager 信号（v3 路径下由 SessionRuntime 内的 PhaseCoordinator 接管）
        if not self._v3_enabled:
            self._phase_manager.phase_changed.connect(self._on_phase_changed)
            self._phase_manager.analyze_required.connect(self._on_analyze_required)
            self._phase_manager.confirm_required.connect(self._on_confirm_required)
            self._phase_manager.execute_required.connect(self._on_execute_required)
            self._phase_manager.verify_required.connect(self._on_verify_required)
            self._phase_manager.archive_required.connect(self._on_archive_required)
            self._phase_manager.flow_finished.connect(self._on_phase_flow_finished)
            self._phase_manager.error_occurred.connect(self._on_phase_error)

        # v3.9 多任务管理系统 — TaskService 信号连接
        self.task_service.task_status_changed.connect(
            self._on_task_status_changed
        )
        self.task_service.capacity_changed.connect(
            self._on_capacity_changed
        )
        self.task_service.task_progress.connect(
            self._on_task_progress_signal
        )
        self.task_service.tool_usage_changed.connect(
            self._on_tool_usage_changed
        )
        self.task_service.task_completed.connect(
            self._on_task_service_completed
        )

        # ── 初始化 ──────────────────────────────
        # 从配置恢复上次选择的模式和模型；若无效则回退到 ask/tool-agent
        available_modes = list(self.config_service.get("manual_modes", {}).keys())
        providers = self.llm_registry.list_providers()
        last_mode, last_model = self.persistence_service.resolve_start_mode_model(
            available_modes,
            list(providers.keys()),
            defaults=("ask", next(iter(providers.keys()), "tool-agent")),
        )
        self._init_mode(last_mode, last_model)
        self._init_default_session()
        self.chat_view.populate_models(
            self.llm_registry.list_providers(),
            self._current_model_name
        )

        # ── 持久化恢复 ──────────────────────────
        self._restore_conversations()

        # ── 全局启动事件 ─────────────────────────
        self._on_log_message(f"🚀 程序启动: {self.windowTitle()}", is_header=True, is_global=True)

    # ── SessionManager 代理属性（绞杀者模式：兼容旧代码）──
    @property
    def _current_session(self) -> str:
        return self._session_mgr.current_session

    @_current_session.setter
    def _current_session(self, value: str):
        self._session_mgr.current_session = value

    @property
    def _sessions(self) -> dict:
        return self._session_mgr.sessions

    @_sessions.setter
    def _sessions(self, value: dict):
        self._session_mgr._sessions = value

    @property
    def _switching(self) -> bool:
        return self._session_mgr.switching

    @_switching.setter
    def _switching(self, value: bool):
        self._session_mgr.switching = value

    def _connect_orchestrator(self):
        """将 SessionManager 生命周期信号桥接到 SessionOrchestrator"""
        orch = self._orchestrator

        def _on_session_created(session_id: str, project_path: str):
            orch.create_runtime(
                session_id=session_id,
                project_path=project_path or "",
                title="新对话",
                mode=self._current_mode,
                model=self._current_model_name,
            )

        def _on_session_switched(old_id: str, new_id: str):
            orch.switch_session(new_id)

        def _on_session_deleted(session_id: str):
            orch.delete_runtime(session_id)

        self._session_mgr.session_created.connect(_on_session_created)
        self._session_mgr.session_switched.connect(_on_session_switched)
        self._session_mgr.session_deleted.connect(_on_session_deleted)

        # 订阅 v3 ui.* 事件（Phase 5 前为占位，仅记录日志避免事件丢失）
        bus = self._app_ctx.message_bus
        bus.subscribe_namespace("ui", self._on_ui_event)

    def _on_ui_event(self, event):
        """v3 UI 事件占位处理器（Phase 5 由 UIRenderer 接管）"""
        # 当前阶段仍由旧信号路径直接更新 UI；此处仅做调试追踪
        pass

    # ═══════════════════════════════════════════════════
    # 主题
    # ═══════════════════════════════════════════════════
    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#0D1117"))
        dark_palette.setColor(QPalette.WindowText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Base, QColor("#161B22"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#1C2128"))
        dark_palette.setColor(QPalette.ToolTipBase, QColor("#21262D"))
        dark_palette.setColor(QPalette.ToolTipText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Text, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Button, QColor("#21262D"))
        dark_palette.setColor(QPalette.ButtonText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.BrightText, QColor("#FF5555"))
        dark_palette.setColor(QPalette.Link, QColor("#58A6FF"))
        dark_palette.setColor(QPalette.Highlight, QColor("#58A6FF"))
        dark_palette.setColor(QPalette.HighlightedText, QColor("#0D1117"))
        app.setPalette(dark_palette)

        # 加载 QSS 文件
        qss = self.theme_service.get_qss()
        if qss:
            app.setStyleSheet(qss)

    # ═══════════════════════════════════════════════════
    # UI 布局
    # ═══════════════════════════════════════════════════
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 左侧图标栏 ──────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(52)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(4, 12, 4, 12)
        sidebar_layout.setSpacing(8)

        self.explorer_btn = self._create_sidebar_btn("📁", "资源管理器", "explorer")
        self.chat_btn = self._create_sidebar_btn("💬", "对话", "chat")
        self.terminal_btn = self._create_sidebar_btn("🖥", "终端", "terminal")
        self.tasks_btn = self._create_sidebar_btn("📝", "任务", "tasks")

        sidebar_layout.addWidget(self.explorer_btn)
        sidebar_layout.addWidget(self.chat_btn)
        sidebar_layout.addWidget(self.terminal_btn)
        sidebar_layout.addWidget(self.tasks_btn)
        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # ── 左侧面板（可切换）────────────────────
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        self.left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 8, 0, 8)
        left_layout.setSpacing(0)

        self.left_stack = QStackedWidget()

        self.file_tree = FileTreeWidget(self._project_root)
        self.file_tree.file_selected.connect(self._on_file_selected)
        self.file_tree.folder_changed.connect(self._on_folder_changed)
        self.file_tree.new_conversation_requested.connect(self._on_new_conversation_in_folder)
        self.file_tree.set_recent_projects(self.project_service.list_recent_projects())

        self.conversation_list = ConversationListWidget()
        self.conversation_list.new_conversation.connect(self._on_new_conversation_requested)
        self.conversation_list.conversation_selected.connect(self._switch_conversation)
        self.conversation_list.conversation_deleted.connect(self._delete_conversation)

        self.task_list = TaskListWidget()

        self.left_stack.addWidget(self.file_tree)
        self.left_stack.addWidget(self.conversation_list)
        self.left_stack.addWidget(self.task_list)
        left_layout.addWidget(self.left_stack)
        main_layout.addWidget(self.left_panel)

        # ── 中央对话区 ──────────────────────────
        self.chat_view = ChatView()
        self.chat_view.send_clicked.connect(self._send_message)
        self.chat_view.mode_clicked.connect(self._on_mode_clicked)
        main_layout.addWidget(self.chat_view, 1)

        # ── 右侧工作区 ──────────────────────────
        self.workspace = WorkspaceWidget(interpreter_service=self.interpreter_service)
        self.workspace.setMinimumWidth(300)
        self.workspace.set_logs_max_lines(self._log_max_lines)
        self.workspace.set_project_path(self._project_root)
        self.workspace.setVisible(self._log_panel_visible)
        main_layout.addWidget(self.workspace)

        # ── 状态栏 ──────────────────────────────
        self.status_bar = QStatusBar()
        self.status_indicator = StatusIndicator()
        self.status_bar.addWidget(self.status_indicator, 1)
        self.capacity_label = QLabel("🟢 任务:0/3 | ⏳ 排队:0/5 | 🔧 工具:0/12")
        self.status_bar.addPermanentWidget(self.capacity_label)
        # 双槽位队列状态条
        self._queue_bar = QLabel("")
        self._queue_bar.setFont(QFont("Microsoft YaHei", 9))
        self._queue_bar.setStyleSheet("color: #888; padding: 2px 8px;")
        self._queue_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self._queue_bar)
        self.setStatusBar(self.status_bar)

        # 默认选中对话
        self.chat_btn.setChecked(True)
        self.left_stack.setCurrentIndex(1)

    def _create_sidebar_btn(self, icon_text, tooltip, name):
        btn = SidebarButton(icon_text, tooltip)
        btn.setObjectName("sidebarBtn")
        btn.setProperty("view", name)
        btn.clicked.connect(self._on_sidebar_clicked)
        return btn

    def _on_sidebar_clicked(self):
        sender = self.sender()
        view = sender.property("view")
        for btn in [self.explorer_btn, self.chat_btn, self.terminal_btn, self.tasks_btn]:
            btn.setChecked(btn == sender)

        if view == "explorer":
            self.left_stack.setCurrentIndex(0)
        elif view == "chat":
            self.left_stack.setCurrentIndex(1)
        elif view == "terminal":
            self.workspace.set_terminal_focus()
            self.workspace.setVisible(True)
            self.chat_view.set_log_panel_checked(True)
        elif view == "tasks":
            self.left_stack.setCurrentIndex(2)

    # ═══════════════════════════════════════════════════
    # 模式管理
    # ═══════════════════════════════════════════════════
    def _init_mode(self, mode_name, llm_name=None):
        mode_config = self.config_service.get("manual_modes", {}).get(mode_name)
        if not mode_config:
            return
        self._current_mode = mode_name
        if llm_name is None:
            llm_name = mode_config.get("current_model", "tool-agent")

        providers = self.llm_registry.list_providers()
        if llm_name not in providers:
            llm_name = next(iter(providers.keys()), "tool-agent")

        self._current_llm = self.llm_registry.get_llm(llm_name)
        self._current_tools = mode_config.get("tools", list(TOOL_MAP.keys()))
        self._current_model_name = llm_name

        self.chat_view.set_mode(mode_name)
        current_title = self._sessions.get(self._current_session, {}).get("title", "未命名会话")
        self.chat_view.set_header(mode_name, llm_name, current_title)
        self.chat_view.populate_models(providers, llm_name)
        self.status_indicator.set_mode(mode_name)
        self.status_indicator.set_model(llm_name)
        self._on_log_message(f"🔄 切换模式: {mode_name} / {llm_name}", is_header=True, is_global=True)

    def _on_mode_clicked(self, mode_name):
        # 切换模式时保留当前选择的模型（全局模型记忆，不因模式切换而重置）
        self._init_mode(mode_name, self._current_model_name)
        # 持久化当前模式
        self.persistence_service.save_mode(mode_name)

    def _on_model_changed(self, llm_name):
        self._current_llm = self.llm_registry.get_llm(llm_name)
        self._current_model_name = llm_name
        # 持久化当前模式选用的模型，以及全局 last_model
        self.persistence_service.save_model(self._current_mode, llm_name)

        provider = self.llm_registry.get_provider_config(llm_name)
        current_title = self._sessions.get(self._current_session, {}).get("title", "未命名会话")
        self.chat_view.set_header(self._current_mode, llm_name, current_title)
        self.status_indicator.set_model(llm_name)
        self._on_log_message(f"🔄 切换模型: {llm_name} ({provider.get('model', '?')})", is_global=True)

    # ═══════════════════════════════════════════════════
    # 设置对话框
    # ═══════════════════════════════════════════════════
    def _open_settings(self):
        dlg = SettingsDialog(self.llm_registry, self, config_service=self.config_service)
        dlg.providers_changed.connect(self._on_settings_changed)
        dlg.ui_settings_changed.connect(self._apply_ui_settings)
        dlg.exec()

    def _on_settings_changed(self):
        providers = self.llm_registry.list_providers()
        model_changed = False
        if self._current_model_name not in providers:
            self._current_model_name = next(iter(providers.keys()), "tool-agent")
            self._current_llm = self.llm_registry.get_llm(self._current_model_name)
            model_changed = True
        # 如因设置变更导致模型回退，同步保存 last_model，避免下次启动丢失
        if model_changed:
            self.persistence_service.save_model(self._current_mode, self._current_model_name)
        self.chat_view.populate_models(providers, self._current_model_name)
        current_title = self._sessions.get(self._current_session, {}).get("title", "未命名会话")
        self.chat_view.set_header(self._current_mode, self._current_model_name, current_title)
        self._on_log_message("🔧 模型设置已更新", is_global=True)

    # ═══════════════════════════════════════════════════
    # 项目目录管理
    # ═══════════════════════════════════════════════════
    def _on_folder_changed(self, path: str):
        """用户通过资源管理器切换项目目录"""
        if not path or path == self._project_root:
            return
        self._project_root = self.project_service.set_current_project(path)
        self.context_service.set_project_root(path)
        self.project_service.add_recent_project(path)
        self.file_tree.set_recent_projects(self.project_service.list_recent_projects())
        self._on_log_message(f"📂 切换项目目录: {path}", is_header=True)
        self._switch_project(path)

    @Slot()
    def _on_context_changed(self):
        """上下文变化时更新状态栏"""
        project_root = self.context_service.get_project_root()
        active_doc = self.context_service.get_active_document()
        active_file = os.path.basename(active_doc.path) if active_doc else ""
        self.status_indicator.set_workspace_context(project_root, active_file)

    @Slot(str)
    def _on_interpreter_changed(self, interpreter_type: str):
        """终端解释器切换时更新上下文与状态栏"""
        self.context_service.update_interpreter_context()
        current = self.interpreter_service.get_current()
        name = current.name if current else interpreter_type
        self._on_log_message(f"🖥 切换解释器: {name}", is_header=True, is_global=True)
        self._on_context_changed()

    @Slot(str, str, int)
    def _on_document_opened(self, path: str, preview: str, size: int):
        """右侧文档打开/切换时更新上下文"""
        self.context_service.set_active_document(path, preview, size)

    @Slot(str)
    def _on_document_closed(self, path: str):
        """右侧文档关闭时更新上下文"""
        self.context_service.remove_open_document(path)

    def _on_new_conversation_in_folder(self, path: str):
        """在指定目录下开启新对话（右键菜单 / 工具栏触发）"""
        if path and path != self._project_root:
            self._project_root = self.project_service.set_current_project(path)
            self.file_tree.set_root_path(path)
        self._new_conversation(project_path=self._project_root)

    def _on_new_conversation_requested(self, project_flag: str):
        """对话列表新建按钮：'<project>' 表示当前项目，'' 表示全局纯对话"""
        if project_flag == "<project>":
            # 兜底：_project_root 可能为空（未切换过项目），尝试从文件树获取
            if not self._project_root:
                self._project_root = self.file_tree.get_root_path() or ""
                if not self._project_root:
                    self._on_log_message("⚠️ 当前未检测到项目路径，已降级为全局对话", is_header=True)
                    self._new_conversation(project_path="")
                    return
            self._new_conversation(project_path=self._project_root)
        else:
            self._new_conversation(project_path="")

    def _switch_project(self, project_path: str, is_init=False):
        """切换项目目录上下文：加载该目录下会话与全局纯对话"""
        print(f"[DIAG] _switch_project: path={project_path}, is_init={is_init}", flush=True)
        project_path = self.project_service.normalize_path(project_path)
        self._project_root = project_path
        self.context_service.set_project_root(project_path)
        self.file_tree.set_root_path(project_path)
        self._session_mgr.clear()
        self.conversation_list.set_project_label(project_path)
        self.memory_manager.store.clear()
        self.chat_view.clear()

        # 加载会话
        project_sessions, global_sessions = self._session_mgr.load_project_sessions(project_path)

        if project_sessions or global_sessions:
            first = project_sessions[0] if project_sessions else global_sessions[0]
            QTimer.singleShot(0, lambda sid=first["id"]: self._switch_conversation(sid))
            if not is_init:
                self._on_log_message(
                    f"📂 已加载项目: {project_path} ({len(project_sessions)} 个项目会话, {len(global_sessions)} 个全局会话)",
                    is_header=True,
                )
        else:
            session_id = self._session_mgr.create_session(
                project_path=project_path, mode=self._current_mode,
                model=self._current_model_name, title="新对话",
            )
            self.chat_view.set_header(self._current_mode, self._current_model_name, "新对话")
            if not is_init:
                self.chat_view.append_system(
                    f"已切换到项目目录: {project_path}\n当前无历史会话，已自动创建新对话。"
                )
                self._on_log_message(f"📂 新建项目会话: {project_path}", is_header=True)

        # 同步活动面板的项目路径过滤
        self.workspace.set_project_path(project_path)
        self._refresh_activities()

    # ═══════════════════════════════════════════════════
    # 对话管理
    # ═══════════════════════════════════════════════════
    def _init_default_session(self):
        """启动时根据当前项目目录初始化默认会话"""
        self._switch_project(self._project_root, is_init=True)
        if not self._sessions:
            self.chat_view.append_system(
                f"欢迎使用 AI Agent Workbench。当前项目：{self._project_root}\n当前模式：{self._current_mode.capitalize()}"
            )
            self.chat_view.append_system("新特性：项目目录 · 流式输出 · 模型管理 · 对话持久化 · 键盘快捷键")

    def _restore_conversations(self):
        """启动恢复：由 _init_default_session -> _switch_project 统一处理"""
        pass

    def _new_conversation(self, project_path=""):
        """创建新对话；project_path='' 表示全局纯对话，否则关联项目目录"""
        print(f"[DIAG] _new_conversation: project_path={project_path}", flush=True)
        # 中止当前会话的活跃任务，释放队列槽位
        self._abort_current_session_task()
        # 守卫：防止信号槽重入导致重复创建（v3.10.1）
        if getattr(self, '_switching', False):
            return

        # 守卫：当前上下文中已有空对话（标题=新对话 且 消息数=0）→ 直接切换
        empty_sid = self._session_mgr.find_empty_session(project_path)
        if empty_sid:
            self._switch_conversation(empty_sid)
            return

        self._switching = True
        try:
            session_id = self._session_mgr.create_session(
                project_path=project_path, mode=self._current_mode,
                model=self._current_model_name, title="新对话",
            )
            self.chat_view.clear()
            self.chat_view.set_header(self._current_mode, self._current_model_name, "新对话")
            # 全局对话清除项目上下文，项目对话设置项目上下文
            self.context_service.set_project_root(project_path)
            label = "全局" if project_path == "" else project_path
            self._on_log_message(f"📝 新会话 @ {label}", is_header=True)
        finally:
            self._switching = False

    def _switch_conversation(self, session_id):
        """会话列表点击入口：走完整 Session-as-Room 切换协议。"""
        self._on_session_switch(self._current_session, session_id)

    def _on_session_switch(self, old_session_id, new_session_id):
        """Session-as-Room (v3.11: SessionManager 管理数据 + MainWindow 管理 UI)"""
        if old_session_id == new_session_id:
            return

        if getattr(self, '_switching', False):
            return
        # 中止旧会话的活跃任务，释放队列槽位
        self._abort_current_session_task()
        self._switching = True
        try:
            # 1. 解绑旧会话的 UI 信号
            if old_session_id:
                self._detach_ui_signals(old_session_id)

            # 2. 保存当前 Phase 状态
            self._save_phase_state(old_session_id)

            # 3. 不再清空双槽位队列 — 每个会话独立队列，切换时保留后台任务

            # 4. SessionManager 处理数据侧切换（加载消息、设置 project_root）
            self._session_mgr.switch_session(new_session_id)

            # 5. 渲染 UI
            self.chat_view.clear()
            session = self._session_mgr.get_session_data(new_session_id)
            msgs = session["messages"]

            # 5.1 接替上下文
            handoff_context = self._self_context.build_handoff(new_session_id)
            if handoff_context:
                self.chat_view.append_system(handoff_context)

            # 5.2 render
            self.chat_view.set_header(self._current_mode, self._current_model_name, session["title"])
            from langchain_core.messages import HumanMessage, AIMessage
            history = self.memory_manager.get_session_history(new_session_id)
            history.clear()
            for msg in msgs:
                self._render_stored_message(msg)
                if msg["role"] == "user":
                    history.add_message(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    history.add_message(AIMessage(content=msg["content"]))
            self._on_log_message(f"📂 切换会话: {session['title']}")

            # 6. 恢复任务状态
            task = self.task_service.get_task_status(new_session_id)
            if task:
                if task.status == TaskStatus.AWAITING_CONFIRM:
                    self._restore_confirm_ui(task)
                elif task.is_active:
                    self._attach_ui_signals(new_session_id)
                    self.chat_view.set_phase_indicator(task.phase, len(task.task_list))
        finally:
            self._switching = False

    def _detach_ui_signals(self, session_id: str):
        """解绑指定会话 Worker 的 UI 信号。不 stop Worker，只断开信号连接。"""
        worker = self._workers.get(session_id) if hasattr(self, '_workers') else None
        if worker is None:
            return
        self.chat_view.finalize_stream()

    def _attach_ui_signals(self, session_id: str):
        """重新绑定指定会话 Worker 的 UI 信号。"""
        worker = self._workers.get(session_id) if hasattr(self, '_workers') else None
        if worker is None:
            return
        worker_session_id = session_id
        current_only = self._make_current_only_guard(worker, self, worker_session_id)
        try:
            worker.chunk_ready.disconnect()
        except Exception:
            pass
        worker.chunk_ready.connect(current_only(self._on_chunk))
        try:
            worker.log_message.disconnect()
        except Exception:
            pass
        worker.log_message.connect(current_only(self._on_log_message))

    def _save_phase_state(self, session_id: str):
        """保存当前 Phase 状态到 SessionTask（用于切回时恢复 confirm UI）"""
        if not session_id or not self.task_service:
            return
        task = self.task_service.get_task_status(session_id)
        if task is None:
            return
        if self._current_phase == "confirm":
            task.phase = "confirm"
            task.task_list = list(self._phase_task_list)
            # 状态变更统一由 TaskService 发起
            self.task_service._on_phase_change(
                session_id, "confirm", "等待用户确认"
            )

    def _restore_confirm_ui(self, task):
        """恢复 confirm 阶段的 UI 状态"""
        self._phase_task_list = list(task.task_list)
        self.chat_view.set_phase_indicator("confirm", len(self._phase_task_list))
        self.chat_view.show_confirmation(self._phase_task_list)

    def _render_stored_message(self, msg):
        content = msg["content"]
        # Strip any leaked tool_call XML from historical messages
        if "</tool_calls>" in content or "<invoke name=" in content:
            import re
            content = re.sub(r'\s*<tool_calls>.*?</tool_calls>', '', content, flags=re.DOTALL)
            content = content.strip()
            if not content:
                content = "[tool executed]"
        if msg["role"] == "user":
            self.chat_view.append_user(content)
        elif msg["role"] == "ai":
            self.chat_view.append_ai(content)
        else:
            self.chat_view.append_system(content)

    def _delete_conversation(self, session_id):
        if len(self._sessions) <= 1:
            QMessageBox.information(self, "提示", "不能删除唯一的会话")
            return
        self._session_mgr.delete_session(session_id)
        if self._current_session == session_id:
            first = next(iter(self._sessions.keys()), "")
            if first:
                self._switch_conversation(first)

    def _update_conversation_title(self, session_id, title):
        self._session_mgr.update_title(session_id, title)

    def _abort_current_session_task(self):
        """中止当前会话的活跃任务：停止 Worker、清空队列、重置 PhaseManager"""
        current_sid = self._current_session
        if not current_sid:
            return
        # 1. 停止当前 Worker
        worker = self._workers.get(current_sid) if hasattr(self, '_workers') else None
        if worker is not None and worker.isRunning():
            worker.stop()
            worker.wait(3000)
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        self._worker = None
        # 2. 清空双槽位队列
        self._pending_queue.clear()
        # 3. 重置 PhaseManager
        self._phase_manager.reset()
        self._current_phase = "idle"
        self._phase_task_list = []
        self._phase_results = []
        # 4. 更新 TaskService 状态（通过 cancel_task 统一处理）
        self.task_service.cancel_task(current_sid)
        # 5. 更新 UI
        self.chat_view.finalize_stream()
        self.chat_view.clear_phase_ui()
        self.chat_view.set_streaming(False)

    # ═══════════════════════════════════════════════════
    # 消息发送
    # ═══════════════════════════════════════════════════
    def _send_message(self, user_text):
        print(f"[DIAG] _send_message ENTER: text='{user_text[:30]}' v3={self._v3_enabled}", flush=True)

        # 0.1 Phase 状态拦截：CONFIRM 阶段用户输入视为对任务清单的反馈
        if self._current_phase == "confirm" and not self._v3_enabled:
            lowered = user_text.lower()
            if "重新分析" in user_text or "取消" in user_text or "cancel" in lowered or "no" in lowered:
                self._on_phase_reanalyze()
            else:
                self._on_phase_confirmed()
            return

        # v3 路径：委托给 SessionOrchestrator
        if self._v3_enabled:
            self._send_message_v3(user_text)
            return

        print(f"[DIAG] _send_message ENTER: text='{user_text[:30]}' full={self._pending_queue.is_full} len={self._pending_queue.length}", flush=True)
        # 0. 槽满检查：队列已满时拒绝新消息
        if self._pending_queue.is_full:
            print(f"[DIAG] _send_message QUEUE FULL, len={self._pending_queue.length}", flush=True)
            self._on_log_message("⚠ 队列已满，请等待当前任务完成", is_global=True)
            return

        # 0.2 写入本轮日志标题
        display_text = user_text[:80] + ("..." if len(user_text) > 80 else "")
        self._on_log_message(f"▶ 用户: {display_text}", is_header=True)

        # 1. UI 和 session 持久化
        self._session_mgr.add_message(self._current_session, "user", user_text)
        self.chat_view.append_user(user_text)
        self.session_service.add_message(self._current_session, "user", user_text)

        session = self._session_mgr.get_session_data(self._current_session)
        if len(session["messages"]) == 1:
            title = user_text[:20] + "..." if len(user_text) > 20 else user_text
            session["title"] = title
            self._update_conversation_title(self._current_session, title)
            self.chat_view.set_header(self._current_mode, self._current_model_name, title)
            project_path = self.project_service.get_session_project(self._current_session)
            self.session_service.create_conversation(
                self._current_session, title, self._current_mode, self._current_model_name,
                project_path=project_path
            )

        # 2. 构建上下文并提交到 v3.9 TaskService
        context_text = self.context_service.build_prompt_context()
        old_task = self.task_service.get_task_status(self._current_session)
        print(f"[DIAG-SEND] submit_task: session={self._current_session}, old_task={old_task.status.value if old_task else 'None'}, is_terminal={old_task.is_terminal if old_task else 'N/A'}", flush=True)
        try:
            self.task_service.submit_task(self._current_session, self._current_mode, user_text)
        except ResourceError as e:
            self._on_log_message(f"[TaskService] {e}", is_global=True)

        # 3. 入队双槽位队列
        import uuid
        task = PendingTask(
            task_id=uuid.uuid4().hex[:8],
            user_text=user_text,
            mode=self._current_mode,
            context=context_text,
        )
        if not self._pending_queue.enqueue(task):
            self._on_log_message("⚠ 入队失败", is_global=True)
            return

        self.chat_view.clear_input()

        # 由 _on_queue_task_started（QueuedConnection）统一启动 Phase 工作流
        # 不再在此处直接调用 _start_streaming，避免双重启动和信号槽重入

    def _send_message_v3(self, user_text: str):
        """v3 路径：通过 MessageBus 委托给 SessionOrchestrator"""
        rt = self._orchestrator.get_runtime(self._current_session)
        if rt is None:
            self._on_log_message("⚠ 当前会话未初始化", is_global=True)
            return

        if rt.queue_manager.is_full:
            self._on_log_message("⚠ 队列已满，请等待当前任务完成", is_global=True)
            return

        # 写入本轮日志标题
        display_text = user_text[:80] + ("..." if len(user_text) > 80 else "")
        self._on_log_message(f"▶ 用户: {display_text}", is_header=True)

        # UI 和 session 持久化
        self._session_mgr.add_message(self._current_session, "user", user_text)
        self.session_service.add_message(self._current_session, "user", user_text)

        session = self._session_mgr.get_session_data(self._current_session)
        if len(session["messages"])  == 1:
            title = user_text[:20] + "..." if len(user_text) > 20 else user_text
            session["title"] = title
            self._update_conversation_title(self._current_session, title)
            self.chat_view.set_header(self._current_mode, self._current_model_name, title)
            project_path = self.project_service.get_session_project(self._current_session)
            self.session_service.create_conversation(
                self._current_session, title, self._current_mode, self._current_model_name,
                project_path=project_path
            )

        self._app_ctx.message_bus.emit(UserSendEvent(
            session_id=self._current_session,
            user_text=user_text,
            mode=self._current_mode,
        ))
        self.chat_view.clear_input()

    def _start_streaming(self, task: PendingTask):
        """启动队列任务的 Phase 工作流"""
        self._on_log_message(f"🚀 开始处理: {task.user_text[:30]}...", is_header=False)
        self._phase_manager.start(task.user_text, task.mode, task.context)

    # ═══════════════════════════════════════════════════
    # Phase Manager 回调
    # ═══════════════════════════════════════════════════
    @Slot(str, str)
    def _on_phase_changed(self, phase, mode):
        self._current_phase = phase
        self.chat_view.set_phase_indicator(phase, len(self._phase_task_list))
        self._on_log_message(f"[Phase] {phase.upper()} @ {mode}", is_header=False)

    @Slot(str, str, str)
    def _on_analyze_required(self, user_text, mode, context):
        """Analyze 阶段：请求 AgentWorker 生成 task list"""
        self.chat_view.append_phase_message("analyze", "正在分析需求...")
        self._ensure_phase_worker()
        self._worker.reset_cancel()
        self._worker.request_analyze(user_text, context)

    @Slot(list)
    def _on_confirm_required(self, task_list):
        """Confirm 阶段：显示任务清单等待用户确认"""
        self._phase_task_list = list(task_list)
        self.chat_view.set_phase_indicator("confirm", len(self._phase_task_list))
        self.chat_view.append_phase_message("confirm", "请确认以下任务清单")
        self.chat_view.show_confirmation(self._phase_task_list)

    @Slot(list)
    def _on_execute_required(self, task_list):
        """Execute 阶段：请求 AgentWorker 绑定工具执行用户请求"""
        self._phase_task_list = list(task_list)
        self.chat_view.hide_confirmation()
        self.chat_view.append_phase_message("execute", "开始执行任务")
        context_text = self.context_service.get_phase_context("execute")
        original_text = self._phase_manager.current_context().user_text
        self._ensure_phase_worker()
        self._worker.reset_cancel()
        self._worker.request_execute(self._phase_task_list, original_text, context_text)

    @Slot(list, str)
    def _on_verify_required(self, execution_results, mode):
        """Verify 阶段：请求 AgentWorker 运行 LLM 验证"""
        self.chat_view.append_phase_message("verify", "正在验证执行结果...")
        self.chat_view.show_skip_verify()
        self._verification_details = self._run_local_verification()
        context_text = self.context_service.get_phase_context("verify")
        self._ensure_phase_worker()
        self._worker.reset_cancel()
        self._worker.request_verify(execution_results, self._verification_details, context_text)

    @Slot(str)
    def _on_archive_required(self, mode):
        """Archive 阶段：普通对话直接收尾；若用户触发存档则执行"""
        print("[DIAG] _on_archive_required called", flush=True)
        self.chat_view.append_phase_message("archive", "任务收尾")
        self.chat_view.hide_skip_verify()
        user_text = self._phase_manager.current_context().user_text
        if self._is_archive_request(user_text):
            self._archive_project()
        self._phase_manager.on_archive_complete(True, "工作流完成")
        # mark_task_completed 由 _on_phase_flow_finished 统一处理，此处不重复调用

    @Slot(bool, str)
    def _on_phase_flow_finished(self, success, message):
        print(f"[DIAG] _on_phase_flow_finished success={success}, queue_len={self._pending_queue.length}", flush=True)
        self._current_phase = "idle"
        self._phase_task_list = []
        self._phase_results = []
        self.chat_view.clear_phase_ui()
        if not success:
            self.chat_view.append_system(f"⚠️ {message}")

        # 更新 TaskService 中的任务状态，并通过信号刷新 UI
        current_sid = self._current_session
        error_msg = "" if success else message
        print(f"[DIAG-FLOW] _on_phase_flow_finished: session={current_sid}, success={success}", flush=True)
        self.task_service.complete_task(current_sid, success, error_msg)

        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        self._worker = None
        # 清理 _workers 字典和 WorkerPool
        if current_sid:
            self._workers.pop(current_sid, None)
            self.worker_pool.on_task_complete(current_sid)
        # 当前任务完成 → 自动出队下一个
        streaming = self._pending_queue.get_streaming_task()
        if streaming:
            self._pending_queue.mark_task_completed(streaming.task_id)

    @Slot(str, str)
    def _on_phase_error(self, code, detail):
        print(f"[DIAG] _on_phase_error code={code}, detail={detail}", flush=True)
        self._current_phase = "idle"
        self.chat_view.clear_phase_ui()
        self.chat_view.append_system(f"❌ Phase 错误 [{code}]: {detail}")
        self._on_log_message(f"[ERR] Phase {code}: {detail}", is_global=True)
        # 更新 TaskService 任务状态为 FAILED，并通过信号刷新 UI
        current_sid = self._current_session
        self.task_service.complete_task(current_sid, False, f"Phase 错误 [{code}]: {detail}")
        # 停止 Worker 并清理
        if self._worker is not None:
            if self._worker.isRunning():
                self._worker.stop()
                self._worker.wait(3000)
            self._worker = None
        # 清理 _workers 字典和 WorkerPool
        if current_sid:
            self._workers.pop(current_sid, None)
            self.worker_pool.on_task_complete(current_sid)
        # Phase 错误视为当前任务失败 → 出队下一个
        streaming = self._pending_queue.get_streaming_task()
        if streaming:
            self._pending_queue.mark_task_completed(streaming.task_id)

    # ═══════════════════════════════════════════════════
    # v3.9 TaskService 回调
    # ═══════════════════════════════════════════════════
    @Slot(str, str)
    def _on_task_status_changed(self, session_id: str, status: str):
        """TaskService 任务状态变化 → 更新会话列表"""
        self.conversation_list.update_task_status(session_id, status)

    @Slot(int, int, int)
    def _on_capacity_changed(self, active: int, queued: int, max_total: int):
        """更新底栏永久容量标签"""
        self.capacity_label.setText(
            f"🟢 任务:{active}/{self.task_service.capacity.max_concurrent_tasks}"
            f" | ⏳ 排队:{queued}/{self.task_service.capacity.max_queued_tasks}"
            f" | 🔧 工具:{self._tools_in_use}/{self.task_service.capacity.max_total_tools}"
        )

    @Slot(str, str, str)
    def _on_task_progress_signal(self, session_id: str, phase: str, detail: str):
        """TaskService Phase 变化 → 更新 UI"""
        if session_id == self._current_session:
            self.chat_view.set_phase_indicator(phase, len(self._phase_task_list))
        self.conversation_list.update_task_status(session_id, phase)

    @Slot(int, int)
    def _on_tool_usage_changed(self, tools_in_use: int, max_tools: int):
        """工具使用统计"""
        self._tools_in_use = tools_in_use
        self.capacity_label.setText(
            f"🟢 任务:{self.task_service.active_count}/{self.task_service.capacity.max_concurrent_tasks}"
            f" | ⏳ 排队:{self.task_service.queue_size}/{self.task_service.capacity.max_queued_tasks}"
            f" | 🔧 工具:{tools_in_use}/{max_tools}"
        )

    @Slot(str, bool)
    def _on_task_service_completed(self, session_id: str, success: bool):
        """TaskService 任务完成"""
        if session_id == self._current_session:
            if success:
                self.chat_view.append_system("✅ 任务完成")
            else:
                self.chat_view.append_system("❌ 任务执行失败")

    def _on_phase_confirmed(self):
        """用户点击确认执行"""
        if self._v3_enabled:
            self._app_ctx.message_bus.emit(UserConfirmEvent(
                session_id=self._current_session,
                confirmed=True,
            ))
            return
        self.chat_view.hide_confirmation()
        self._phase_manager.on_user_confirm(True)

    def _on_phase_reanalyze(self):
        """用户点击重新分析：重启 analyze"""
        if self._v3_enabled:
            self._app_ctx.message_bus.emit(UserReanalyzeEvent(
                session_id=self._current_session,
            ))
            return
        self.chat_view.hide_confirmation()
        ctx = self._phase_manager.current_context()
        self._phase_manager.reset()
        context_text = self.context_service.get_phase_context("analyze")
        self._phase_manager.start(ctx.user_text, ctx.mode, context_text)

    def _on_phase_skip_verify(self):
        """用户点击跳过验证"""
        if self._v3_enabled:
            self._app_ctx.message_bus.emit(UserSkipVerifyEvent(
                session_id=self._current_session,
            ))
            return
        self.chat_view.hide_skip_verify()
        self._phase_manager.on_verify_complete(True, "用户跳过验证")

    def _on_analyze_result(self, task_list):
        """Analyze 阶段结果：已解析为 task list"""
        print(f"[DIAG] _on_analyze_result called, task_list_len={len(task_list) if task_list else 0}, phase={self._current_phase}", flush=True)
        if not task_list and self._current_mode in ("plan", "craft"):
            # LLM 没有输出标准清单时，把原始需求作为单一任务兜底
            original = self._phase_manager.current_context().user_text
            fallback_desc = original.strip()[:300] if original.strip() else "执行用户请求"
            from agent_engine.agent_session import TaskItem
            task_list = [TaskItem(id="task-1", description=fallback_desc)]
        self._phase_task_list = task_list
        self.chat_view.set_task_progress(0, len(task_list))
        self._phase_manager.on_analyze_complete(task_list)

    def _on_execute_result(self, text):
        """Execute 阶段结果：显示并保存到 session"""
        self.chat_view.finalize_stream()
        if text and text.strip():
            self.chat_view.append_ai(text)
            self._append_ai_message(self._current_session, text)
            self._phase_results.append({"task": "execute", "result": text})
        self._append_metrics_footer_if_any()
        self._chunks_received = False
        self.status_indicator.set_tokens("")
        self._phase_manager.on_execute_complete(self._phase_results)

    def _on_verify_result(self, text):
        """Verify 阶段结果：显示验证结论"""
        self.chat_view.finalize_stream()
        self.chat_view.hide_skip_verify()
        if text and text.strip():
            self.chat_view.append_ai(f"**验证结果**\n\n{text}")
        self._append_metrics_footer_if_any()
        self._chunks_received = False
        self.status_indicator.set_tokens("")
        local_details = getattr(self, "_verification_details", "")
        passed = "通过" in text or "passed" in text.lower() or "未通过" not in text
        self._phase_manager.on_verify_complete(passed, f"{local_details}\n\n{text}")

    def _on_worker_error(self, code, detail):
        """AgentWorker 报告错误"""
        self.chat_view.finalize_stream()
        self._append_metrics_footer_if_any()
        self._chunks_received = False
        self.status_indicator.set_tokens("")
        self.chat_view.append_system(f"❌ Worker 错误 [{code}]: {detail}")
        self._on_log_message(f"[ERR] Worker {code}: {detail}", is_global=True)
        # 更新 TaskService 任务状态为 FAILED，并通过信号刷新 UI
        current_sid = self._current_session
        self.task_service.complete_task(current_sid, False, f"Worker 错误 [{code}]: {detail}")
        # 停止 Worker 并清理
        if self._worker is not None:
            if self._worker.isRunning():
                self._worker.stop()
                self._worker.wait(3000)
            self._worker = None
        # 清理 _workers 字典和 WorkerPool
        if current_sid:
            self._workers.pop(current_sid, None)
            self.worker_pool.on_task_complete(current_sid)

    @staticmethod
    def _make_current_only_guard(worker, main_window, worker_session_id):
        def guard(slot):
            def wrapper(*args):
                if worker is not main_window._worker:
                    print(f"[DIAG-GUARD] BLOCKED: worker mismatch (worker={worker.worker_id}, _worker={main_window._worker.worker_id if main_window._worker else 'None'})", flush=True)
                    return
                if main_window._current_session != worker_session_id:
                    print(f"[DIAG-GUARD] BLOCKED: session mismatch (worker_session={worker_session_id}, current={main_window._current_session})", flush=True)
                    return
                slot(*args)
            return wrapper
        return guard

    def _ensure_phase_worker(self):
        """确保存在一个已启动并就绪的 AgentWorker（跨 Phase 复用 AgentSession）"""
        if self._worker is not None and self._worker.isRunning():
            return

        mode_config = self.config_service.get_mode_config(self._current_mode)
        default_prompt = mode_config.get("system_prompt", "你是全能 AI 助手。")
        user_rules = self.config_service.get("user_rules", [])
        max_tool_rounds = self.config_service.get_max_tool_rounds(self._current_mode)
        task_timeout = self.config_service.get_task_timeout(self._current_mode)
        llm_timeout = self.config_service.get_llm_timeout(self._current_mode)
        tool_timeout = self.config_service.get_tool_timeout(self._current_mode)

        worker_session_id = self._current_session
        worker = AgentWorker(
            mode_name=self._current_mode,
            current_llm=self._current_llm,
            current_tools=self._current_tools,
            session_id=worker_session_id,
            system_prompt=default_prompt,
            tool_map=TOOL_MAP,
            tool_definitions=TOOL_DEFINITIONS,
            enable_streaming=True,
            user_rules=user_rules,
            max_tool_rounds=max_tool_rounds,
            task_timeout=task_timeout,
            llm_timeout=llm_timeout,
            tool_timeout=tool_timeout,
            project_root=self.context_service.get_project_root(),
            workspace_context=self.context_service.build_prompt_context(),
            app_version=self.config_service.get("app.version", "v3.x"),
        )
        self._worker = worker
        self._workers[worker_session_id] = worker  # v3.9: 多 Worker 池
        self._chunks_received = False

        current_only = self._make_current_only_guard(worker, self, worker_session_id)

        worker.chunk_ready.connect(current_only(self._on_chunk))
        worker.log_message.connect(current_only(self._on_log_message))
        worker.task_created.connect(current_only(self._add_task))
        worker.task_finished.connect(current_only(self._finish_task))
        worker.confirm_required.connect(current_only(self._on_tool_confirm_required))
        worker.token_used.connect(current_only(self._on_token_used))
        worker.turn_metrics_ready.connect(current_only(self._on_turn_metrics_ready))
        worker.tool_executed.connect(current_only(self._on_tool_executed))
        worker.analyze_result_ready.connect(current_only(self._on_analyze_result))
        worker.execute_result_ready.connect(current_only(self._on_execute_result))
        worker.verify_result_ready.connect(current_only(self._on_verify_result))
        worker.error_occurred.connect(current_only(self._on_worker_error))
        # v3.9: result_ready 不包 current_only，后台 Worker 完成时也要落盘
        # _on_result 内部按 session_id 判断是否渲染到 UI
        worker.result_ready.connect(self._on_result)
        worker.start()

        # 等待 Worker 线程的事件循环完全就绪，避免启动时序竞态
        ready = worker._loop_ready.wait(timeout=5.0)

        self.chat_view.set_streaming(True)
        self.status_indicator.set_tokens("生成中...")

    def _append_metrics_footer_if_any(self):
        """如果有待显示的 metrics，追加到 AI 内容下方"""
        if self._pending_metrics:
            self.chat_view.append_ai_metrics_footer(self._pending_metrics.format_brief())
            self._pending_metrics = None

    def _append_ai_message(self, session_id, text, persist_to_memory=True):
        """把 AI 回复持久化到 session 和数据库；可选是否写入 LangChain memory"""
        if not text or not text.strip():
            return
        if session_id not in self._sessions:
            return
        self._session_mgr.add_message(session_id, "ai", text)
        self.session_service.add_message(session_id, "ai", text)
        if persist_to_memory:
            from langchain_core.messages import AIMessage
            self.memory_manager.get_session_history(session_id).add_message(AIMessage(content=text))

    def _run_local_verification(self) -> str:
        """运行本地语法检查和单元测试，优先使用项目 venv Python"""
        import subprocess
        import shutil
        lines = []

        # 优先选择项目 venv Python
        python_path = self._resolve_venv_python()
        if not python_path:
            python_path = shutil.which("python") or "python"

        # 语法检查
        try:
            result = subprocess.run(
                [python_path, "-m", "py_compile", "main.py"],
                cwd=self._project_root or None,
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                lines.append(f"✅ 语法检查通过 (main.py) — 使用 {python_path}")
            else:
                lines.append(f"❌ 语法检查失败: {result.stderr}")
        except Exception as e:
            lines.append(f"⚠️ 语法检查异常: {e}")

        # 单元测试
        try:
            result = subprocess.run(
                [python_path, "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=self._project_root or None,
                capture_output=True, text=True, timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                lines.append("✅ 单元测试通过")
            else:
                lines.append(f"❌ 单元测试失败: {result.stderr[:500]}")
        except Exception as e:
            lines.append(f"⚠️ 单元测试异常: {e}")
        return "\n".join(lines)

    def _resolve_venv_python(self) -> str:
        """从 interpreter_service 中优先挑选 venv Python"""
        if not self.interpreter_service:
            return ""
        # 当前解释器如果是 python 则直接使用
        current = self.interpreter_service.get_current()
        if current and current.type == "python" and os.path.exists(current.path):
            return current.path
        # 否则从发现列表中优先选 venv
        for interp in self.interpreter_service.list_all():
            if interp.type == "python" and "venv" in interp.name.lower() and os.path.exists(interp.path):
                return interp.path
        # 最后任选一个 python
        for interp in self.interpreter_service.list_all():
            if interp.type == "python" and os.path.exists(interp.path):
                return interp.path
        return ""

    def _is_archive_request(self, user_text: str) -> bool:
        """判断用户输入是否触发存档流程"""
        return "请存档" in user_text or "请存档并推送" in user_text

    def _archive_project(self):
        """执行项目存档（简化版：调用外部脚本或直接 commit/tag）"""
        self._on_log_message("📦 执行项目存档...", is_header=True)
        # 实际存档逻辑由用户规则驱动，这里仅作标记
        self.chat_view.append_system("📦 已触发项目存档流程")

    def _on_stop_generation(self):
        """用户点击停止：取消当前 streaming 任务，自动出队下一个"""
        if self._v3_enabled:
            self._app_ctx.message_bus.emit(UserStopEvent(
                session_id=self._current_session,
            ))
            return

        streaming = self._pending_queue.get_streaming_task()
        if streaming:
            # 取消当前
            self._pending_queue.cancel(0)
            if self._worker and self._worker.isRunning():
                self._worker.stop()
            self.chat_view.finalize_stream()
            self._on_log_message("⏹ 用户停止了生成", is_global=True)
            # 重置 Phase 状态
            if self._current_phase != "idle":
                self._phase_manager.reset()
                self._current_phase = "idle"
                self.chat_view.clear_phase_ui()

    # ═══════════════════════════════════════════════════
    # 双槽位队列管理 (v3.10)
    # ═══════════════════════════════════════════════════
    def _on_queue_changed(self):
        """队列状态变化 → 更新 UI"""
        self._update_queue_bar()
        self._update_send_button_state()

    @Slot(str)
    def _on_queue_task_started(self, task_id):
        """队列中 slot[0] 开始新任务 → 启动 Phase 工作流"""
        print(f"[DIAG] _on_queue_task_started task_id={task_id}, switching={getattr(self, '_switching', False)}", flush=True)
        if getattr(self, '_switching', False):
            print("[DIAG] _on_queue_task_started BLOCKED by switching guard", flush=True)
            return  # 会话切换中，跳过任务启动
        streaming = self._pending_queue.get_streaming_task()
        if streaming and streaming.task_id == task_id:
            self._start_streaming(streaming)

    def _update_queue_bar(self):
        """更新队列状态条：显示 streaming（slot 0）和 pending（slot 1）"""
        streaming = self._pending_queue.get_streaming_task()
        pending = self._pending_queue.get_pending_tasks()

        if not streaming and not pending:
            self._queue_bar.setVisible(False)
            return

        lines = []
        if streaming:
            preview = streaming.user_text[:40] + "..." if len(streaming.user_text) > 40 else streaming.user_text
            lines.append(f"🔄 处理中: {preview}")
        for task in pending:
            preview = task.user_text[:40] + "..." if len(task.user_text) > 40 else task.user_text
            lines.append(f"📋 排队中: {preview}")
        if self._pending_queue.is_full:
            lines.append("[队列已满，请等待]")

        self._queue_bar.setText("  |  ".join(lines))
        self._queue_bar.setVisible(True)

    def _update_send_button_state(self):
        """队列满时灰化发送键"""
        if hasattr(self.chat_view, 'set_send_enabled'):
            self.chat_view.set_send_enabled(not self._pending_queue.is_full)

    def _cancel_pending(self):
        """取消所有排队任务（保留当前 streaming）"""
        streaming = self._pending_queue.get_streaming_task()
        pending = self._pending_queue.get_pending_tasks()
        for task in pending:
            self._pending_queue.cancel(1)  # slot 1 = pending
            self._on_log_message(f"⏹ 取消排队: {task.user_text[:30]}...", is_global=True)

    def _cancel_current(self):
        """取消当前 streaming 任务（保留排队）"""
        self._on_stop_generation()

    @Slot(str)
    def _on_chunk(self, chunk):
        """流式输出每个 token"""
        self._chunks_received = True
        self.chat_view.append_chunk(chunk)

    def _on_result(self, session_id, text):
        if not text or not text.strip():
            self.chat_view.finalize_stream()
            self._chunks_received = False
            self.status_indicator.set_tokens("")
            if self._current_phase != "idle":
                self._phase_manager.reset()
                self._current_phase = "idle"
                self.chat_view.clear_phase_ui()
            # 停止当前 Worker 并清理
            if self._worker is not None:
                if self._worker.isRunning():
                    self._worker.stop()
                    self._worker.wait(3000)
                self._worker = None
            # 清理 _workers 字典和 WorkerPool
            self._workers.pop(session_id, None)
            self.worker_pool.on_task_complete(session_id)
            # 更新 TaskService 任务状态为 FAILED，并通过信号刷新 UI
            self.task_service.complete_task(session_id, False, "LLM 返回空结果")
            # 空结果视为当前任务异常完成 → 出队下一个
            streaming = self._pending_queue.get_streaming_task()
            if streaming:
                self._pending_queue.mark_task_completed(streaming.task_id)
            return
        self._append_ai_message(session_id, text)
        if session_id == self._current_session:
            self.chat_view.finalize_stream()
            if not self._chunks_received:
                self.chat_view.append_ai(text)
            self._append_metrics_footer_if_any()
            self._chunks_received = False
            self.status_indicator.set_tokens("")

    @Slot(str)
    def _on_log_message(self, text, is_header=False, is_global=False):
        """原始日志追加 + 结构化活动记录"""
        self.workspace.add_log(text, is_header=is_header)
        self._add_activity_from_log(text, is_header, is_global)

    def _add_activity(self, title: str, category: str, detail: str = "", is_global: bool = False):
        """添加结构化活动并刷新面板

        :param is_global: True 表示不绑定当前项目，归入全局活动列表
        """
        project_path = "" if is_global else self._project_root
        self.activity_service.add(
            title=title,
            category=category,
            project_path=project_path,
            summary=detail[:60] if detail else title,
            detail=detail or title,
        )
        self._refresh_activities()

    def _refresh_activities(self):
        """刷新活动面板：显示当前项目活动 + 全局活动"""
        self.workspace.refresh_activities(
            self.activity_service.list_by_project(self._project_root)
        )

    def _add_activity_from_log(self, text: str, is_header: bool = False, is_global: bool = False):
        """从日志文本推断活动类别并记录"""
        category = "系统"
        title = text
        detail = text

        if text.startswith("📂 切换项目目录") or text.startswith("📂 已加载项目") or text.startswith("📂 新建项目会话"):
            category = "项目"
            title = "切换项目目录"
        elif text.startswith("📁 资源管理器"):
            category = "文件"
            title = "打开文件"
            path_part = text[len("📁 资源管理器"):].strip()
            try:
                size = os.path.getsize(path_part) if os.path.exists(path_part) else 0
                detail = f"路径: {path_part}\n大小: {size} bytes"
            except Exception:
                detail = text
        elif text.startswith("📝 新会话"):
            category = "对话"
            title = "新建对话"
        elif text.startswith("📂 切换会话"):
            category = "对话"
            title = "切换对话"
        elif text.startswith("▶ 用户:"):
            category = "对话"
            title = "用户输入"
        elif text.startswith("🔄 切换模式") or text.startswith("🔄 切换模型"):
            category = "系统"
            title = "模式/模型切换"
        elif text.startswith("🔧"):
            category = "系统"
            title = "设置更新"
        elif text.startswith("🖥 切换解释器"):
            category = "系统"
            title = "切换解释器"
        elif text.startswith("[ERR]") or text.startswith("⏹") or text.startswith("[STOP]"):
            category = "系统"
            title = "系统事件"

        self._add_activity(title, category, detail, is_global=is_global)

    def _toggle_log_panel(self, visible: bool):
        self._log_panel_visible = visible
        self.workspace.setVisible(visible)
        self.chat_view.set_log_panel_checked(visible)
        self.persistence_service.update_nested("ui.log_panel", {"visible": visible})

    def _apply_ui_settings(self):
        ui_cfg = self.config_service.get("ui", {}).get("log_panel", {})
        self._log_max_lines = ui_cfg.get("max_lines", 500)
        self.workspace.set_logs_max_lines(self._log_max_lines)
        visible = ui_cfg.get("visible", True)
        if visible != self._log_panel_visible:
            self._toggle_log_panel(visible)

    @Slot(str, str, int, int)
    def _on_token_used(self, provider, model, input_tokens, output_tokens):
        """token 持久化（metrics UI 由 _on_turn_metrics_ready 处理）"""
        self.session_service.log_token_usage(provider, model, input_tokens, output_tokens)

    @Slot(object)
    def _on_turn_metrics_ready(self, metrics: TurnMetrics):
        """接收到本轮指标：缓存 brief 格式，等 result_ready 后显示在内容下方"""
        try:
            self._pending_metrics = metrics
            # 详细指标先写入日志
            self._on_log_message(f"📊 {metrics.format_detail()}", is_header=False)
        except Exception as e:
            self._on_log_message(f"[WARN] 指标处理失败: {e}")

    @Slot(str, dict, str, int)
    def _on_tool_executed(self, name: str, args: dict, result: str, elapsed_ms: int):
        """工具执行回传：追加到共享输出面板"""
        try:
            self.workspace.shared_output.append_execution(name, args, result, elapsed_ms=elapsed_ms)
        except Exception as e:
            self._on_log_message(f"[WARN] 共享输出面板追加失败: {e}")

    @Slot(str, str)
    def _add_task(self, task_id, description):
        self.task_list.add_task(description, task_id)

    @Slot(str, str)
    def _finish_task(self, task_id, result):
        self.task_list.finish_task(task_id, result)

    @Slot(str, str)
    def _on_tool_confirm_required(self, tool_name, command):
        reply = QMessageBox.warning(
            self, "敏感操作确认",
            f"工具 <b>{tool_name}</b> 即将执行以下命令：\n\n{command}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        confirmed = (reply == QMessageBox.Yes)
        if self._worker is not None:
            self._worker.set_confirm_result(confirmed)
        if not confirmed:
            self._on_log_message(f"⛔ 用户取消了敏感操作 {command}")

    @Slot(str)
    def _on_file_selected(self, path):
        self._on_log_message(f"📁 资源管理器 {path}")
        self.context_service.set_selected_paths([path])
        self.workspace.open_document(path)

    def closeEvent(self, event):
        # 停止所有 Worker 线程（v3.11: 多会话 Registry）
        all_workers = list(self._workers.values())
        if self._worker and self._worker not in all_workers:
            all_workers.append(self._worker)
        for worker in all_workers:
            if worker and worker.isRunning():
                try:
                    worker.stop()
                except Exception:
                    pass
        for worker in all_workers:
            if worker and worker.isRunning():
                worker.quit()
                if not worker.wait(5000):
                    worker.terminate()
                    worker.wait(1000)
        # 关闭线程池
        cpu_executor = getattr(self, '_cpu_executor', None)
        if cpu_executor:
            try:
                cpu_executor.shutdown(wait=True)
            except Exception:
                pass
        event.accept()

