"""
ChatView — 底部控件栏版：模式切换/模型选择贴底，Enter 发送 / Shift+Enter 换行
"""
import html

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QButtonGroup, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QTextCursor, QKeySequence, QShortcut

from markdown import markdown as md


def md_to_html(text: str) -> str:
    # 先转义原始文本防止被当作 HTML 标签，markdown 生成后还原实体，
    # 避免 &quot; / &#x27; 等字面量直接显示在气泡中。
    raw_html = md(html.escape(text), extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'])
    return html.unescape(raw_html)


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
    log_panel_toggled = Signal(bool)
    confirm_clicked = Signal()      # 用户确认 task list
    reanalyze_clicked = Signal()    # 用户要求重新分析
    skip_verify_clicked = Signal()  # 用户跳过验证

    def __init__(self, parent=None):
        super().__init__(parent)
        self._streaming_active = False
        self._streaming_buffer = ""
        self._has_received_chunks = False
        self._phase_indicator = None
        self._confirm_btn = None
        self._reanalyze_btn = None
        self._skip_verify_btn = None
        self._task_progress_label = None
        self._confirm_active = False
        self._setup_ui()
        self._setup_shortcuts()
        self.installEventFilter(self)

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

        # 日志面板开关
        self.log_btn = QPushButton("日志")
        self.log_btn.setCheckable(True)
        self.log_btn.setChecked(True)
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 11px;
            }
            QPushButton:checked {
                background-color: #388BFD26; border: 1px solid #58A6FF; color: #58A6FF;
            }
            QPushButton:hover { background-color: #30363D; }
        """)
        self.log_btn.clicked.connect(self._on_log_btn_clicked)
        bar.addWidget(self.log_btn)

        bar.addSpacing(12)

        # Phase 指示器
        self._phase_indicator = QLabel("")
        self._phase_indicator.setStyleSheet(
            "color: #8B949E; font-size: 11px; font-weight: 600; padding: 2px 8px;"
        )
        bar.addWidget(self._phase_indicator)

        # 任务进度
        self._task_progress_label = QLabel("")
        self._task_progress_label.setStyleSheet(
            "color: #58A6FF; font-size: 11px; padding: 2px 8px;"
        )
        bar.addWidget(self._task_progress_label)

        # 确认 / 重新分析 / 跳过验证（默认隐藏）
        self._confirm_btn = QPushButton("\u786e\u8ba4\u6267\u884c")
        self._confirm_btn.setObjectName("confirmBtn")
        self._confirm_btn.setVisible(False)
        self._confirm_btn.setCursor(Qt.PointingHandCursor)
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: #FFFFFF; border: 1px solid #238636;
                padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 11px;
            }
            QPushButton:hover { background-color: #2EA043; }
        """)
        self._confirm_btn.clicked.connect(self.confirm_clicked.emit)
        bar.addWidget(self._confirm_btn)

        self._reanalyze_btn = QPushButton("\u91cd\u65b0\u5206\u6790")
        self._reanalyze_btn.setObjectName("reanalyzeBtn")
        self._reanalyze_btn.setVisible(False)
        self._reanalyze_btn.setCursor(Qt.PointingHandCursor)
        self._reanalyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 11px;
            }
            QPushButton:hover { background-color: #30363D; }
        """)
        self._reanalyze_btn.clicked.connect(self.reanalyze_clicked.emit)
        bar.addWidget(self._reanalyze_btn)

        self._skip_verify_btn = QPushButton("\u8df3\u8fc7\u9a8c\u8bc1")
        self._skip_verify_btn.setObjectName("skipVerifyBtn")
        self._skip_verify_btn.setVisible(False)
        self._skip_verify_btn.setCursor(Qt.PointingHandCursor)
        self._skip_verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #8B949E; border: 1px solid #30363D;
                padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 11px;
            }
            QPushButton:hover { background-color: #30363D; color: #E6EDF3; }
        """)
        self._skip_verify_btn.clicked.connect(self.skip_verify_clicked.emit)
        bar.addWidget(self._skip_verify_btn)

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

    def _on_log_btn_clicked(self, checked):
        self.log_panel_toggled.emit(checked)

    def set_log_panel_checked(self, checked: bool):
        self.log_btn.setChecked(checked)

    def _on_stop(self):
        self.stop_requested.emit()
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    def set_streaming(self, active: bool):
        self._streaming_active = active
        self._has_received_chunks = False
        self.stop_btn.setVisible(active)
        self.send_btn.setVisible(not active)
        if active:
            self._streaming_buffer = ""

    def append_chunk(self, chunk: str):
        if not chunk:
            return
        self._has_received_chunks = True
        self._streaming_buffer += chunk
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        if hasattr(self, '_streaming_start_pos'):
            cursor.setPosition(self._streaming_start_pos)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        else:
            self._streaming_start_pos = cursor.position()
        html = self._build_bubble("ai", self._streaming_buffer)
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html)
        self.chat_area.moveCursor(QTextCursor.End)

    def finalize_stream(self):
        self._streaming_active = False
        if hasattr(self, '_streaming_start_pos'):
            del self._streaming_start_pos
        self.stop_btn.setVisible(False)
        self.send_btn.setVisible(True)

    def has_received_chunks(self) -> bool:
        return self._has_received_chunks

    def append_user(self, text):
        self._append_message("user", text)

    def append_ai(self, text):
        self._append_message("ai", text)

    def append_ai_metrics_footer(self, text: str):
        """在最后一个 AI 气泡左下角追加 metrics 小字（如 33546tok/34ms）"""
        if not text:
            return
        html_block = (
            f"<div style='color:#8B949E;font-size:10px;text-align:left;"
            f"margin:2px 8px 10px 48px;font-family:\"Segoe UI\",\"Microsoft YaHei\",sans-serif;'>"
            f"{html.escape(text)}"
            f"</div>"
        )
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html_block)
        self.chat_area.moveCursor(QTextCursor.End)

    def append_system(self, text):
        self._append_message("system", text)

    def _append_message(self, role, text):
        if role in ("user", "ai"):
            html_block = self._build_bubble(role, text)
        else:
            html_block = f"<div style='color:#8B949E;font-size:12px;text-align:center;margin:6px 0;'>{html.escape(text)}</div>"
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html_block)
        self.chat_area.moveCursor(QTextCursor.End)

    def _avatar_cell(self, label: str, align: str) -> str:
        bg = "#10B981" if label == "我" else "#6366F1"
        return f"""
        <td valign="top" width="36" style="padding:4px 8px;text-align:{align};">
            <div style="width:32px;height:32px;line-height:32px;text-align:center;
                        background-color:{bg};color:#FFFFFF;border-radius:50%;
                        font-size:12px;font-weight:bold;overflow:hidden;">
                {label}
            </div>
        </td>
        """

    def _build_bubble(self, role: str, text: str) -> str:
        """简约风格：头像在左/右，内容无背景色，居左/居右对齐。"""
        if role == "user":
            avatar = self._avatar_cell("我", "right")
            content_align = "right"
            row = f"""
            <td align="right" valign="top" style="padding:2px 8px 8px 48px;">
                {self._md_content(text, align="right")}
            </td>
            {avatar}
            """
        else:
            avatar = self._avatar_cell("AI", "left")
            content_align = "left"
            row = f"""
            {avatar}
            <td align="left" valign="top" style="padding:2px 48px 8px 8px;">
                {self._md_content(text, align="left")}
            </td>
            """

        return f"""
        <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:12px 0;">
            <tr>
                {row}
            </tr>
        </table>
        <div style="clear:both;"></div>
        """

    def _md_content(self, text: str, align: str = "left") -> str:
        html_content = md_to_html(text)
        return f"""
        <div style="display:inline-block;color:#E6EDF3;
                    font-family:'Segoe UI','Microsoft YaHei',sans-serif;
                    font-size:13px;line-height:1.6;text-align:{align};">
            {html_content}
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

    # ═══════════════════════════════════════════════════
    # Phase UI 控制
    # ═══════════════════════════════════════════════════
    def set_phase_indicator(self, phase: str, task_count: int = 0, current: int = 0):
        """设置底部阶段指示器文本"""
        labels = {
            "analyze": "[分析中]",
            "confirm": "[等待确认]",
            "execute": f"[执行中 {current}/{task_count}]" if task_count else "[执行中]",
            "verify": "[验证中]",
            "archive": "[存档中]",
            "idle": "",
        }
        text = labels.get((phase or "").lower(), f"[{phase}]")
        self._phase_indicator.setText(text)

    def set_task_progress(self, current: int, total: int):
        """设置任务进度文本"""
        if total <= 0:
            self._task_progress_label.setText("")
        else:
            self._task_progress_label.setText(f"任务 {current}/{total}")

    def show_confirmation(self, task_list: list):
        """在对话区显示内联确认卡片，并激活 Enter/Esc 快捷键"""
        self._confirm_btn.setVisible(True)
        self._reanalyze_btn.setVisible(True)
        self._skip_verify_btn.setVisible(False)
        self.set_confirm_active(True)
        # 在对话区显示任务清单等待确认
        if task_list:
            lines = ["### ✅ 任务清单已生成，请确认是否执行"]
            display_tasks = list(task_list)[:7]
            hidden_count = len(task_list) - len(display_tasks)
            for idx, task in enumerate(display_tasks, 1):
                desc = task.description if hasattr(task, "description") else str(task)
                lines.append(f"{idx}. {desc}")
            if hidden_count > 0:
                lines.append(f"\n*... 还有 {hidden_count} 个任务已折叠 ...*")
            lines.append("\n💡 **操作方式**：")
            lines.append("- 按 **Enter** 或点击「确认执行」立即执行")
            lines.append("- 按 **Esc** 或点击「重新分析」调整需求")
            self.append_system("\n".join(lines))

    def hide_confirmation(self):
        """隐藏确认相关按钮，关闭 Enter/Esc 快捷键"""
        self._confirm_btn.setVisible(False)
        self._reanalyze_btn.setVisible(False)
        self.set_confirm_active(False)

    def show_skip_verify(self):
        """验证阶段显示跳过按钮"""
        self._skip_verify_btn.setVisible(True)

    def hide_skip_verify(self):
        self._skip_verify_btn.setVisible(False)

    def clear_phase_ui(self):
        """清空 phase 相关 UI 状态"""
        self.set_phase_indicator("idle")
        self.set_task_progress(0, 0)
        self.hide_confirmation()
        self.hide_skip_verify()

    def eventFilter(self, obj, event):
        """Confirm 阶段监听 Enter/Esc 快捷键"""
        if event.type() == QEvent.KeyPress and self._confirm_active:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self.confirm_clicked.emit()
                return True
            if key == Qt.Key_Escape:
                self.reanalyze_clicked.emit()
                return True
        return super().eventFilter(obj, event)

    def set_confirm_active(self, active: bool):
        """设置是否处于 Confirm 阶段，控制 Enter/Esc 快捷键"""
        self._confirm_active = active
        if active and self._confirm_btn:
            self._confirm_btn.setDefault(True)
            self._confirm_btn.setFocus()

    def append_phase_message(self, phase: str, text: str):
        """按 phase 追加系统消息，带阶段前缀"""
        prefix = {
            "analyze": "🔍 ",
            "confirm": "⏸ ",
            "execute": "⚙️ ",
            "verify": "✅ ",
            "archive": "📦 ",
        }.get((phase or "").lower(), "")
        self.append_system(f"{prefix}{text}")

    def clear(self):
        self.chat_area.clear()
        self.clear_phase_ui()
