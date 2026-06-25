"""
主窗口 — AI Agent 工作台
整合所有模块化组件，管理全局状态
"""
import os
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QStackedWidget, QMessageBox,
    QStyleFactory,
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPalette, QColor

from agent_engine import ModeManager, LLMRegistry, MemoryManager
from agent_engine.phase_manager import PhaseManager, TaskItem
from services.config_service import ConfigService
from services.session_service import SessionService
from services.theme_service import ThemeService
from services.project_service import ProjectService
from services.activity_service import ActivityService
from services.context_service import ContextService
from services.metrics_collector import MetricsCollector, TurnMetrics
from workers.agent_worker import AgentWorker, TOOL_DEFINITIONS
from ui.widgets import (
    SidebarButton, FileTreeWidget, ConversationListWidget,
    TaskListWidget, TerminalWidget, StatusIndicator,
    WorkspaceWidget,
)
from ui.dialogs import SettingsDialog, ProviderFormDialog
from ui.chat_view import ChatView
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent 工作台 v2 · 手动模式")
        self.resize(1600, 950)

        # ── 服务初始化 ──────────────────────────
        config_path = resource_path("config.yaml")
        config_write = (
            os.path.join(os.path.dirname(sys.executable), "config.yaml")
            if getattr(sys, 'frozen', False)
            else config_path
        )
        self.config_service = ConfigService(config_path, writable_path=config_write)
        self.session_service = SessionService()
        self.project_service = ProjectService(self.session_service, self.config_service)
        self.context_service = ContextService(self.project_service, self)
        # 活动记录持久化到可写目录（兼容 PyInstaller）
        activity_storage_path = (
            os.path.join(os.path.dirname(sys.executable), "storage", "activities.json")
            if getattr(sys, 'frozen', False)
            else "storage/activities.json"
        )
        self.activity_service = ActivityService(activity_storage_path)
        self.theme_service = ThemeService()
        self.mode_manager = ModeManager(config_path)
        self.llm_registry = LLMRegistry(config_path, config_write)
        self.memory_manager = MemoryManager(self.config_service.get("memory", {}))

        # UI 配置
        ui_cfg = self.config_service.get("ui", {}).get("log_panel", {})
        self._log_panel_visible = ui_cfg.get("visible", True)
        self._log_max_lines = ui_cfg.get("max_lines", 500)

        # ── 全局状态 ────────────────────────────
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._project_root = self.project_service.detect_current_project(app_root)
        self._current_session = ""
        self._sessions = {}
        self._current_mode = "ask"
        self._current_llm = None
        self._current_tools = []
        self._current_model_name = "tool-agent"
        self._worker = None  # Active AgentWorker
        self._chunks_received = False
        self._pending_metrics = None  # 等待 AI 回复完成后显示的 metrics
        self._phase_manager = PhaseManager(self)
        self._current_phase = "idle"
        self._phase_task_list = []
        self._phase_results = []

        # ── UI 构建 ─────────────────────────────
        self._apply_theme()
        self._setup_ui()

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
        self.workspace.document_opened.connect(self._on_document_opened)
        self.workspace.document_closed.connect(self._on_document_closed)

        # PhaseManager 信号
        self._phase_manager.phase_changed.connect(self._on_phase_changed)
        self._phase_manager.analyze_required.connect(self._on_analyze_required)
        self._phase_manager.confirm_required.connect(self._on_confirm_required)
        self._phase_manager.execute_required.connect(self._on_execute_required)
        self._phase_manager.verify_required.connect(self._on_verify_required)
        self._phase_manager.archive_required.connect(self._on_archive_required)
        self._phase_manager.flow_finished.connect(self._on_phase_flow_finished)
        self._phase_manager.error_occurred.connect(self._on_phase_error)

        # ── 初始化 ──────────────────────────────
        self._init_mode("ask")
        self._init_default_session()
        self.chat_view.populate_models(
            self.llm_registry.list_providers(),
            self._current_model_name
        )

        # ── 持久化恢复 ──────────────────────────
        self._restore_conversations()

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
        self.workspace = WorkspaceWidget()
        self.workspace.setMinimumWidth(300)
        self.workspace.set_logs_max_lines(self._log_max_lines)
        self.workspace.set_project_path(self._project_root)
        self.workspace.setVisible(self._log_panel_visible)
        main_layout.addWidget(self.workspace)

        # ── 状态栏 ──────────────────────────────
        self.status_bar = QStatusBar()
        self.status_indicator = StatusIndicator()
        self.status_bar.addWidget(self.status_indicator, 1)
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
        self._on_log_message(f"🔄 切换模式: {mode_name} / {llm_name}", is_header=True)

    def _on_mode_clicked(self, mode_name):
        self._init_mode(mode_name)

    def _on_model_changed(self, llm_name):
        self._current_llm = self.llm_registry.get_llm(llm_name)
        self._current_model_name = llm_name
        # 持久化当前模式选用的模型到 config.yaml
        llm_registry_config = self.config_service.config.setdefault("manual_modes", {})
        llm_registry_config[self._current_mode] = llm_registry_config.get(self._current_mode, {})
        llm_registry_config[self._current_mode]["current_model"] = llm_name
        self.config_service.save()

        provider = self.llm_registry.get_provider_config(llm_name)
        current_title = self._sessions.get(self._current_session, {}).get("title", "未命名会话")
        self.chat_view.set_header(self._current_mode, llm_name, current_title)
        self.status_indicator.set_model(llm_name)
        self._on_log_message(f"🔄 切换模型: {llm_name} ({provider.get('model', '?')})")

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
        if self._current_model_name not in providers:
            self._current_model_name = next(iter(providers.keys()), "tool-agent")
            self._current_llm = self.llm_registry.get_llm(self._current_model_name)
        self.chat_view.populate_models(providers, self._current_model_name)
        current_title = self._sessions.get(self._current_session, {}).get("title", "未命名会话")
        self.chat_view.set_header(self._current_mode, self._current_model_name, current_title)
        self._on_log_message("🔧 模型设置已更新")

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
            self._new_conversation(project_path=self._project_root)
        else:
            self._new_conversation(project_path="")

    def _switch_project(self, project_path: str, is_init=False):
        """切换项目目录上下文：加载该目录下会话与全局纯对话"""
        project_path = self.project_service.normalize_path(project_path)
        self._project_root = project_path
        self.context_service.set_project_root(project_path)
        self.file_tree.set_root_path(project_path)
        self._sessions = {}
        self.conversation_list.clear_conversations()
        self.conversation_list.set_project_label(project_path)
        self.memory_manager.store.clear()
        self.chat_view.clear()

        has_any = False

        # 1) 加载全局纯对话
        global_sessions = self.project_service.list_sessions("")
        for conv in global_sessions:
            self._sessions[conv["id"]] = {"title": conv["title"], "messages": []}
            msgs = self.session_service.get_messages(conv["id"])
            self._sessions[conv["id"]]["messages"] = msgs
            self.conversation_list.add_conversation(conv["id"], conv["title"], project_path="")
            has_any = True

        # 2) 加载当前项目目录下会话
        project_sessions = self.project_service.list_sessions(project_path)
        for conv in project_sessions:
            self._sessions[conv["id"]] = {"title": conv["title"], "messages": []}
            msgs = self.session_service.get_messages(conv["id"])
            self._sessions[conv["id"]]["messages"] = msgs
            self.conversation_list.add_conversation(conv["id"], conv["title"], project_path=project_path)
            has_any = True

        if has_any:
            # 优先激活项目会话；无则激活全局会话
            first = project_sessions[0] if project_sessions else global_sessions[0]
            self._switch_conversation(first["id"])
            if not is_init:
                self._on_log_message(
                    f"📂 已加载项目: {project_path} ({len(project_sessions)} 个项目会话, {len(global_sessions)} 个全局会话)",
                    is_header=True,
                )
        else:
            # 无任何会话时，自动在当前项目创建一个默认会话
            session_id = self.project_service.create_session(
                project_path=project_path,
                mode=self._current_mode,
                model=self._current_model_name,
                title="新对话",
            )
            self._sessions[session_id] = {"title": "新对话", "messages": []}
            self.conversation_list.add_conversation(session_id, "新对话", project_path=project_path, active=True)
            self._current_session = session_id
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
        session_id = self.project_service.create_session(
            project_path=project_path,
            mode=self._current_mode,
            model=self._current_model_name,
            title="新对话",
        )
        self._sessions[session_id] = {"title": "新对话", "messages": []}
        self.memory_manager.get_session_history(session_id)
        self.conversation_list.add_conversation(session_id, "新对话", project_path=project_path, active=True)
        self._current_session = session_id
        self.chat_view.clear()
        self.chat_view.set_header(self._current_mode, self._current_model_name, "新对话")
        label = "全局" if project_path == "" else project_path
        self._on_log_message(f"📝 新会话 @ {label}", is_header=True)

    def _switch_conversation(self, session_id):
        self._current_session = session_id
        session = self._sessions[session_id]
        self.chat_view.clear()
        self.chat_view.set_header(self._current_mode, self._current_model_name, session["title"])
        # ★ 注入 LangChain 上下文
        history = self.memory_manager.get_session_history(session_id)
        history.clear()
        from langchain_core.messages import HumanMessage, AIMessage
        for msg in session["messages"]:
            self._render_stored_message(msg)
            if msg["role"] == "user":
                history.add_message(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                history.add_message(AIMessage(content=msg["content"]))
        self._on_log_message(f"📂 切换会话: {session['title']}")

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
        self.conversation_list.remove_conversation(session_id)
        self._sessions.pop(session_id, None)
        self.memory_manager.store.pop(session_id, None)
        # 持久化
        self.session_service.delete_conversation(session_id)
        if self._current_session == session_id:
            first = next(iter(self._sessions.keys()), "")
            if first:
                self._switch_conversation(first)

    def _update_conversation_title(self, session_id, title):
        for lst in (self.conversation_list.project_list, self.conversation_list.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    item.setText(title)
                    item.setToolTip(title)
                    return

    # ═══════════════════════════════════════════════════
    # 消息发送
    # ═══════════════════════════════════════════════════
    def _send_message(self, user_text):
        # 0. 写入本轮日志标题
        display_text = user_text[:80] + ("..." if len(user_text) > 80 else "")
        self._on_log_message(f"▶ 用户: {display_text}", is_header=True)

        # 1. UI 和 session 持久化
        self._sessions[self._current_session]["messages"].append({"role": "user", "content": user_text})
        self.chat_view.append_user(user_text)
        self.session_service.add_message(self._current_session, "user", user_text)

        session = self._sessions[self._current_session]
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

        # 2. 启动 Phase-driven 工作流
        context_text = self.context_service.build_prompt_context()
        self._phase_manager.start(user_text, self._current_mode, context_text)

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
        """Analyze 阶段：启动一个不绑定工具的 worker 生成 task list"""
        self.chat_view.append_phase_message("analyze", "正在分析需求...")
        self._run_phase_worker(
            user_text=user_text,
            phase="analyze",
            context_text=context,
            on_result=self._on_analyze_result,
        )

    @Slot(list)
    def _on_confirm_required(self, task_list):
        """Confirm 阶段：显示任务清单等待用户确认"""
        self._phase_task_list = list(task_list)
        self.chat_view.set_phase_indicator("confirm", len(self._phase_task_list))
        self.chat_view.append_phase_message("confirm", "请确认以下任务清单")
        self.chat_view.show_confirmation(self._phase_task_list)

    @Slot(list)
    def _on_execute_required(self, task_list):
        """Execute 阶段：绑定工具执行用户请求"""
        self._phase_task_list = list(task_list)
        self.chat_view.hide_confirmation()
        self.chat_view.append_phase_message("execute", "开始执行任务")
        # 组装 execute 阶段上下文
        context_text = self.context_service.get_phase_context("execute")
        # 把 task list 简要注入，让 LLM 知道执行范围
        task_summary = "\n".join(f"- {t.description}" for t in self._phase_task_list)
        user_text = f"请按以下任务清单执行：\n{task_summary}\n\n原始需求：\n{self._phase_manager.current_context().user_text}"
        self._run_phase_worker(
            user_text=user_text,
            phase="execute",
            context_text=context_text,
            on_result=self._on_execute_result,
        )

    @Slot(list, str)
    def _on_verify_required(self, execution_results, mode):
        """Verify 阶段：运行测试 + LLM 验证"""
        self.chat_view.append_phase_message("verify", "正在验证执行结果...")
        self.chat_view.show_skip_verify()
        # 运行本地检查（语法检查 + 单元测试）
        verification_details = self._run_local_verification()
        # 让 LLM 检查执行结果
        context_text = self.context_service.get_phase_context("verify")
        result_summary = "\n".join(
            f"- {r.get('task', '')}: {r.get('result', '')[:200]}"
            for r in execution_results
        ) if execution_results else "无执行结果"
        user_text = (
            f"执行结果摘要：\n{result_summary}\n\n"
            f"本地验证结果：\n{verification_details}\n\n"
            "请判断任务是否完成，是否存在明显错误。"
        )
        self._run_phase_worker(
            user_text=user_text,
            phase="verify",
            context_text=context_text,
            on_result=lambda text: self._on_verify_result(text, verification_details),
        )

    @Slot(str)
    def _on_archive_required(self, mode):
        """Archive 阶段：普通对话直接收尾；若用户触发存档则执行"""
        self.chat_view.append_phase_message("archive", "任务收尾")
        self.chat_view.hide_skip_verify()
        user_text = self._phase_manager.current_context().user_text
        if self._is_archive_request(user_text):
            self._archive_project()
        self._phase_manager.on_archive_complete(True, "工作流完成")

    @Slot(bool, str)
    def _on_phase_flow_finished(self, success, message):
        self._current_phase = "idle"
        self._phase_task_list = []
        self._phase_results = []
        self.chat_view.clear_phase_ui()
        if not success:
            self.chat_view.append_system(f"⚠️ {message}")

    @Slot(str, str)
    def _on_phase_error(self, code, detail):
        self._current_phase = "idle"
        self.chat_view.clear_phase_ui()
        self.chat_view.append_system(f"❌ Phase 错误 [{code}]: {detail}")
        self._on_log_message(f"[ERR] Phase {code}: {detail}")

    def _on_phase_confirmed(self):
        """用户点击确认执行"""
        self.chat_view.hide_confirmation()
        self._phase_manager.on_user_confirm(True)

    def _on_phase_reanalyze(self):
        """用户点击重新分析：重启 analyze"""
        self.chat_view.hide_confirmation()
        ctx = self._phase_manager.current_context()
        self._phase_manager.reset()
        context_text = self.context_service.get_phase_context("analyze")
        self._phase_manager.start(ctx.user_text, ctx.mode, context_text)

    def _on_phase_skip_verify(self):
        """用户点击跳过验证"""
        self.chat_view.hide_skip_verify()
        self._phase_manager.on_verify_complete(True, "用户跳过验证")

    def _on_analyze_result(self, text):
        """Analyze 阶段结果：解析 task list"""
        task_list = PhaseManager.parse_task_list(text)
        self._phase_task_list = task_list
        self.chat_view.set_task_progress(0, len(task_list))
        self._phase_manager.on_analyze_complete(task_list)

    def _on_execute_result(self, text):
        """Execute 阶段结果：显示并保存到 session"""
        if text and text.strip():
            self._append_ai_message(text)
            self._phase_results.append({"task": "execute", "result": text})
        self._phase_manager.on_execute_complete(self._phase_results)

    def _on_verify_result(self, text, local_details):
        """Verify 阶段结果：显示验证结论"""
        self.chat_view.hide_skip_verify()
        if text and text.strip():
            self.chat_view.append_ai(f"**验证结果**\n\n{text}")
        passed = "通过" in text or "passed" in text.lower() or "未通过" not in text
        self._phase_manager.on_verify_complete(passed, f"{local_details}\n\n{text}")

    def _run_phase_worker(self, user_text, phase, context_text, on_result, system_prompt=None):
        """通用 Phase Worker 创建与启动"""
        mode_config = self.config_service.get_mode_config(self._current_mode)
        default_prompt = mode_config.get("system_prompt", "你是全能 AI 助手。")
        user_rules = self.config_service.get("user_rules", [])
        max_tool_rounds = self.config_service.get_max_tool_rounds(self._current_mode)
        task_timeout = self.config_service.get_task_timeout(self._current_mode)
        history = self.memory_manager.get_session_history(self._current_session)

        # execute 阶段才需要把用户消息保留在历史中
        chat_history = list(history.messages) if phase == "execute" else []

        worker = AgentWorker(
            user_text=user_text,
            mode_name=self._current_mode,
            current_llm=self._current_llm,
            current_tools=self._current_tools if phase == "execute" else [],
            session_id=self._current_session,
            system_prompt=system_prompt or default_prompt,
            tool_map=TOOL_MAP,
            tool_definitions=TOOL_DEFINITIONS if phase == "execute" else [],
            enable_streaming=True,
            chat_history=chat_history,
            user_rules=user_rules,
            max_tool_rounds=max_tool_rounds,
            task_timeout=task_timeout,
            project_root=self.context_service.get_project_root(),
            workspace_context=context_text,
            phase=phase,
        )
        self._worker = worker
        self._chunks_received = False

        def current_only(slot):
            def wrapper(*args):
                if worker is not self._worker:
                    return
                slot(*args)
            return wrapper

        worker.chunk_ready.connect(current_only(self._on_chunk))
        worker.result_ready.connect(current_only(lambda text: self._on_phase_result(text, on_result)))
        worker.log_message.connect(current_only(self._on_log_message))
        worker.task_created.connect(current_only(self._add_task))
        worker.task_finished.connect(current_only(self._finish_task))
        worker.confirm_required.connect(current_only(self._on_confirm_required))
        worker.token_used.connect(current_only(self._on_token_used))
        worker.turn_metrics_ready.connect(current_only(self._on_turn_metrics_ready))
        worker.finished.connect(worker.deleteLater)
        worker.start()

        self.chat_view.set_streaming(True)
        self.status_indicator.set_tokens("生成中...")

    def _on_phase_result(self, text, on_result):
        """通用 phase result 分发"""
        self.chat_view.finalize_stream()
        if text and text.strip() and not self._chunks_received:
            # analyze/verify 阶段如果未收到 chunk，也显示原始文本
            if self._current_phase in ("analyze", "verify"):
                self.chat_view.append_ai(text)
        # 任何产生 LLM 输出的阶段都在内容下方追加 metrics footer
        if self._pending_metrics:
            self.chat_view.append_ai_metrics_footer(self._pending_metrics.format_brief())
            self._pending_metrics = None
        self._chunks_received = False
        self.status_indicator.set_tokens("")
        on_result(text)

    def _append_ai_message(self, text):
        """把 AI 回复持久化到 session 和记忆"""
        if not text or not text.strip():
            return
        self._sessions[self._current_session]["messages"].append({"role": "ai", "content": text})
        self.session_service.add_message(self._current_session, "ai", text)
        from langchain_core.messages import AIMessage
        self.memory_manager.get_session_history(self._current_session).add_message(AIMessage(content=text))

    def _run_local_verification(self) -> str:
        """运行本地语法检查和单元测试"""
        import subprocess
        lines = []
        # 语法检查
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", "main.py"],
                cwd=self._project_root or None,
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines.append("✅ 语法检查通过 (main.py)")
            else:
                lines.append(f"❌ 语法检查失败: {result.stderr}")
        except Exception as e:
            lines.append(f"⚠️ 语法检查异常: {e}")

        # 单元测试
        try:
            result = subprocess.run(
                ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=self._project_root or None,
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                lines.append("✅ 单元测试通过")
            else:
                lines.append(f"❌ 单元测试失败: {result.stderr[:500]}")
        except Exception as e:
            lines.append(f"⚠️ 单元测试异常: {e}")
        return "\n".join(lines)

    def _is_archive_request(self, user_text: str) -> bool:
        """判断用户输入是否触发存档流程"""
        return "请存档" in user_text or "请存档并推送" in user_text

    def _archive_project(self):
        """执行项目存档（简化版：调用外部脚本或直接 commit/tag）"""
        self._on_log_message("📦 执行项目存档...", is_header=True)
        # 实际存档逻辑由用户规则驱动，这里仅作标记
        self.chat_view.append_system("📦 已触发项目存档流程")

    def _on_stop_generation(self):
        """用户点击停止"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self.chat_view.finalize_stream()
            self._on_log_message("⏹ 用户停止了生成")

    @Slot(str)
    def _on_chunk(self, chunk):
        """流式输出每个 token"""
        self._chunks_received = True
        self.chat_view.append_chunk(chunk)

    @Slot(str)
    def _on_log_message(self, text, is_header=False):
        """原始日志追加 + 结构化活动记录"""
        self.workspace.add_log(text, is_header=is_header)
        self._add_activity_from_log(text, is_header)

    def _add_activity(self, title: str, category: str, detail: str = ""):
        """添加结构化活动并刷新面板"""
        self.activity_service.add(
            title=title,
            category=category,
            project_path=self._project_root,
            summary=detail[:60] if detail else title,
            detail=detail or title,
        )
        self._refresh_activities()

    def _refresh_activities(self):
        self.workspace.refresh_activities(
            self.activity_service.list_by_project(self._project_root)
        )

    def _add_activity_from_log(self, text: str, is_header: bool = False):
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

        self._add_activity(title, category, detail)

    def _toggle_log_panel(self, visible: bool):
        self._log_panel_visible = visible
        self.workspace.setVisible(visible)
        self.chat_view.set_log_panel_checked(visible)
        ui_cfg = self.config_service.config.setdefault("ui", {}).setdefault("log_panel", {})
        ui_cfg["visible"] = visible
        self.config_service.save()

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

    @Slot(str, str)
    def _add_task(self, task_id, description):
        self.task_list.add_task(description, task_id)

    @Slot(str, str)
    def _finish_task(self, task_id, result):
        self.task_list.finish_task(task_id, result)

    @Slot(str, str)
    def _on_confirm_required(self, tool_name, command):
        reply = QMessageBox.warning(
            self, "敏感操作确认",
            f"工具 <b>{tool_name}</b> 即将执行以下命令：\n\n{command}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        self._worker.confirm_result = (reply == QMessageBox.Yes)
        self._worker.confirm_event.set()
        if not self._worker.confirm_result:
            self._on_log_message(f"⛔ 用户取消了敏感操作 {command}")

    @Slot(str)
    def _on_file_selected(self, path):
        self._on_log_message(f"📁 资源管理器 {path}")
        self.context_service.set_selected_paths([path])
        self.workspace.open_document(path)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
        event.accept()
