"""
main_window.py — v4 主窗口（Solo 极简风格 + Trae 暗色/浅色主题）

布局：
- 固定两栏：左栏 280px，右栏填充
- 左栏：模型下拉 + 主题切换 + 「+ 新任务」按钮 + 会话列表
- 右栏：会话标题/环境信息 + 消息流 + 输入框

主题：
- 支持 dark / light 两套配色，通过左栏顶部 🌙/☀️ 切换
- 主题状态持久化到 config.yaml 的 app.theme

禁止：
- 三栏布局、大型状态栏、容量标签、Phase/工具按钮、资源管理器/终端/文档编辑器
"""
import html

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QStyleFactory,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPalette, QColor, QFont, QTextCursor

from markdown import markdown as md

from .repository import SessionRepository
from .event_bus import MessageBus
from .orchestrator import SessionOrchestrator
from .ui_renderer import UIRenderer
from .conversation_list import ConversationListWidget
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


THEMES = {
    "dark": {
        "bg_primary": "#1e1e1e",
        "bg_sidebar": "#252526",
        "bg_input": "#2d2d30",
        "bg_hover": "#2a2d2e",
        "bg_selected": "#37373d",
        "bg_bubble_user": "#0e639c",
        "bg_bubble_ai": "#2d2d30",
        "bg_system_card": "#252526",
        "border": "#3e3e42",
        "border_bubble_ai": "#3e3e42",
        "text_primary": "#cccccc",
        "text_secondary": "#858585",
        "text_inverse": "#ffffff",
        "accent": "#007acc",
        "accent_hover": "#1177bb",
        "send_btn": "#0e639c",
        "send_btn_hover": "#1177bb",
        "stop_btn": "#3e3e42",
        "stop_btn_hover": "#4e4e52",
    },
    "light": {
        "bg_primary": "#ffffff",
        "bg_sidebar": "#f3f3f3",
        "bg_input": "#ffffff",
        "bg_hover": "#e8e8e8",
        "bg_selected": "#e0e0e0",
        "bg_bubble_user": "#007acc",
        "bg_bubble_ai": "#f3f3f3",
        "bg_system_card": "#f9f9f9",
        "border": "#e5e5e5",
        "border_bubble_ai": "#e5e5e5",
        "text_primary": "#333333",
        "text_secondary": "#666666",
        "text_inverse": "#ffffff",
        "accent": "#007acc",
        "accent_hover": "#005a9e",
        "send_btn": "#007acc",
        "send_btn_hover": "#005a9e",
        "stop_btn": "#e5e5e5",
        "stop_btn_hover": "#d0d0d0",
    },
}

DEFAULT_THEME = "dark"


class InputTextEdit(QTextEdit):
    """多行输入框：Enter 发送，Shift+Enter 换行。"""
    send_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入消息，Enter 发送，Shift+Enter 换行...")
        self.setMaximumHeight(120)
        self.setMinimumHeight(44)
        self.setFont(QFont("Segoe UI", 13))

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.insertPlainText("\n")
            else:
                self.send_requested.emit()
            return
        super().keyPressEvent(event)


class SimpleChatArea(QWidget):
    """极简聊天区，为 UIRenderer 提供与旧 ChatView 兼容的接口。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._streaming_active = False
        self._streaming_buffer = ""
        self._streaming_start_pos = None
        self._theme = THEMES[DEFAULT_THEME]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部：会话标题 + 环境信息
        self.header = QLabel("")
        self.header.setStyleSheet(
            f"color: {self._theme['text_primary']}; font-size: 15px; font-weight: 600; padding: 16px 24px;"
        )
        layout.addWidget(self.header)

        self.sep = QLabel()
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet(f"background-color: {self._theme['border']};")
        layout.addWidget(self.sep)

        # 消息流
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 13))
        self.chat_area.setObjectName("chatArea")
        layout.addWidget(self.chat_area, 1)

        # 输入区
        input_panel = QWidget()
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(24, 12, 24, 16)
        input_layout.setSpacing(10)

        self.input_field = InputTextEdit()
        self.input_field.send_requested.connect(self._on_send)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedWidth(64)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedWidth(64)
        self.stop_btn.setVisible(False)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        input_layout.addWidget(self.stop_btn)

        layout.addWidget(input_panel)
        self._apply_theme_styles()

    def set_theme(self, theme_name: str):
        """切换主题并即时重绘样式。"""
        self._theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self._apply_theme_styles()
        self.header.setStyleSheet(
            f"color: {self._theme['text_primary']}; font-size: 15px; font-weight: 600; padding: 16px 24px;"
        )
        self.sep.setStyleSheet(f"background-color: {self._theme['border']};")

    def _apply_theme_styles(self):
        t = self._theme
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                line-height: 1.65;
            }}
        """)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['send_btn']}; color: {t['text_inverse']};
                border: 1px solid {t['send_btn']}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {t['send_btn_hover']}; }}
            QPushButton:disabled {{
                background-color: {t['border']}; color: {t['text_secondary']};
                border: 1px solid {t['border']};
            }}
        """)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['stop_btn']}; color: {t['text_primary']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {t['stop_btn_hover']}; }}
        """)
        self.chat_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['bg_primary']}; color: {t['text_primary']};
                border: none; font-size: 13px; line-height: 1.65;
            }}
        """)
        self.setStyleSheet(f"background-color: {t['bg_primary']};")

    # ── 兼容 UIRenderer 的接口 ──────────────────────────────────
    def _on_send(self):
        text = self.input_field.toPlainText().strip()
        if text and hasattr(self, '_send_callback'):
            self._send_callback(text)

    def set_send_callback(self, callback):
        self._send_callback = callback

    def set_stop_callback(self, callback):
        self.stop_btn.clicked.connect(callback)

    def clear_input(self):
        self.input_field.setPlainText("")

    def clear_chat(self):
        self.chat_area.clear()
        self._streaming_buffer = ""
        self._streaming_active = False
        self._streaming_start_pos = None

    def set_header(self, title: str, env: str = ""):
        if env:
            self.header.setText(f"{title}  ·  {env}")
        else:
            self.header.setText(title)

    def append_user(self, text: str):
        self._append_message("user", text)

    def append_ai(self, text: str):
        self._append_message("ai", text)

    def append_system(self, text: str):
        self._append_message("system", text)

    def _append_message(self, role: str, text: str):
        if role in ("user", "ai"):
            html_block = self._build_bubble(role, text)
        else:
            html_block = self._build_system_card(text)
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html_block)
        self.chat_area.moveCursor(QTextCursor.End)

    def append_chunk(self, chunk: str):
        if not chunk:
            return
        self._streaming_buffer += chunk
        cursor = self.chat_area.textCursor()
        if self._streaming_start_pos is not None:
            cursor.setPosition(self._streaming_start_pos)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        else:
            self._streaming_start_pos = cursor.position()
        html_block = self._build_bubble("ai", self._streaming_buffer)
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html_block)
        self.chat_area.moveCursor(QTextCursor.End)

    def finalize_stream(self):
        self._streaming_active = False
        self._streaming_start_pos = None
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    def set_streaming(self, active: bool):
        self._streaming_active = active
        self.stop_btn.setVisible(active)
        self.send_btn.setVisible(not active)
        if active:
            self._streaming_buffer = ""
            self._streaming_start_pos = None

    def set_send_enabled(self, enabled: bool):
        self.send_btn.setEnabled(enabled)

    # Phase UI：极简风格下不显示按钮，仅追加系统文本
    def set_phase_indicator(self, phase: str, task_count: int = 0):
        pass

    def set_task_progress(self, current: int, total: int):
        pass

    def show_confirmation(self, task_list: list):
        if task_list:
            lines = ["### 任务清单", ""]
            for idx, task in enumerate(task_list[:7], 1):
                desc = task.description if hasattr(task, "description") else str(task)
                lines.append(f"{idx}. {desc}")
            self.append_system("\n".join(lines))

    def hide_confirmation(self):
        pass

    def show_skip_verify(self):
        pass

    def hide_skip_verify(self):
        pass

    def clear_phase_ui(self):
        pass

    def append_phase_message(self, phase: str, text: str):
        self.append_system(text)

    # ── HTML 构建 ──────────────────────────────────
    def _build_system_card(self, text: str) -> str:
        t = self._theme
        html_content = _md_to_html(text)
        return f"""
        <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:10px 0;">
            <tr><td align="center" style="padding:0 64px;">
                <div style="display:inline-block;max-width:80%;min-width:280px;
                            background-color:{t['bg_system_card']};border:1px solid {t['border']};
                            border-radius:12px;padding:14px 18px;text-align:left;">
                    <div style="color:{t['text_primary']};font-family:'Segoe UI','Microsoft YaHei',sans-serif;
                                font-size:13px;line-height:1.7;">
                        {html_content}
                    </div>
                </div>
            </td></tr>
        </table>
        <div style="clear:both;"></div>
        """

    def _build_bubble(self, role: str, text: str) -> str:
        t = self._theme
        if role == "user":
            avatar = self._avatar_cell("我", "right", t["accent"])
            bubble_bg = t["bg_bubble_user"]
            bubble_border = t["bg_bubble_user"]
            text_color = t["text_inverse"]
            row = f"""
            <td align="right" valign="top" style="padding:2px 8px 10px 64px;">
                {self._md_content(text, bubble_bg, bubble_border, text_color)}
            </td>
            {avatar}
            """
        else:
            avatar = self._avatar_cell("AI", "left", "#6366F1")
            bubble_bg = t["bg_bubble_ai"]
            bubble_border = t["border_bubble_ai"]
            text_color = t["text_primary"]
            row = f"""
            {avatar}
            <td align="left" valign="top" style="padding:2px 64px 10px 8px;">
                {self._md_content(text, bubble_bg, bubble_border, text_color)}
            </td>
            """

        return f"""
        <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:10px 0;">
            <tr>{row}</tr>
        </table>
        <div style="clear:both;"></div>
        """

    @staticmethod
    def _avatar_cell(label: str, align: str, bg: str) -> str:
        return f"""
        <td valign="top" width="36" style="padding:4px 8px;text-align:{align};">
            <div style="width:32px;height:32px;line-height:32px;text-align:center;
                        background-color:{bg};color:#FFFFFF;border-radius:50%;
                        font-size:12px;font-weight:bold;overflow:hidden;">
                {label}
            </div>
        </td>
        """

    @staticmethod
    def _md_content(text: str, bubble_bg: str, bubble_border: str, text_color: str) -> str:
        html_content = _md_to_html(text)
        return f"""
        <div style="display:inline-block;max-width:85%;color:{text_color};
                    background-color:{bubble_bg};border:1px solid {bubble_border};
                    border-radius:14px;padding:10px 14px;
                    font-family:'Segoe UI','Microsoft YaHei',sans-serif;
                    font-size:13px;line-height:1.65;text-align:left;">
            {html_content}
        </div>
        """


class MainWindow(QMainWindow):
    def __init__(self, worker_mgr=None):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle("Agent")

        # 1. 初始化配置与主题
        self._config = ConfigService(config_path="config.yaml")
        self._theme_name = self._config.get("app.theme", DEFAULT_THEME)
        if self._theme_name not in THEMES:
            self._theme_name = DEFAULT_THEME

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
            parent=self,
        )

        self._apply_theme()
        self._setup_ui()

        self._ui_renderer = UIRenderer(
            message_bus=self._bus,
            chat_view=self.chat_area,
            conversation_list=self.conversation_list,
            current_session_provider=lambda: self._orchestrator.current_session_id or "",
            parent=self,
        )

        # 草稿窗口状态（未写入 DB 的初始化窗口）
        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._current_model_name = self._config.get("app.last_model", "tool-agent")

        self._connect_signals()
        self._init_default_session()

    def _get_project_path(self) -> str:
        """获取当前项目路径（当前可返回空字符串）。"""
        return ""

    def _setup_ui(self):
        """Solo 两栏布局：左 280px + 右填充。"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左栏
        self.conversation_list = ConversationListWidget(theme=self._theme_name)
        self.conversation_list.new_task_clicked.connect(self._on_new_task)
        self.conversation_list.conversation_selected.connect(self._on_conversation_selected)
        self.conversation_list.conversation_deleted.connect(self._on_conversation_deleted)
        self.conversation_list.conversation_pinned.connect(self._on_conversation_pinned)
        self.conversation_list.model_changed.connect(self._on_model_changed)
        self.conversation_list.theme_changed.connect(self._on_theme_changed)
        main_layout.addWidget(self.conversation_list)

        # 右栏
        self.chat_area = SimpleChatArea()
        self.chat_area.set_theme(self._theme_name)
        self.chat_area.set_send_callback(self._on_send_message)
        self.chat_area.set_stop_callback(self._on_stop_generation)
        main_layout.addWidget(self.chat_area, 1)

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
        registry = LLMRegistry("config.yaml", "config.yaml")
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
                app_root="F:/Agent/agent_workbench",
                config=config.get("self_context", {}), policy_engine=policy,
            ),
        }
        return engines

    def _connect_signals(self):
        pass

    def _init_default_session(self):
        """启动时不自动创建 DB 会话，直接进入草稿窗口状态。"""
        self._reset_to_draft()
        self.chat_area.set_header("Agent", "准备就绪")
        self._populate_model_selector()

    def _populate_model_selector(self):
        """从 config 读取模型列表并填充下拉框。"""
        providers = self._config.get("llm_providers", {})
        self.conversation_list.populate_models(providers, self._current_model_name)

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
        QTimer.singleShot(0, self.chat_area.input_field.setFocus)

    def _on_conversation_selected(self, session_id: str):
        self._bus.emit(SessionSwitchEvent(new_session_id=session_id))

    def _on_conversation_deleted(self, session_id: str):
        self._bus.emit(SessionDeleteEvent(session_id=session_id))

    def _on_conversation_pinned(self, session_id: str, pinned: bool):
        self._bus.emit(SessionPinEvent(session_id=session_id, pinned=pinned))

    def _on_theme_changed(self, theme_name: str):
        """用户切换主题：应用新主题并持久化到 config.yaml。"""
        if theme_name not in THEMES or theme_name == self._theme_name:
            return
        self._theme_name = theme_name
        self._apply_theme()
        self.conversation_list.set_theme(theme_name)
        self.chat_area.set_theme(theme_name)
        self._config.set("app.theme", theme_name)
        self._config.save()

    def _on_send_message(self, user_text: str):
        """发送消息：草稿窗口首条消息会触发 orchestrator 创建会话。"""
        self.chat_area.clear_input()
        self._bus.emit(UserSendEvent(
            session_id="",
            user_text=user_text,
            mode="ask",
            session_type=self._draft_session_type,
            project_path=self._draft_project_path,
            model=self._current_model_name,
        ))

    def _on_stop_generation(self):
        current_sid = self._orchestrator.current_session_id
        if current_sid:
            self._bus.emit(UserStopEvent(session_id=current_sid))

    def _on_model_changed(self, model_name: str):
        """用户切换模型：更新当前模型并持久化到 config.yaml。"""
        if not model_name or model_name == self._current_model_name:
            return
        self._current_model_name = model_name
        self._config.set("app.last_model", model_name)
        self._config.save()
