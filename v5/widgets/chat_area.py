"""V5 聊天区域组件。"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QGraphicsView, QFrame, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize, QEvent, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap
from .base import theme, V5_THEMES, C, font, qcolor, svg_icon
from .chat_scene import ChatScene
from .chat_items import (
    ChatItem, UserBubble, FoldBlock, ToolEntry, PhasePanel,
    BulletItem, StepItem, TextItem, SystemCard, _strip_html,
)

# ══════════════════════════════════════════════════════════════
# MoreDropdown — "..." 按钮下拉面板（进度 + 文件）
# ══════════════════════════════════════════════════════════════
class MoreDropdown(QWidget):
    WIDTH = 260
    CORNER = 8
    export_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(self.WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 进度区
        prog_hdr = QLabel("📊 进度")
        prog_hdr.setFont(font(11, bold=True))
        prog_hdr.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        layout.addWidget(prog_hdr)

        # 步骤列表（当前无真实任务进度，显示空状态）
        self._steps_layout = QVBoxLayout()
        self._steps_layout.setSpacing(4)
        empty_lbl = QLabel("暂无任务进度")
        empty_lbl.setFont(font(9))
        empty_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._steps_layout.addWidget(empty_lbl)
        layout.addLayout(self._steps_layout)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"color: {C['border']};")
        layout.addWidget(sep)

        # 文件区
        file_hdr = QLabel("📁 文件")
        file_hdr.setFont(font(11, bold=True))
        file_hdr.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        layout.addWidget(file_hdr)

        empty_file_lbl = QLabel("暂无文件")
        empty_file_lbl.setFont(font(9))
        empty_file_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        layout.addWidget(empty_file_lbl)

        # 分隔线
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"color: {C['border']};")
        layout.addWidget(sep2)

        # 导出会话入口
        export_lbl = QLabel("⬇ 导出会话")
        export_lbl.setFont(font(10))
        export_lbl.setCursor(Qt.PointingHandCursor)
        export_lbl.setStyleSheet(f"color: {C['accent']}; background: transparent;")
        export_lbl.mousePressEvent = lambda e: self.export_requested.emit()
        layout.addWidget(export_lbl)

        # 设置入口
        settings_lbl = QLabel("⚙ 设置")
        settings_lbl.setFont(font(10))
        settings_lbl.setCursor(Qt.PointingHandCursor)
        settings_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        settings_lbl.mousePressEvent = lambda e: self.settings_requested.emit()
        layout.addWidget(settings_lbl)

        self.setFixedHeight(306)
        self.setFocusPolicy(Qt.StrongFocus)
        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def position_under(self, btn: QWidget):
        """将下拉面板定位到给定按钮正下方、右对齐（在父控件内）。"""
        parent = self.parentWidget()
        if not parent:
            return
        # 按钮在父控件中的位置
        btn_pos = btn.mapTo(parent, QPoint(0, btn.height()))
        x = btn_pos.x() - self.WIDTH + btn.width()
        y = btn_pos.y()
        self.move(max(0, x), y)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(0, 0, 0, 40))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), self.CORNER, self.CORNER)
        p.setBrush(QColor(C["bg_card"]))
        p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), self.CORNER - 1, self.CORNER - 1)
        p.setPen(QPen(QColor(C["border"]), 0.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1.5, 1.5, self.width() - 3, self.height() - 3), self.CORNER, self.CORNER)
        p.end()


# ══════════════════════════════════════════════════════════════
# 标题栏
# ══════════════════════════════════════════════════════════════

class HeaderBar(QWidget):
    expand_toggled = Signal()
    search_clicked = Signal()
    more_clicked = Signal()
    double_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 双行标题（SVG: title y=16, env y=30）
        title_block = QVBoxLayout()
        title_block.setContentsMargins(12, 4, 0, 4)
        title_block.setSpacing(2)

        self._title_lbl = QLabel("新会话")
        self._title_lbl.setFont(font(12))
        title_block.addWidget(self._title_lbl)

        self._env_lbl = QLabel("")
        self._env_lbl.setFont(font(10))
        self._env_lbl.hide()
        title_block.addWidget(self._env_lbl)

        self._status_lbl = QLabel()
        self._status_lbl.setFont(font(9))
        self._status_lbl.hide()
        title_block.addWidget(self._status_lbl)
        layout.addLayout(title_block, 1)

        # 垂直分隔线（SVG: x1=553, h=24）
        self._vsep = QLabel()
        self._vsep.setFixedSize(1, 24)
        layout.addWidget(self._vsep)
        layout.addSpacing(6)

        self._btn_block = QWidget()
        btn_hl = QHBoxLayout(self._btn_block)
        btn_hl.setContentsMargins(0, 0, 0, 0)
        btn_hl.setSpacing(4)

        self._search_btn = self._icon_btn("搜索 (Ctrl+F)")
        self._search_btn.clicked.connect(self.search_clicked.emit)
        self._more_btn = self._icon_btn("更多操作")
        self._more_btn.clicked.connect(self.more_clicked.emit)
        self._expand_btn = self._icon_btn("展开/收起面板 (Ctrl+B)")
        self._expand_btn.clicked.connect(self.expand_toggled.emit)

        btn_hl.addWidget(self._search_btn)
        btn_hl.addWidget(self._more_btn)
        btn_hl.addWidget(self._expand_btn)
        layout.addWidget(self._btn_block)

        layout.addSpacing(12)
        self._refresh_theme()

    def _icon_btn(self, tooltip: str) -> QPushButton:
        """18×22 图标按钮：规范背景三态 + 圆角 4px。"""
        btn = QPushButton()
        btn.setFixedSize(18, 22)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['header_btn_bg']}; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {C['header_btn_hover']}; }}"
            f"QPushButton:pressed {{ background-color: {C['header_btn_active']}; }}"
        )
        lbl = QLabel(btn)
        lbl.setObjectName("icon_lbl")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setGeometry(0, 0, 18, 22)
        return btn

    def set_expanded_state(self, expanded: bool):
        self._expanded = expanded
        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._env_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._status_lbl.setStyleSheet(f"color: {C['accent_blue']}; background: transparent;")
        self._vsep.setStyleSheet(f"background-color: {C['border']};")

        stroke = C['header_icon']
        search_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="22" viewBox="0 0 18 22">
            <path d="M 5 6 a 3.5 3.5 0 1 0 0 7 a 3.5 3.5 0 1 0 0 -7 M 8 13 L 11 16" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''
        more_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="22" viewBox="0 0 18 22">
            <circle cx="5" cy="7" r="1.2" fill="{stroke}"/>
            <circle cx="9" cy="7" r="1.2" fill="{stroke}"/>
            <circle cx="13" cy="7" r="1.2" fill="{stroke}"/>
        </svg>'''
        if self._expanded:
            expand_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="22" viewBox="0 0 18 22">
                <path d="M 6 4 L 11 4 L 11 9 M 6 10 L 11 10 L 11 5" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
        else:
            expand_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="22" viewBox="0 0 18 22">
                <path d="M 8 4 L 3 4 L 3 9 M 8 10 L 3 10 L 3 5" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
        for btn, svg in [(self._search_btn, search_svg),
                         (self._more_btn, more_svg),
                         (self._expand_btn, expand_svg)]:
            lbl = btn.findChild(QLabel, "icon_lbl")
            if lbl:
                lbl.setPixmap(svg_icon(svg, 18, 22))

    # ── 窗口拖动 & 双击最大化 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_pos") and self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            win = self.window()
            if win:
                win.move(win.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()


# ══════════════════════════════════════════════════════════════
# 搜索条（浮动在标题栏下方）
# ══════════════════════════════════════════════════════════════

class SearchBar(QWidget):
    search_text_changed = Signal(str)
    next_match = Signal()
    prev_match = Signal()
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(28)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        self._input = QLineEdit()
        self._input.setPlaceholderText("搜索会话内容...")
        self._input.textChanged.connect(self.search_text_changed.emit)
        layout.addWidget(self._input, 1)

        self._prev_btn = self._small_btn("↑")
        self._next_btn = self._small_btn("↓")
        self._close_btn = self._small_btn("✕")
        self._prev_btn.clicked.connect(self.prev_match.emit)
        self._next_btn.clicked.connect(self.next_match.emit)
        self._close_btn.clicked.connect(self.closed.emit)
        layout.addWidget(self._prev_btn)
        layout.addWidget(self._next_btn)
        layout.addWidget(self._close_btn)

        self._refresh_theme()

    def _small_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(18, 18)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {C['text_secondary']}; "
            f"border: none; border-radius: 4px; font-size: 10px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _refresh_theme(self):
        self.setStyleSheet(
            f"QWidget {{ background-color: {C['search_bar_bg']}; "
            f"border: 1px solid {C['search_bar_border']}; border-radius: 6px; }}"
            f"QLineEdit {{ background: transparent; color: {C['text_primary']}; "
            f"border: none; font-size: 12px; }}"
            f"QLineEdit::placeholder {{ color: {C['text_muted']}; }}"
        )
        for btn in (self._prev_btn, self._next_btn, self._close_btn):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {C['text_secondary']}; "
                f"border: none; border-radius: 4px; font-size: 10px; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
            )

    def setFocus(self):
        self._input.setFocus()

    def text(self) -> str:
        return self._input.text()

    def clear(self):
        self._input.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.closed.emit()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.prev_match.emit()
            else:
                self.next_match.emit()
        else:
            super().keyPressEvent(event)


# ══════════════════════════════════════════════════════════════
# 输入区
# ══════════════════════════════════════════════════════════════

class InputArea(QWidget):
    send_clicked = Signal()
    stop_clicked = Signal()
    mode_clicked = Signal()
    model_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.setMinimumHeight(104)  # 8+56+6+26+8 确保输入框+标签行不被裁剪
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 8, 20, 8)
        root.setSpacing(6)

        # ── 输入框（响应式：QTextEdit stretch=1 随窗口宽度自适应）──
        input_container = QWidget()
        input_container.setFixedHeight(56)
        ic_layout = QHBoxLayout(input_container)
        ic_layout.setContentsMargins(0, 0, 0, 0)
        ic_layout.setSpacing(0)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("输入 \"/\" 快速使用技能")
        self._text_edit.setFont(font(11))
        ic_layout.addWidget(self._text_edit, 1)

        root.addWidget(input_container)

        # ── 底部行：标签居左 + 发送按钮居右 ──
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)

        self._skill_btn = QPushButton("+")
        self._skill_btn.setFixedSize(20, 20)
        self._skill_btn.setCursor(Qt.PointingHandCursor)
        bottom_row.addWidget(self._skill_btn)

        self._mode_tag = self._make_tag("模式", "ask", 62)
        self._model_tag = self._make_tag("模型", "flash", 76)
        self._mode_tag.mousePressEvent = lambda e: self.mode_clicked.emit()
        self._model_tag.mousePressEvent = lambda e: self.model_clicked.emit()
        bottom_row.addWidget(self._mode_tag)
        bottom_row.addWidget(self._model_tag)
        bottom_row.addStretch()

        # 发送按钮：输入框外，右下角
        self._send_btn = QPushButton()
        self._send_btn.setFixedSize(24, 24)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.setToolTip("发送")
        self._send_btn.clicked.connect(self.send_clicked.emit)
        bottom_row.addWidget(self._send_btn)

        # 停止按钮：与发送按钮同位置，streaming 状态时显示
        self._stop_btn = QPushButton("停止")
        self._stop_btn.setFixedSize(50, 24)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setToolTip("停止生成")
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        self._stop_btn.hide()
        bottom_row.addWidget(self._stop_btn)

        root.addLayout(bottom_row)
        self.install_enter_shortcut()
        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._text_edit.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 8px; "
            f"padding: 8px 14px 8px 14px; font-size: 11px; }}"
        )
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background-color: #34d399; border-radius: 8px; border: none; }}"
            f"QPushButton:hover {{ background-color: #2ecc71; }}"
        )
        self._stop_btn.setStyleSheet(
            f"QPushButton {{ background-color: #ef4444; color: {C['text_inverse']}; border-radius: 6px; border: none; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: #dc2626; }}"
        )
        send_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
            <path d="M 12 7 L 16 15 L 13 15 L 13 19 L 11 19 L 11 15 L 8 15 Z" fill="#0f1729"/>
        </svg>'''
        self._send_btn.setIcon(QIcon(svg_icon(send_svg, 18, 18)))
        self._send_btn.setIconSize(QSize(18, 18))
        self._skill_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 10px; font-size: 14px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        for tag in (self._mode_tag, self._model_tag):
            tag.setStyleSheet(
                f"QWidget {{ background-color: {C['tag_bg']}; border: 0.5px solid {C['border']}; border-radius: 6px; }}"
                f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
            )

    def _make_tag(self, label: str, value: str, width: int) -> QWidget:
        """SVG: tag fill=tag_bg stroke=border rx=6, w=62/76 h=22。"""
        tag = QWidget()
        tag.setFixedSize(width, 22)
        tag.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(tag)
        hl.setContentsMargins(4, 0, 4, 0)
        hl.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(font(9))
        lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(lbl)

        val = QLabel(value)
        val.setFont(font(10))
        val.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(val)
        tag._value_label = val

        chev = QLabel("▾")
        chev.setFont(font(9))
        chev.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(chev)
        hl.addStretch()
        return tag

    def set_mode(self, mode: str):
        if hasattr(self, "_mode_tag"):
            self._mode_tag._value_label.setText(mode)

    def set_model(self, model: str):
        if hasattr(self, "_model_tag"):
            self._model_tag._value_label.setText(model)

    def set_streaming(self, active: bool):
        """切换发送/停止按钮显隐。"""
        self._send_btn.setVisible(not active)
        self._stop_btn.setVisible(active)

    def install_enter_shortcut(self):
        self._text_edit.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self._text_edit and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                # streaming 中按 Enter 不触发发送
                if self._stop_btn.isVisible():
                    return True
                self.send_clicked.emit()
                return True
        return super().eventFilter(watched, event)


# ══════════════════════════════════════════════════════════════
# 聊天区
# ══════════════════════════════════════════════════════════════

class _ResizeHandle(QWidget):
    """聊天区/输入区之间可拖拽分隔条：4px 高，中间 1px 着色，上下透明。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.setCursor(Qt.SizeVerCursor)
        self._chat_view = None  # QGraphicsView
        self._input = None      # InputArea
        self._rebuild = None    # 防抖回调
        self._dragging = False
        self._start_y = 0
        self._start_h = 0
        self._start_vh = 0
        theme.changed.connect(self._refresh_style)

    def bind(self, chat_view, input_area, rebuild_cb=None):
        self._chat_view = chat_view
        self._input = input_area
        self._rebuild = rebuild_cb

    def _refresh_style(self):
        self.setStyleSheet(f"_ResizeHandle {{ background-color: transparent; border-top: 1px solid {C['border']}; }}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._input:
            self._dragging = True
            p = event.globalPosition().toPoint()
            self._start_y = p.y()
            self._start_h = self._input.height()
            self._start_vh = self._chat_view.height() if self._chat_view else 0

    def mouseMoveEvent(self, event):
        if self._dragging and self._input:
            dy = event.globalPosition().toPoint().y() - self._start_y
            new_input_h = max(104, min(300, self._start_h - dy))
            self._input.setFixedHeight(new_input_h)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            if self._rebuild:
                self._rebuild()


class ChatArea(QWidget):
    confirmation_clicked = Signal(bool)
    analyze_project_clicked = Signal()
    sign_send_msg = Signal(str)
    sign_stop_msg = Signal()
    sign_mode_changed = Signal(str)
    sign_model_changed = Signal(str)
    sign_export_requested = Signal()
    sign_settings_requested = Signal()
    sign_toggle_left = Signal()
    sign_toggle_right = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialized = False
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(80)
        self._rebuild_timer.timeout.connect(self._debounced_rebuild)
        self._current_mode = "ask"
        self._current_model = "tool-agent"
        self._modes = ["ask", "plan", "craft"]
        self._setup_ui()
        self._chat_history = []
        self._search_keyword = ""
        self._search_matches = []
        self._search_current = -1
        self._initialized = True
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        self._header = HeaderBar()
        self._header.search_clicked.connect(self._toggle_search)
        self._header.more_clicked.connect(self._toggle_file_panel)
        self._header.expand_toggled.connect(self.sign_toggle_right.emit)
        layout.addWidget(self._header)

        # 标题栏下分隔线（SVG: y=40）
        self._sep1 = QFrame()
        self._sep1.setFixedHeight(1)
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep1)

        # 任务确认条（P3.3 新增，初始隐藏）
        self._confirm_bar = self._build_confirmation_bar()
        layout.insertWidget(1, self._confirm_bar)

        # 「帮我分析当前项目」按钮（work 类型会话显示）
        self._analyze_btn = QPushButton("帮我分析当前项目")
        self._analyze_btn.setCursor(Qt.PointingHandCursor)
        self._analyze_btn.hide()
        self._analyze_btn.clicked.connect(self.analyze_project_clicked.emit)
        layout.insertWidget(3, self._analyze_btn)

        # QGraphicsView 聊天区
        self._view = QGraphicsView()
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._view.setFrameShape(QGraphicsView.NoFrame)
        self._view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._view.setStyleSheet(
            "QGraphicsView { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        self._scene = ChatScene()
        self._view.setScene(self._scene)
        layout.addWidget(self._view, 1)

        # 输入区可拖拽分隔条（4px，中间 1px 着色）
        self._resize_handle = _ResizeHandle()
        layout.addWidget(self._resize_handle)

        # 输入区
        self._input = InputArea()
        layout.addWidget(self._input)
        self._resize_handle.bind(self._view, self._input, self._debounced_rebuild)
        self.setStyleSheet(f"background-color: {C['bg_primary']};")

        # 浮动搜索条（标题栏下方，子控件覆盖）
        self._search_bar = SearchBar(self)
        self._search_bar.hide()
        self._search_bar.search_text_changed.connect(self._on_search_text_changed)
        self._search_bar.next_match.connect(self._on_search_next)
        self._search_bar.prev_match.connect(self._on_search_prev)
        self._search_bar.closed.connect(self._hide_search)

        # "..." 下拉面板（内嵌子控件，跟随主窗口，非独立顶层窗口）
        self._more_dropdown = MoreDropdown(self)
        self._more_dropdown.export_requested.connect(self.sign_export_requested.emit)
        self._more_dropdown.settings_requested.connect(self.sign_settings_requested.emit)
        self._more_dropdown.raise_()

        # 输入区事件 → V5 标准信号
        self._input.set_mode(self._current_mode)
        self._input.set_model(self._current_model)
        self._input.send_clicked.connect(self._on_send_clicked)
        self._input.stop_clicked.connect(self.sign_stop_msg.emit)
        self._input.mode_clicked.connect(self._on_mode_clicked)
        self._input.model_clicked.connect(self._on_model_clicked)

    def _on_send_clicked(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        self.input_field.clear()
        self.sign_send_msg.emit(text)

    def _on_mode_clicked(self):
        idx = self._modes.index(self._current_mode) if self._current_mode in self._modes else 0
        self._current_mode = self._modes[(idx + 1) % len(self._modes)]
        self._input.set_mode(self._current_mode)
        self.sign_mode_changed.emit(self._current_mode)

    def set_modes(self, modes: list[str]):
        """由 MainWindow 传入引擎实际支持的模式列表。"""
        if modes:
            self._modes = list(modes)
            if self._current_mode not in self._modes:
                self._current_mode = self._modes[0]
                self._input.set_mode(self._current_mode)

    def _on_model_clicked(self):
        models = ["tool-agent", "flash", "deepseek-pro"]
        idx = models.index(self._current_model) if self._current_model in models else 0
        self._current_model = models[(idx + 1) % len(models)]
        self._input.set_model(self._current_model)
        self.sign_model_changed.emit(self._current_model)

    def set_mode(self, mode: str):
        self._current_mode = mode
        self._input.set_mode(mode)

    def set_model(self, model: str):
        self._current_model = model
        self._input.set_model(model)

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        self._analyze_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_input']}; color: {C['accent']}; border: 0.5px solid {C['accent']}; "
            f"border-radius: 8px; padding: 6px 14px; font-size: 11px; font-weight: 600; margin: 6px 20px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._resize_handle._refresh_style()
        self._view.setStyleSheet(
            "QGraphicsView { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        self._scene.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 下拉面板/搜索条随窗口 resize 重新定位
        if hasattr(self, '_more_dropdown') and self._more_dropdown.isVisible():
            self._more_dropdown.position_under(self._header._more_btn)
        if hasattr(self, '_search_bar') and self._search_bar.isVisible():
            self._search_bar.setGeometry(8, 42, self.width() - 16, 28)
        if self._initialized:
            new_w = self._view.viewport().width() if self._view.viewport() else self.width()
            if abs(new_w - ChatScene.CHAT_W) > 4:
                self._pending_width = new_w
                self._rebuild_timer.start()

    def _debounced_rebuild(self):
        """防抖后重建：拖动停止 80ms 后执行。"""
        if hasattr(self, '_pending_width') and self._pending_width:
            self._rebuild_content(self._pending_width)
            self._pending_width = None
        else:
            self._rebuild_content()

    def _rebuild_content(self, width: float = None):
        """清除并重绘聊天区内容，适配新宽度。"""
        if width is not None:
            ChatScene.set_width(width)
        self._render()

    def _scroll_to_bottom(self):
        vsb = self._view.verticalScrollBar()
        QTimer.singleShot(0, lambda: vsb.setValue(vsb.maximum()))

    def clear_chat(self):
        """清除聊天区消息历史并重绘。"""
        self._chat_history.clear()
        self._render()

    def _render(self):
        """根据 _chat_history 渲染聊天区。"""
        self._scene.clear_items()
        for idx, entry in enumerate(self._chat_history):
            role = entry.get("role")
            if role == "user":
                item = UserBubble(entry["text"])
                item._history_index = idx
                self._scene.add_chat_item(item)
            elif role == "system":
                item = SystemCard(entry["text"])
                item._history_index = idx
                self._scene.add_chat_item(item)
            elif role == "ai":
                self._add_ai_entry(entry, idx)
            elif role == "tool":
                self._add_tool_entry(entry, idx)
        self._scene.refresh()
        self._scroll_to_bottom()

    def _add_ai_entry(self, entry: dict, idx: int):
        thinking = _strip_html(entry.get("thinking", ""))
        if thinking:
            fold = FoldBlock("思考过程", "")
            txt = TextItem(thinking, color_key="text_secondary")
            fold.set_body([txt], txt.height())
            fold._history_index = idx
            self._scene.add_chat_item(fold)
        body = _strip_html(entry.get("body", ""))
        if body:
            item = TextItem(body, color_key="text_primary")
            item._history_index = idx
            self._scene.add_chat_item(item)

    def _add_tool_entry(self, entry: dict, idx: int):
        plain = _strip_html(entry.get("html", ""))
        if not plain:
            return
        fold = FoldBlock("工具执行", "")
        txt = TextItem(plain, color_key="text_secondary")
        fold.set_body([txt], txt.height())
        fold._history_index = idx
        self._scene.add_chat_item(fold)

    # ══════════════════════════════════════════════════════════════
    # UIRenderer 桥接 API（P3.2 已实现最小真实渲染）
    # ══════════════════════════════════════════════════════════════

    @property
    def input_field(self):
        return self._input._text_edit

    def append_user(self, text: str):
        self._chat_history.append({"role": "user", "text": text})
        self._render()

    def append_system(self, text: str):
        self._chat_history.append({"role": "system", "text": text})
        self._render()

    def append_ai(self, body: str, phase: str = "", thinking_fold: str = ""):
        if self._chat_history and self._chat_history[-1].get("role") in ("ai_stream", "ai"):
            self._chat_history[-1].update({
                "role": "ai", "body": body, "phase": phase, "thinking": thinking_fold,
            })
        else:
            self._chat_history.append({
                "role": "ai", "body": body, "phase": phase, "thinking": thinking_fold,
            })
        self._render()

    def append_tool_fold(self, tool_html: str):
        self._chat_history.append({"role": "tool", "html": tool_html})
        self._render()

    def append_chunk(self, chunk: str):
        if self._chat_history and self._chat_history[-1].get("role") in ("ai_stream", "ai"):
            self._chat_history[-1]["body"] += chunk
        else:
            self._chat_history.append({"role": "ai_stream", "body": chunk, "phase": "", "thinking": ""})
        self._render()

    def finalize_stream(self):
        if self._chat_history and self._chat_history[-1].get("role") == "ai_stream":
            self._chat_history[-1]["role"] = "ai"
        self._render()

    def _build_confirmation_bar(self) -> QWidget:
        """构建任务确认条（含确认/取消按钮）。"""
        bar = QWidget()
        bar.hide()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(8, 4, 8, 4)
        hl.setSpacing(8)
        self._confirm_lbl = QLabel("是否确认执行以下任务？")
        self._confirm_lbl.setFont(font(10))
        self._confirm_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._confirm_lbl.setWordWrap(True)
        hl.addWidget(self._confirm_lbl, 1)

        yes_btn = QPushButton("确认")
        yes_btn.setCursor(Qt.PointingHandCursor)
        yes_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['accent']}; color: {C['text_inverse']}; "
            f"border: none; border-radius: 4px; padding: 2px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue']}; }}"
        )
        no_btn = QPushButton("取消")
        no_btn.setCursor(Qt.PointingHandCursor)
        no_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: none; border-radius: 4px; padding: 2px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
        yes_btn.clicked.connect(lambda: self.confirmation_clicked.emit(True))
        no_btn.clicked.connect(lambda: self.confirmation_clicked.emit(False))
        hl.addWidget(yes_btn)
        hl.addWidget(no_btn)
        return bar

    def set_streaming(self, active: bool):
        if active:
            self._header._status_lbl.setText("回答中...")
            self._header._status_lbl.show()
        else:
            self._header._status_lbl.hide()
            self._header._status_lbl.clear()
        self._input.set_streaming(active)

    def set_analyze_button_visible(self, visible: bool):
        """控制「帮我分析当前项目」按钮显隐。"""
        self._analyze_btn.setVisible(visible)

    def set_title(self, title: str, env: str = ""):
        """设置聊天区标题与项目路径副标题。"""
        self._header._title_lbl.setText(title)
        if env:
            self._header._env_lbl.setText(env)
            self._header._env_lbl.show()
        else:
            self._header._env_lbl.clear()
            self._header._env_lbl.hide()

    def clear_phase_ui(self):
        self._header._status_lbl.hide()
        self._header._status_lbl.clear()

    def show_confirmation(self, task_list):
        lines = []
        for i, t in enumerate(task_list[:5], 1):
            desc = getattr(t, "description", str(t))
            lines.append(f"{i}. {desc}")
        if len(task_list) > 5:
            lines.append(f"... 等共 {len(task_list)} 项")
        text = "\n".join(lines) if lines else "（无具体任务）"
        self._confirm_lbl.setText(f"是否确认执行以下任务？\n{text}")
        self._confirm_bar.show()

    def hide_confirmation(self):
        self._confirm_bar.hide()

    def set_send_enabled(self, enabled: bool):
        self._input.setEnabled(enabled)

    def set_phase_indicator(self, phase: str, task_count: int = 0):
        if phase:
            self._header._status_lbl.setText(f"阶段：{phase} ({task_count})")
            self._header._status_lbl.show()
        else:
            self._header._status_lbl.hide()

    def set_current_phase(self, phase: str):
        self.set_phase_indicator(phase, 0)

    def to_plain_text(self) -> str:
        """返回聊天区所有消息文本的拼接（供测试使用）。"""
        parts = []
        for entry in self._chat_history:
            role = entry.get("role")
            if role == "user":
                parts.append(entry.get("text", ""))
            elif role in ("ai", "ai_stream"):
                parts.append(entry.get("body", ""))
            elif role == "system":
                parts.append(entry.get("text", ""))
        return "\n".join(parts)

    def _toggle_search(self):
        """切换浮动搜索条显隐。"""
        if self._search_bar.isHidden():
            self._search_bar.setGeometry(8, 42, self.width() - 16, 28)
            self._search_bar.show()
            self._search_bar.raise_()
            self._search_bar.setFocus()
        else:
            self._hide_search()

    def _hide_search(self):
        self._search_bar.hide()
        self._search_bar.clear()
        self._on_search_text_changed("")

    def _on_search_text_changed(self, text: str):
        keyword = text.strip().lower()
        self._search_keyword = keyword
        self._search_matches = []
        matched_indices = set()
        for idx, entry in enumerate(self._chat_history):
            content = ""
            role = entry.get("role")
            if role == "user":
                content = entry.get("text", "")
            elif role in ("ai", "ai_stream"):
                content = entry.get("body", "")
            elif role == "system":
                content = entry.get("text", "")
            elif role == "tool":
                content = entry.get("html", "")
            if keyword and keyword in content.lower():
                matched_indices.add(idx)
                self._search_matches.append(idx)
        for item in self._scene._items:
            if hasattr(item, "set_highlight"):
                item.set_highlight(getattr(item, "_history_index", -1) in matched_indices)
        self._scene.refresh()
        if self._search_matches:
            self._search_current = 0
            self._scroll_to_item(self._search_matches[0])

    def _on_search_next(self):
        if not self._search_matches:
            return
        self._search_current = (self._search_current + 1) % len(self._search_matches)
        self._scroll_to_item(self._search_matches[self._search_current])

    def _on_search_prev(self):
        if not self._search_matches:
            return
        self._search_current = (self._search_current - 1) % len(self._search_matches)
        self._scroll_to_item(self._search_matches[self._search_current])

    def _scroll_to_item(self, idx: int):
        target = None
        for item in self._scene._items:
            if getattr(item, "_history_index", -1) == idx:
                target = item
                break
        if target is None:
            return
        y = int(target.y())
        vsb = self._view.verticalScrollBar()
        vsb.setValue(y)

    def _toggle_file_panel(self):
        """点击 ... 切换下拉面板显隐（内嵌子控件，跟随主窗口）。"""
        dd = self._more_dropdown
        if dd.isHidden():
            dd.position_under(self._header._more_btn)
            dd.show()
            dd.raise_()
        else:
            dd.hide()



