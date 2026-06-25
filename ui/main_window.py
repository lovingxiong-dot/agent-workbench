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
from services.config_service import ConfigService
from services.session_service import SessionService
from services.theme_service import ThemeService
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
        self.theme_service = ThemeService()
        self.mode_manager = ModeManager(config_path)
        self.llm_registry = LLMRegistry(config_path, config_write)
        self.memory_manager = MemoryManager(self.config_service.get("memory", {}))

        # UI 配置
        ui_cfg = self.config_service.get("ui", {}).get("log_panel", {})
        self._log_panel_visible = ui_cfg.get("visible", True)
        self._log_max_lines = ui_cfg.get("max_lines", 500)

        # ── 全局状态 ────────────────────────────
        self._current_session = "default"
        self._sessions = {"default": {"title": "默认会话", "messages": []}}
        self._current_mode = "ask"
        self._current_llm = None
        self._current_tools = []
        self._current_model_name = "tool-agent"
        self._worker = None  # Active AgentWorker
        self._chunks_received = False

        # ── UI 构建 ─────────────────────────────
        self._apply_theme()
        self._setup_ui()

        # ── 连接信号 ────────────────────────────
        self.chat_view.model_changed.connect(self._on_model_changed)
        self.chat_view.settings_clicked.connect(self._open_settings)
        self.chat_view.stop_requested.connect(self._on_stop_generation)
        self.chat_view.log_panel_toggled.connect(self._toggle_log_panel)
        self.chat_view.set_log_panel_checked(self._log_panel_visible)

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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.file_tree = FileTreeWidget(project_root)
        self.file_tree.file_selected.connect(self._on_file_selected)

        self.conversation_list = ConversationListWidget()
        self.conversation_list.new_conversation.connect(self._new_conversation)
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
        self.chat_view.set_header(mode_name, llm_name, self._sessions[self._current_session]["title"])
        self.chat_view.populate_models(providers, llm_name)
        self.status_indicator.set_mode(mode_name)
        self.status_indicator.set_model(llm_name)
        self._on_log_message(f"🔄 切换模式: {mode_name} / {llm_name}", is_header=True)

    def _on_mode_clicked(self, mode_name):
        self._init_mode(mode_name)

    def _on_model_changed(self, llm_name):
        self._current_llm = self.llm_registry.get_llm(llm_name)
        self._current_model_name = llm_name
        llm_registry_config = self.config_service.get("manual_modes", {})
        llm_registry_config[self._current_mode] = llm_registry_config.get(self._current_mode, {})
        llm_registry_config[self._current_mode]["current_model"] = llm_name
        self.llm_registry._save()

        provider = self.llm_registry.get_provider_config(llm_name)
        self.chat_view.set_header(self._current_mode, llm_name, self._sessions[self._current_session]["title"])
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
        self.chat_view.set_header(self._current_mode, self._current_model_name, self._sessions[self._current_session]["title"])
        self._on_log_message("🔧 模型设置已更新")

    # ═══════════════════════════════════════════════════
    # 对话管理
    # ═══════════════════════════════════════════════════
    def _init_default_session(self):
        self.conversation_list.add_conversation("default", "默认会话", active=True)
        # Restore default session messages from DB if they exist
        try:
            msgs = self.session_service.get_messages("default")
            if msgs:
                self._sessions["default"]["messages"] = msgs
                # 同时注入 LangChain 记忆，保证 LLM 能看到完整上下文
                from langchain_core.messages import HumanMessage, AIMessage
                history = self.memory_manager.get_session_history("default")
                history.clear()
                for msg in msgs:
                    self._render_stored_message(msg)
                    if msg["role"] == "user":
                        history.add_message(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "ai":
                        history.add_message(AIMessage(content=msg["content"]))
                # Restore title if set by first message
                if msgs and len(msgs) > 0:
                    first = msgs[0]
                    title = first["content"][:30]
                    self._sessions["default"]["title"] = title
                    self._update_conversation_title("default", title)
                self.chat_view.set_header(self._current_mode, self._current_model_name,
                                          self._sessions["default"]["title"])
                self._on_log_message(f"Restored {len(msgs)} messages from last session")
                return
        except Exception:
            pass
        self.chat_view.set_header(self._current_mode, self._current_model_name, "默认会话")
        self.chat_view.append_system(f"欢迎使用 AI Agent Workbench v2。当前模式：{self._current_mode.capitalize()}。")
        self.chat_view.append_system("新特性：流式输出 · 模型管理 · 对话持久化 · 键盘快捷键")

    def _restore_conversations(self):
        """从 SQLite 恢复对话列表"""
        try:
            saved = self.session_service.list_conversations()
            for conv in saved:
                if conv["id"] != "default":
                    self._sessions[conv["id"]] = {"title": conv["title"], "messages": []}
                    self.conversation_list.add_conversation(conv["id"], conv["title"])
                    # Load messages
                    msgs = self.session_service.get_messages(conv["id"])
                    for msg in msgs:
                        self._sessions[conv["id"]]["messages"].append(msg)
        except Exception as e:
            pass  # Silently handle - DB might not exist yet

    def _new_conversation(self):
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        title = f"新对话 {len(self._sessions)}"
        self._sessions[session_id] = {"title": title, "messages": []}
        self.memory_manager.get_session_history(session_id)
        self.conversation_list.add_conversation(session_id, title, active=True)
        self._current_session = session_id
        self.chat_view.clear()
        self.chat_view.set_header(self._current_mode, self._current_model_name, title)
        # 持久化
        self.session_service.create_conversation(session_id, title, self._current_mode, self._current_model_name)
        self._on_log_message(f"📝 新会话 {title}", is_header=True)

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
        if session_id == "default" and len(self._sessions) == 1:
            QMessageBox.information(self, "提示", "不能删除唯一的默认会话")
            return
        self.conversation_list.remove_conversation(session_id)
        self._sessions.pop(session_id, None)
        self.memory_manager.store.pop(session_id, None)
        # 持久化
        self.session_service.delete_conversation(session_id)
        if self._current_session == session_id:
            first = next(iter(self._sessions.keys()), "default")
            self._switch_conversation(first)

    def _update_conversation_title(self, session_id, title):
        for i in range(self.conversation_list.list.count()):
            item = self.conversation_list.list.item(i)
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

        # 1. UI 和 session 持久化（记忆稍后再注入，避免 worker 内部重复追加）
        self._sessions[self._current_session]["messages"].append({"role": "user", "content": user_text})
        self.chat_view.append_user(user_text)
        self.session_service.add_message(self._current_session, "user", user_text)

        session = self._sessions[self._current_session]
        if len(session["messages"]) == 1:
            title = user_text[:20] + "..." if len(user_text) > 20 else user_text
            session["title"] = title
            self._update_conversation_title(self._current_session, title)
            self.chat_view.set_header(self._current_mode, self._current_model_name, title)
            self.session_service.create_conversation(self._current_session, title, self._current_mode, self._current_model_name)

        # 2. 系统提示与记忆
        mode_config = self.config_service.get_mode_config(self._current_mode)
        system_prompt = mode_config.get("system_prompt", "你是全能 AI 助手。")
        user_rules = self.config_service.get("user_rules", [])

        # 读取多轮工具调用上限和任务超时
        max_tool_rounds = self.config_service.get_max_tool_rounds(self._current_mode)
        task_timeout = self.config_service.get_task_timeout(self._current_mode)

        history = self.memory_manager.get_session_history(self._current_session)
        from langchain_core.messages import HumanMessage
        history.add_message(HumanMessage(content=user_text))  # 仅在此处加入一次
        # 3. 重置流式状态；时 worker 由槽函数的 sender 校验自动忽略）
        #    不主动 stop/disconnect，避免中断即将生成的最终回复
        self._chunks_received = False

        # 4. 启动新 worker
        worker = AgentWorker(
            user_text=user_text,
            mode_name=self._current_mode,
            current_llm=self._current_llm,
            current_tools=self._current_tools,
            session_id=self._current_session,
            system_prompt=system_prompt,
            tool_map=TOOL_MAP,
            tool_definitions=TOOL_DEFINITIONS,
            enable_streaming=True,
            chat_history=list(history.messages),  # 已包含当前用户消息
            user_rules=user_rules,
            max_tool_rounds=max_tool_rounds,
            task_timeout=task_timeout,
        )
        self._worker = worker

        # 使用闭包捕获当前 worker 引用，避免跨线程 QueuedConnection 中 self.sender() 不可靠
        def current_only(slot):
            def wrapper(*args):
                if worker is not self._worker:
                    return
                slot(*args)
            return wrapper

        worker.chunk_ready.connect(current_only(self._on_chunk))
        worker.result_ready.connect(current_only(self._on_reply))
        worker.log_message.connect(current_only(self._on_log_message))
        worker.task_created.connect(current_only(self._add_task))
        worker.task_finished.connect(current_only(self._finish_task))
        worker.confirm_required.connect(current_only(self._on_confirm_required))
        worker.token_used.connect(current_only(self._on_token_used))
        worker.finished.connect(worker.deleteLater)
        worker.start()

        self.chat_view.set_streaming(True)
        self.status_indicator.set_tokens("生成中...")

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
    def _on_reply(self, text):
        """完整回复（由 AgentWorker 在流式完成后发射）"""
        self.chat_view.finalize_stream()
        # 流式过程中已经实时渲染，若已收到 chunk 则不再追加完整气泡
        if text and text.strip():
            if not self._chunks_received:
                self.chat_view.append_ai(text)
            self._sessions[self._current_session]["messages"].append({"role": "ai", "content": text})
            self.session_service.add_message(self._current_session, "ai", text)
            # 注入 LangChain 记忆
            from langchain_core.messages import AIMessage
            self.memory_manager.get_session_history(self._current_session).add_message(
                AIMessage(content=text)
            )
        self._chunks_received = False
        self.status_indicator.set_tokens("")

    @Slot(str)
    def _on_log_message(self, text, is_header=False):
        self.workspace.add_log(text, is_header=is_header)

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
        self.session_service.log_token_usage(provider, model, input_tokens, output_tokens)
        total = input_tokens + output_tokens
        self.status_indicator.set_tokens(f"Tokens: {total}")

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
        self.workspace.open_document(path)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
        event.accept()
