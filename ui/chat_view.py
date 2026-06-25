"""
聊天视图 — 增强版：支持流式输出、停止生成、快捷键
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFrame, QButtonGroup, QComboBox, QScrollBar,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QKeySequence, QShortcut


# Markdown 渲染工具
from markdown import markdown as md


def md_to_html(text: str) -> str:
    """Markdown → HTML"""
    html = md(text, extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'])
    return html


class ChatView(QWidget):
    send_clicked = Signal(str)
    mode_clicked = Signal(str)
    model_changed = Signal(str)
    settings_clicked = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._streaming_active = False
        self._streaming_buffer = ""
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部工具栏 ──────────────────────────
        self.toolbar = QHBoxLayout()
        self.toolbar.setContentsMargins(12, 8, 12, 8)
        self.toolbar.setSpacing(10)

        self.mode_indicator = QLabel("●")
        self.mode_indicator.setStyleSheet("color: #3FB950; font-size: 12px;")
        self.mode_label = QLabel("Ask")
        self.mode_label.setObjectName("modeLabel")

        self.session_label = QLabel("默认会话")
        self.session_label.setObjectName("sessionLabel")

        self.toolbar.addWidget(self.mode_indicator)
        self.toolbar.addWidget(self.mode_label)
        self.toolbar.addSpacing(8)

        # 模式切换按钮组
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.btn_ask = self._create_mode_btn("Ask", "ask")
        self.btn_plan = self._create_mode_btn("Plan", "plan")
        self.btn_act = self._create_mode_btn("Act", "act")
        for btn, name in [(self.btn_ask, "ask"), (self.btn_plan, "plan"), (self.btn_act, "act")]:
            btn.clicked.connect(lambda checked, n=name: self.mode_clicked.emit(n))
        self.btn_ask.setChecked(True)

        self.toolbar.addStretch()

        # 模型下拉选择器
        self.model_selector = QComboBox()
        self.model_selector.setFixedWidth(200)
        self.model_selector.setToolTip("选择当前使用的模型")
        self.model_selector.setStyleSheet("""
            QComboBox {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                border-radius: 8px; padding: 5px 10px; font-size: 12px;
            }
            QComboBox:hover { border: 1px solid #58A6FF; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #8B949E; margin-right: 4px; }
            QComboBox QAbstractItemView {
                background-color: #161B22; color: #E6EDF3; border: 1px solid #30363D;
                selection-background-color: #1F6FEB33; selection-color: #58A6FF;
                outline: none;
            }
        """)
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        self.toolbar.addWidget(self.model_selector)

        # 设置齿轮按钮
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip("模型设置")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #8B949E; border: none;
                border-radius: 6px; font-size: 16px;
            }
            QPushButton:hover { background-color: #21262D; color: #E6EDF3; }
        """)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        self.toolbar.addWidget(self.settings_btn)
        self.toolbar.addWidget(self.session_label)
        layout.addLayout(self.toolbar)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("toolbarSeparator")
        layout.addWidget(sep)

        # ── 聊天显示区 ──────────────────────────
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 12))
        self.chat_area.setObjectName("chatArea")
        layout.addWidget(self.chat_area)

        # ── 输入区 ──────────────────────────────
        input_widget = QWidget()
        input_widget.setObjectName("inputWidget")
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入指令，Ctrl+Enter 发送...")
        self.input_field.setMinimumHeight(36)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.stop_btn)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_widget)

    def _create_mode_btn(self, text, name):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("mode", name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                padding: 5px 16px; border-radius: 8px; font-weight: 600; font-size: 12px;
            }
            QPushButton:checked {
                background-color: #388BFD26; border: 1px solid #58A6FF; color: #58A6FF;
            }
            QPushButton:hover { background-color: #30363D; }
        """)
        self.mode_group.addButton(btn)
        self.toolbar.addWidget(btn)
        return btn

    def _setup_shortcuts(self):
        """键盘快捷键"""
        # Ctrl+Enter 发送
        self.send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.send_shortcut.activated.connect(self._send)
        # Ctrl+L 清空
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.clear_shortcut.activated.connect(self.clear)
        # Escape 停止
        self.stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.stop_shortcut.activated.connect(self._on_stop)

    def _send(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.send_clicked.emit(text)

    def _on_stop(self):
        self.stop_requested.emit()
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    def set_streaming(self, active: bool):
        """切换流式状态"""
        self._streaming_active = active
        self.stop_btn.setVisible(active)
        self.send_btn.setVisible(not active)
        if active:
            self._streaming_buffer = ""

    def append_chunk(self, chunk: str):
        """流式追加文本块"""
        self._streaming_buffer += chunk
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        # Replace the last streaming bubble with updated content
        if hasattr(self, '_streaming_start_pos'):
            cursor.setPosition(self._streaming_start_pos)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        else:
            self._streaming_start_pos = cursor.position()
        html = self._build_bubble("left", "#21262D", "#E6EDF3", self._streaming_buffer)
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html)
        self.chat_area.moveCursor(QTextCursor.End)

    def finalize_stream(self):
        """流式完成，清理状态"""
        self._streaming_active = False
        if hasattr(self, '_streaming_start_pos'):
            del self._streaming_start_pos
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    # ── 消息附加 ──────────────────────────────────
    def append_user(self, text):
        self._append_message("user", text)

    def append_ai(self, text):
        self._append_message("ai", text)

    def append_system(self, text):
        self._append_message("system", text)

    def _append_message(self, role, text):
        if role == "user":
            html = self._build_bubble("right", "#1F6FEB", "#FFFFFF", text)
        elif role == "ai":
            html = self._build_bubble("left", "#21262D", "#E6EDF3", text)
        else:
            html = f"<div style='color:#8B949E;font-size:12px;text-align:center;margin:6px 0;'>{text}</div>"

        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html)
        self.chat_area.moveCursor(QTextCursor.End)

    def _build_bubble(self, align, bg, color, text):
        if align == "right":
            margin = "margin: 6px 16px 6px 80px;"
            align_style = "text-align: right;"
        else:
            margin = "margin: 6px 80px 6px 16px;"
            align_style = "text-align: left;"

        html_content = md_to_html(text)
        bubble = f"""
        <div style='{margin}{align_style}'>
            <div style='display:inline-block;background:{bg};color:{color};padding:10px 14px;border-radius:12px;
                        max-width:85%;font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:13px;line-height:1.6;text-align:left;'>
                {html_content}
            </div>
        </div>
        """
        return bubble

    # ── 标题与模式 ───────────────────────────────
    def set_header(self, mode, model, session):
        self.mode_label.setText(mode.capitalize())
        self.session_label.setText(session)
        idx = self.model_selector.findData(model)
        if idx >= 0:
            self.model_selector.blockSignals(True)
            self.model_selector.setCurrentIndex(idx)
            self.model_selector.blockSignals(False)

    def set_mode(self, mode_name):
        self.btn_ask.setChecked(mode_name == "ask")
        self.btn_plan.setChecked(mode_name == "plan")
        self.btn_act.setChecked(mode_name == "act")
        self.mode_label.setText(mode_name.capitalize())
        # Mode indicator color
        colors = {"ask": "#3FB950", "plan": "#D29922", "act": "#F85149"}
        self.mode_indicator.setStyleSheet(f"color: {colors.get(mode_name, '#58A6FF')}; font-size: 12px;")

    def populate_models(self, providers: dict, current: str):
        """刷新模型下拉列表"""
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        for name, cfg in providers.items():
            display = f"{name}  ({cfg.get('model', '?')})"
            self.model_selector.addItem(display, name)
        idx = self.model_selector.findData(current)
        if idx >= 0:
            self.model_selector.setCurrentIndex(idx)
        self.model_selector.blockSignals(False)

    def _on_model_changed(self, text):
        name = self.model_selector.currentData()
        if name:
            self.model_changed.emit(name)

    def clear(self):
        self.chat_area.clear()
