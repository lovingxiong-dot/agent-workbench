"""
ChatView — 底部控件栏版：模式切换/模型选择贴底，Enter 发送 / Shift+Enter 换行
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QButtonGroup, QComboBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QKeySequence, QShortcut

from markdown import markdown as md


def md_to_html(text: str) -> str:
    return md(text, extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'])


class InputTextEdit(QTextEdit):
    """自定义输入框：Enter 发送，Shift+Enter 换行"""
    send_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入指令，Enter 发送，Shift+Enter 换行...")
        self.setMaximumHeight(120)
        self.setMinimumHeight(36)
        self.setFont(QFont("Segoe UI", 12))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.insertPlainText("\n")
            else:
                self.send_requested.emit()
            return
        super().keyPressEvent(event)


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

        # ── 对话区 (占满空间) ────────────────────
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 12))
        self.chat_area.setObjectName("chatArea")
        layout.addWidget(self.chat_area, 1)  # stretch=1 占满

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #30363D;")
        layout.addWidget(sep)

        # ── 底部控�条 (模式 | 模型 | 发送) ──────
        bar = QHBoxLayout()
        bar.setContentsMargins(10, 6, 10, 6)
        bar.setSpacing(8)

        # 左侧：模式切换
        self.mode_indicator = QLabel("\u25cf")
        self.mode_indicator.setStyleSheet("color: #3FB950; font-size: 10px;")
        bar.addWidget(self.mode_indicator)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.btn_ask = self._make_mode_btn("Ask", "ask")
        self.btn_plan = self._make_mode_btn("Plan", "plan")
        self.btn_craft = self._make_mode_btn("Craft", "craft")
        bar.addWidget(self.btn_ask)
        bar.addWidget(self.btn_plan)
        bar.addWidget(self.btn_craft)
        self.btn_ask.setChecked(True)

        bar.addSpacing(12)

        # 中部：模型选择 + 齿轮
        self.model_selector = QComboBox()
        self.model_selector.setFixedWidth(180)
        self.model_selector.setToolTip("\u9009\u62e9\u5f53\u524d\u4f7f\u7528\u7684\u6a21\u578b")
        self.model_selector.setStyleSheet("""
            QComboBox {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                border-radius: 8px; padding: 4px 8px; font-size: 11px;
            }
            QComboBox:hover { border: 1px solid #58A6FF; }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow {
                image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-top: 5px solid #8B949E;
                margin-right: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #161B22; color: #E6EDF3; border: 1px solid #30363D;
                selection-background-color: #1F6FEB33; selection-color: #58A6FF;
                outline: none;
            }
        """)
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        bar.addWidget(self.model_selector)

        self.settings_btn = QPushButton("\u2699")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("\u6a21\u578b\u8bbe\u7f6e")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #8B949E; border: none;
                border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #21262D; color: #E6EDF3; }
        """)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        bar.addWidget(self.settings_btn)

        bar.addStretch()

        # 右侧：停止 / 发送
        self.stop_btn = QPushButton("\u23f9 \u505c\u6b62")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedWidth(72)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop)
        bar.addWidget(self.stop_btn)

        self.send_btn = QPushButton("\u53d1\u9001")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedWidth(72)
        self.send_btn.clicked.connect(self._send)
        bar.addWidget(self.send_btn)

        layout.addLayout(bar)

        # ── 多行输入区 ──────────────────────────
        self.input_field = InputTextEdit()
        self.input_field.send_requested.connect(self._send)
        self.input_field.setObjectName("chatArea")
        layout.addWidget(self.input_field)

    def _make_mode_btn(self, text, name):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("mode", name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 11px;
            }
            QPushButton:checked {
                background-color: #388BFD26; border: 1px solid #58A6FF; color: #58A6FF;
            }
            QPushButton:hover { background-color: #30363D; }
        """)
        self.mode_group.addButton(btn)
        btn.clicked.connect(lambda checked, n=name: self.mode_clicked.emit(n))
        return btn

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.clear)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_stop)

    def _send(self):
        text = self.input_field.toPlainText().strip()
        if text:
            self.input_field.clear()
            self.send_clicked.emit(text)

    def _on_stop(self):
        self.stop_requested.emit()
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    def set_streaming(self, active: bool):
        self._streaming_active = active
        self.stop_btn.setVisible(active)
        self.send_btn.setVisible(not active)
        if active:
            self._streaming_buffer = ""

    def append_chunk(self, chunk: str):
        self._streaming_buffer += chunk
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
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
        self._streaming_active = False
        if hasattr(self, '_streaming_start_pos'):
            del self._streaming_start_pos
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

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
        return f"""
        <div style='{margin}{align_style}'>
            <div style='display:inline-block;background:{bg};color:{color};padding:10px 14px;
                        border-radius:12px;max-width:85%;
                        font-family:"Segoe UI","Microsoft YaHei",sans-serif;
                        font-size:13px;line-height:1.6;text-align:left;'>
                {html_content}
            </div>
        </div>
        """

    def set_header(self, mode, model, session):
        idx = self.model_selector.findData(model)
        if idx >= 0:
            self.model_selector.blockSignals(True)
            self.model_selector.setCurrentIndex(idx)
            self.model_selector.blockSignals(False)

    def set_mode(self, mode_name):
        self.btn_ask.setChecked(mode_name == "ask")
        self.btn_plan.setChecked(mode_name == "plan")
        self.btn_craft.setChecked(mode_name == "craft")
        colors = {"ask": "#3FB950", "plan": "#D29922", "craft": "#F85149"}
        self.mode_indicator.setStyleSheet(f"color: {colors.get(mode_name, '#58A6FF')}; font-size: 10px;")

    def populate_models(self, providers: dict, current: str):
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        for name, cfg in providers.items():
            self.model_selector.addItem(f"{name}  ({cfg.get('model', '?')})", name)
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
