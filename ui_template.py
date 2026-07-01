"""
ui_template.py — Agent Workbench 纯 UI 模版（零业务逻辑）

三栏 QSplitter 布局，精确对齐 SVG 设计稿（ui-full-dark.svg 1024×720）：
  左 220px | 中 stretch | 右 400px

交互：
  - 左栏 Tab 切换（功能/会话）+ 会话项动态选中 + 分组折叠
  - 中栏标题栏三按钮 + 聊天区 QGraphicsView 像素级 Demo 内容
  - 右栏标签栏 + 最近文件 + 终端/编辑器占位
  - 左栏/右栏独立折叠展开

纯 UI 层，所有数据为 Demo 硬编码。
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QSplitter, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QSizePolicy,
    QFrame, QScrollArea, QMenu,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QSize, QTimer
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPalette, QAction, QIcon, QPixmap, QLinearGradient,
)

# ══════════════════════════════════════════════════════════════
# SVG 精确颜色常量（来自 ui-full-dark.svg / ui-chat-area.svg）
# ══════════════════════════════════════════════════════════════
C = {
    "bg_primary":        "#1a1a2e",
    "bg_sidebar":        "#16213e",
    "bg_right":          "#0f1729",
    "bg_darker":         "#1a1a2e",
    "accent":            "#007acc",
    "accent_blue":       "#569cd6",
    "border":            "#2a2a4a",
    "text_primary":      "#e0e0e0",
    "text_secondary":    "#a0a0b0",
    "text_muted":        "#6a6a8a",
    "text_inverse":      "#ffffff",
    "green":             "#4ec9b0",
    "yellow":            "#dcdcaa",
    "mono_text":         "#d4d4d4",
    "tag_bg":            "#0f3460",
    "gray":              "#858585",
    "purple":            "#c586c0",
    "btn_bg":            "#2a2a4a",
    "btn_hover":         "#3a3a5a",
    "bg_hover":          "#2a2a4a",
    "bg_selected":       "#0f3460",
}
CHAT_W = 402
LEFT_MARGIN = 20
CONTENT_W = 362
RIGHT_MARGIN = 20


def qcolor(hex_str: str) -> QColor:
    return QColor(hex_str)


def font(size: int, bold: bool = False, family: str = "Segoe UI") -> QFont:
    f = QFont(family, size)
    f.setBold(bold)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


def mono_font(size: int) -> QFont:
    f = QFont("Cascadia Code", size)
    f.setStyleHint(QFont.Monospace)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


# ══════════════════════════════════════════════════════════════
# 左栏：ConversationListPanel（220px）
# ══════════════════════════════════════════════════════════════

class SessionItem(QWidget):
    """单个会话项：精确对齐 SVG y=108~156。
       标题(x=24,y=126)、预览(x=24,y=144)、时间(x=24,y=160)，固定高度48。
    """
    clicked = Signal(int)

    def __init__(self, index: int, title: str, preview: str, time_str: str, parent=None):
        super().__init__(parent)
        self._index = index
        self._active = False
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)

        self._title_lbl = QLabel(self)
        self._title_lbl.setFont(font(12, bold=True))
        self._title_lbl.move(10, 6)
        self._title_lbl.resize(172, 18)
        self._title_lbl.setText(title[:24])

        self._preview_lbl = QLabel(self)
        self._preview_lbl.setFont(font(10))
        self._preview_lbl.move(10, 24)
        self._preview_lbl.resize(172, 16)
        self._preview_lbl.setText(preview[:40])

        self._time_lbl = QLabel(self)
        self._time_lbl.setFont(font(9))
        self._time_lbl.move(10, 40)
        self._time_lbl.resize(172, 12)
        self._time_lbl.setText(time_str)

        self._refresh_style()

    def _refresh_style(self):
        if self._active:
            self.setStyleSheet(
                f"SessionItem {{ background-color: {C['bg_selected']}; "
                f"border: 0.5px solid {C['accent']}; border-radius: 6px; }}"
            )
            self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        else:
            self.setStyleSheet(
                f"SessionItem {{ background-color: {C['bg_sidebar']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 6px; }}"
                f"SessionItem:hover {{ background-color: {C['bg_hover']}; }}"
            )
            self._title_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._preview_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._time_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)


class SessionGroup(QWidget):
    """可折叠会话分组。"""
    session_clicked = Signal(int)

    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._items: list[SessionItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(4)

        # 分组头
        hdr = QWidget()
        hdr.setFixedHeight(20)
        hdr.setStyleSheet(f"background-color: {C['bg_sidebar']}; border-radius: 4px;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(6)

        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setFixedSize(16, 16)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setStyleSheet(
            f"QPushButton {{ color: {C['text_secondary']}; background: transparent; border: none; font-size: 9px; }}")
        self._toggle_btn.clicked.connect(self._toggle)
        hl.addWidget(self._toggle_btn)

        lbl = QLabel(name)
        lbl.setFont(font(10, bold=True))
        lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(lbl, 1)

        cnt = QLabel(str(count))
        cnt.setFont(font(9))
        cnt.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(cnt)

        layout.addWidget(hdr)

        # 项容器
        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(4, 0, 4, 0)
        self._items_layout.setSpacing(4)
        layout.addLayout(self._items_layout)

    def add_session(self, item: SessionItem):
        item.clicked.connect(self.session_clicked.emit)
        self._items.append(item)
        self._items_layout.addWidget(item)

    def set_active(self, index: int):
        for it in self._items:
            it.set_active(it._index == index)

    def _toggle(self):
        self._expanded = not self._expanded
        self._toggle_btn.setText("▼" if self._expanded else "▶")
        for it in self._items:
            it.setVisible(self._expanded)


class LeftPanel(QWidget):
    """左栏面板：Tab切换 + 分组会话列表 + 底部控制。"""
    session_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._current_tab = "会话"
        self._groups: list[SessionGroup] = []
        self._all_items: list[SessionItem] = []
        self._active_idx = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ── Tab 行（SVG: 功能=#2a2a4a 会话=#007acc active）──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)

        self._func_btn = self._make_tab_btn("功能", active=False)
        self._sess_btn = self._make_tab_btn("会话", active=True)
        self._func_btn.clicked.connect(lambda: self._switch_tab("功能"))
        self._sess_btn.clicked.connect(lambda: self._switch_tab("会话"))

        tab_row.addWidget(self._func_btn, 1)
        tab_row.addWidget(self._sess_btn, 1)
        layout.addLayout(tab_row)

        # ── 工具行（SVG: 搜索 + 新会话 + 更多）──
        tool_row = QHBoxLayout()
        tool_row.setSpacing(6)

        self._search_btn = self._make_small_btn("🔍", 28, 22)
        self._new_btn = self._make_new_btn()
        self._more_btn = self._make_small_btn("...", 28, 22)
        tool_row.addWidget(self._search_btn)
        tool_row.addWidget(self._new_btn, 1)
        tool_row.addWidget(self._more_btn)
        layout.addLayout(tool_row)

        # 工具行下分隔线（SVG: y=76）
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(sep1)

        # ── 内容区（QStackedWidget：功能页 / 会话列表）──
        self._stack = QStackedWidget()

        # 功能页占位
        func_page = QLabel("功能页（工具/MCP/技能/自动化）\n待实现")
        func_page.setAlignment(Qt.AlignCenter)
        func_page.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px;")
        self._stack.addWidget(func_page)

        # 会话列表（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {C['bg_sidebar']}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )

        sess_widget = QWidget()
        self._sess_layout = QVBoxLayout(sess_widget)
        self._sess_layout.setContentsMargins(0, 0, 0, 0)
        self._sess_layout.setSpacing(6)
        self._sess_layout.addStretch()
        scroll.setWidget(sess_widget)
        self._stack.addWidget(scroll)

        self._stack.setCurrentIndex(1)
        layout.addWidget(self._stack, 1)

        # ── 底部控制（SVG: 分隔线 y=700 + 主题/设置按钮 h=12）──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(sep2)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        self._theme_btn = self._make_bottom_btn("🌙")
        self._settings_btn = self._make_bottom_btn("⚙")
        bottom_row.addWidget(self._theme_btn)
        bottom_row.addWidget(self._settings_btn)
        bottom_row.addStretch()
        layout.addLayout(bottom_row)

        # 填充 Demo 会话数据
        self._populate_sessions()

        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")

    def _make_tab_btn(self, text: str, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumWidth(88)
        bg = C["accent"] if active else C["btn_bg"]
        fg = C["text_inverse"] if active else C["text_secondary"]
        fw = 600 if active else 500
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: {fg}; "
            f"border: none; border-radius: 6px; padding: 2px 8px; "
            f"font-size: 11px; font-weight: {fw}; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return btn

    def _make_small_btn(self, text: str, w: int, h: int) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(w, h)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 10px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return btn

    def _make_new_btn(self) -> QPushButton:
        btn = QPushButton("+ 新会话")
        btn.setFixedHeight(22)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return btn

    def _make_bottom_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(32, 12)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; font-size: 8px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return btn

    def _switch_tab(self, tab: str):
        self._current_tab = tab
        is_func = (tab == "功能")
        self._stack.setCurrentIndex(0 if is_func else 1)
        self._func_btn.setChecked(is_func)
        self._sess_btn.setChecked(not is_func)
        # 更新按钮样式
        for btn, active in [(self._func_btn, is_func), (self._sess_btn, not is_func)]:
            bg = C["accent"] if active else C["btn_bg"]
            fg = C["text_inverse"] if active else C["text_secondary"]
            fw = 600 if active else 500
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )

    def _populate_sessions(self):
        """填充 Demo 分组会话数据（对应 SVG 设计稿）。"""
        # 分组1: agent_workbench
        g1 = SessionGroup("agent_workbench", 3)
        sessions_g1 = [
            ("v4 架构升级", "✓ 三个文件已修改并测试通过", "20:15"),
            ("量化策略回测", "△ 等待确认执行计划", "18:42"),
            ("API 接口设计", "等待第一条消息...", "15:30"),
        ]
        for i, (title, preview, t) in enumerate(sessions_g1):
            item = SessionItem(i, title, preview, t)
            g1.add_session(item)
            self._all_items.append(item)

        # 分组2: 全局会话
        g2 = SessionGroup("全局会话", 5)
        sessions_g2 = [
            ("通用问答", "如何配置 Python 环境？", "14:20"),
            ("代码片段咨询", "Python 装饰器用法", "13:08"),
            ("翻译任务", "将 README 翻译为英文", "10:45"),
        ]
        for i, (title, preview, t) in enumerate(sessions_g2, start=3):
            item = SessionItem(i, title, preview, t)
            g2.add_session(item)
            self._all_items.append(item)

        self._groups = [g1, g2]
        # 插入到 stretch 之前
        for g in reversed(self._groups):
            self._sess_layout.insertWidget(self._sess_layout.count() - 1, g)
        # 连接信号
        for g in self._groups:
            g.session_clicked.connect(self._on_session_clicked)
        # 默认选中第一项
        self._select_session(0)

    def _on_session_clicked(self, idx: int):
        self._select_session(idx)
        self.session_selected.emit(idx)

    def _select_session(self, idx: int):
        self._active_idx = idx
        for g in self._groups:
            g.set_active(idx)


# ══════════════════════════════════════════════════════════════
# 聊天区 QGraphicsItem 元素（像素级对齐 SVG）
# ══════════════════════════════════════════════════════════════

class ChatItem(QGraphicsItem):
    """所有聊天元素的基类。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._h = 0.0

    def height(self) -> float:
        return self._h

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, CHAT_W, self._h)


class UserBubble(ChatItem):
    """SVG: x=240 y=56 w=148 h=26 rx=8 fill=#007acc, text x=365 text-anchor=end"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fm = QFontMetrics(font(11))
        tw = fm.horizontalAdvance(text)
        bw = max(60.0, min(float(CONTENT_W), tw + 24.0))
        bh = 26.0
        bx = CHAT_W - 14 - bw  # RIGHT_PAD=14
        self._brect = QRectF(bx, 0, bw, bh)
        self._trect = QRectF(bx + 12, 0, bw - 24, bh)
        self._h = bh + 8
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self._brect, 8, 8)
        painter.fillPath(path, qcolor(C["accent"]))
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_inverse"]))
        painter.drawText(self._trect, Qt.AlignRight | Qt.AlignVCenter, self._text)


class FoldBlock(ChatItem):
    """可折叠块。SVG收起: rx=4 h=22 fill=#16213e；展开: header h=20 fill=#1a1a2e + body。"""
    FOLD_H = 22.0
    HEADER_H = 20.0
    RX = 4.0

    def __init__(self, title: str, status: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._status = status
        self._expanded = False
        self._body_h = 0.0
        self._body_items: list[QGraphicsItem] = []
        self._h = self.FOLD_H + 4
        self.setAcceptHoverEvents(True)

    def set_body(self, items: list[QGraphicsItem], h: float):
        self._body_items = items
        self._body_h = h
        for item in items:
            item.setParentItem(self)
            item.setVisible(False)

    def toggle(self):
        if self._expanded:
            self._expanded = False
            self._h = self.FOLD_H + 4
            for item in self._body_items:
                item.setVisible(False)
        else:
            self._expanded = True
            self._h = self.HEADER_H + self._body_h + 4
            for item in self._body_items:
                item.setVisible(True)
        self.prepareGeometryChange()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y0 = 0.0

        if self._expanded:
            # 外层卡片
            outer = QRectF(LEFT_MARGIN, y0, CONTENT_W, self.HEADER_H + self._body_h)
            p = QPainterPath()
            p.addRoundedRect(outer, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_sidebar"]))

            # Header bar
            hr = QRectF(LEFT_MARGIN, y0, CONTENT_W, self.HEADER_H)
            hp = QPainterPath()
            hp.addRoundedRect(hr, self.RX, self.RX)
            hp.addRect(LEFT_MARGIN, y0 + self.HEADER_H - self.RX, CONTENT_W, self.RX)
            painter.fillPath(hp, qcolor(C["bg_darker"]))

            self._draw_chevron(painter, LEFT_MARGIN + 10, y0 + 10, down=True)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(LEFT_MARGIN + 96, y0 + 15), self._status)
        else:
            fr = QRectF(LEFT_MARGIN, y0, CONTENT_W, self.FOLD_H)
            p = QPainterPath()
            p.addRoundedRect(fr, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_sidebar"]))
            self._draw_chevron(painter, LEFT_MARGIN + 12, y0 + 11, down=False)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(LEFT_MARGIN + 96, y0 + 15), self._status)

    def _draw_chevron(self, painter, cx, cy, down):
        pen = QPen(qcolor(C["accent_blue"]), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath()
        if down:
            path.moveTo(cx - 2, cy - 1); path.lineTo(cx, cy + 2); path.lineTo(cx + 2, cy - 1)
        else:
            path.moveTo(cx - 1, cy - 2); path.lineTo(cx + 2, cy); path.lineTo(cx - 1, cy + 2)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hr = QRectF(LEFT_MARGIN, 0, CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
            if hr.contains(event.pos()):
                self.toggle()
                event.accept()
                return
        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        hr = QRectF(LEFT_MARGIN, 0, CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
        self.setCursor(Qt.PointingHandCursor if hr.contains(event.pos()) else Qt.ArrowCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, CHAT_W, self._h)


class ToolEntry(ChatItem):
    """SVG: 4px左bar + ✓ + 工具名 + 耗时 + ▶参数"""
    def __init__(self, name: str, elapsed: str, success: bool = True, parent=None):
        super().__init__(parent)
        self._name = name
        self._elapsed = elapsed
        self._icon = "✓" if success else "✗"
        self._icon_color = qcolor(C["green"]) if success else qcolor("#f14c4c")
        self._h = 16
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 1.0
        # 4px bar
        br = QRectF(LEFT_MARGIN + 10, y, 4, 14)
        bp = QPainterPath()
        bp.addRoundedRect(br, 2, 2)
        painter.fillPath(bp, qcolor(C["border"]))
        # icon
        painter.setFont(mono_font(10))
        painter.setPen(self._icon_color)
        painter.drawText(QPointF(LEFT_MARGIN + 22, y + 11), self._icon)
        # name
        painter.setPen(qcolor(C["mono_text"]))
        painter.drawText(QPointF(LEFT_MARGIN + 33, y + 11), self._name)
        # elapsed
        painter.setFont(mono_font(9))
        painter.setPen(qcolor(C["text_muted"]))
        painter.drawText(QPointF(LEFT_MARGIN + 134, y + 11), self._elapsed)
        # args chevron
        painter.setPen(qcolor(C["accent_blue"]))
        painter.drawText(QPointF(LEFT_MARGIN + 189, y + 11), "▶ 参数")


class PhasePanel(ChatItem):
    """阶段面板：rx=8卡片 + 4px accent bar + header + body。"""
    HEADER_H = 24.0
    RX = 8.0
    PHASE_COLORS = {
        "analyze": C["accent_blue"], "execute": C["yellow"],
        "archive": C["green"], "verify": C["purple"],
    }

    def __init__(self, title: str, accent_hex: str, body_items: list = None, body_h: float = 0, parent=None):
        super().__init__(parent)
        self._title = title
        self._accent = qcolor(accent_hex)
        self._body_h = body_h
        self._h = self.HEADER_H + body_h + 16
        if body_items:
            for item in body_items:
                item.setParentItem(self)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4.0
        card_h = self.HEADER_H + self._body_h + 8

        # 卡片
        cr = QRectF(LEFT_MARGIN, y, CONTENT_W, card_h)
        cp = QPainterPath()
        cp.addRoundedRect(cr, self.RX, self.RX)
        painter.fillPath(cp, qcolor(C["bg_sidebar"]))
        pen = QPen(qcolor(C["border"]), 0.5)
        painter.setPen(pen)
        painter.drawPath(cp)

        # accent bar
        ar = QRectF(LEFT_MARGIN, y, 4, card_h)
        ap = QPainterPath()
        ap.addRoundedRect(ar, 2, 2)
        painter.fillPath(ap, self._accent)

        # header
        hr = QRectF(LEFT_MARGIN + 4, y, CONTENT_W - 4, self.HEADER_H)
        hp = QPainterPath()
        hp.addRoundedRect(hr, 6, 6)
        hp.addRect(LEFT_MARGIN + 4, y + self.HEADER_H - 6, CONTENT_W - 4, 6)
        painter.fillPath(hp, qcolor(C["bg_darker"]))
        painter.setPen(qcolor(C["text_primary"]))
        painter.setFont(font(12, bold=True))
        painter.drawText(QPointF(LEFT_MARGIN + 14, y + 17), self._title)


class BulletItem(ChatItem):
    """● + 文本"""
    def __init__(self, text: str, color_hex: str = C["green"], parent=None):
        super().__init__(parent)
        self._text = text
        self._color = qcolor(color_hex)
        self._h = 20

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(QPointF(LEFT_MARGIN + 13, 14), 3, 3)
        painter.setFont(font(10))
        painter.setPen(self._color)
        painter.drawText(QPointF(LEFT_MARGIN + 23, 17), self._text)


class StepItem(ChatItem):
    """执行步骤：✓/⟳/○ + 名称 + 详情"""
    ICONS = {"done": ("✓", C["green"]), "running": ("⟳", C["yellow"]),
             "pending": ("○", C["text_muted"]), "fail": ("✗", "#f14c4c")}

    def __init__(self, status: str, name: str, detail: str = "", parent=None):
        super().__init__(parent)
        self._icon, self._ic = self.ICONS.get(status, ("○", C["text_muted"]))
        self._name = name
        self._detail = detail
        self._h = 20

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(self._ic))
        painter.drawText(QPointF(LEFT_MARGIN + 14, y + 12), self._icon)
        painter.setFont(font(10))
        painter.setPen(qcolor(C["text_primary"]))
        painter.drawText(QPointF(LEFT_MARGIN + 29, y + 12), self._name)
        if self._detail:
            painter.setFont(font(9))
            painter.setPen(qcolor(C["text_muted"]))
            fm = QFontMetrics(font(10))
            painter.drawText(QPointF(LEFT_MARGIN + 29 + fm.horizontalAdvance(self._name) + 8, y + 12), self._detail)


class TextItem(ChatItem):
    """纯文本行。"""
    def __init__(self, text: str, color_hex: str = C["green"], parent=None):
        super().__init__(parent)
        self._text = text
        self._color = qcolor(color_hex)
        self._h = 22

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(font(10))
        painter.setPen(self._color)
        painter.drawText(QPointF(LEFT_MARGIN + 14, 15), self._text)


class SystemCard(ChatItem):
    """居中系统卡片。"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fm = QFontMetrics(font(11))
        lines = text.split("\n")
        lh = fm.height() + 2
        max_w = max(fm.horizontalAdvance(l) for l in lines)
        cw = min(CONTENT_W, max_w + 28 + 4)
        ch = len(lines) * lh + 20
        self._crect = QRectF((CHAT_W - cw) / 2, 4, cw, ch)
        self._lines = lines
        self._lh = lh
        self._h = ch + 8

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        cp = QPainterPath()
        cp.addRoundedRect(self._crect, 8, 8)
        painter.fillPath(cp, qcolor(C["bg_sidebar"]))
        painter.setPen(QPen(qcolor(C["border"]), 0.5))
        painter.drawPath(cp)
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_primary"]))
        y = self._crect.top() + 10
        for line in self._lines:
            painter.drawText(QPointF(self._crect.left() + 14, y + self._lh - 3), line)
            y += self._lh


# ══════════════════════════════════════════════════════════════
# 聊天场景
# ══════════════════════════════════════════════════════════════

class ChatScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._y = 8.0
        self._items: list = []
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))

    def add_chat_item(self, item: ChatItem) -> ChatItem:
        self.addItem(item)
        item.setPos(0, self._y)
        self._y += item.height() + 8
        self._items.append(item)
        self._update_rect()
        return item

    def _update_rect(self):
        h = max(self._y + 40, 720)
        self.setSceneRect(QRectF(0, 0, CHAT_W, h))

    def clear_items(self):
        super().clear()
        self._items.clear()
        self._y = 8.0


# ══════════════════════════════════════════════════════════════
# 标题栏
# ══════════════════════════════════════════════════════════════

class HeaderBar(QWidget):
    expand_toggled = Signal()
    search_clicked = Signal()
    more_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 双行标题（SVG: title y=16, env y=30）
        title_block = QVBoxLayout()
        title_block.setContentsMargins(20, 4, 0, 4)
        title_block.setSpacing(2)

        self._title_lbl = QLabel("v4 架构升级")
        self._title_lbl.setFont(font(12, bold=True))
        self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        title_block.addWidget(self._title_lbl)

        self._env_lbl = QLabel("F:\\Agent\\agent_workbench")
        self._env_lbl.setFont(font(10))
        self._env_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        title_block.addWidget(self._env_lbl)
        layout.addLayout(title_block, 1)

        # 垂直分隔线（SVG: x1=331）
        vsep = QLabel()
        vsep.setFixedSize(1, 24)
        vsep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(vsep)
        layout.addSpacing(6)

        # 三按钮
        self._search_btn = self._icon_btn("🔍", "搜索")
        self._search_btn.clicked.connect(self.search_clicked.emit)
        self._more_btn = self._icon_btn("⋯", "更多操作")
        self._more_btn.clicked.connect(self.more_clicked.emit)
        self._expand_btn = self._icon_btn("⤢", "折叠面板")
        self._expand_btn.clicked.connect(self.expand_toggled.emit)

        layout.addWidget(self._search_btn)
        layout.addWidget(self._more_btn)
        layout.addWidget(self._expand_btn)
        self.setStyleSheet(f"background-color: {C['bg_primary']};")

    def _icon_btn(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(18, 22)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
        return btn


# ══════════════════════════════════════════════════════════════
# 输入区
# ══════════════════════════════════════════════════════════════

class InputArea(QWidget):
    send_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 8, 20, 8)
        root.setSpacing(6)

        # ── 输入框 (SVG: x=241 y=660 w=362 h=56 rx=8) ──
        input_container = QWidget()
        input_container.setFixedHeight(56)
        input_container.setStyleSheet("background-color: transparent;")
        self._text_edit = QTextEdit(input_container)
        self._text_edit.setPlaceholderText("输入 \"/\" 快速使用技能")
        self._text_edit.setGeometry(0, 0, 362, 56)
        self._text_edit.setFont(font(11))
        self._text_edit.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_sidebar']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 8px; "
            f"padding: 8px 36px 8px 14px; font-size: 11px; }}"
        )

        # ── 发送按钮 (SVG: cx=585 cy=688 r=12 fill=#34d399, arrow black) ──
        self._send_btn = QPushButton(input_container)
        self._send_btn.setFixedSize(24, 24)
        self._send_btn.move(330, 16)  # 362 - 24 - 8
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background-color: #34d399; border-radius: 8px; border: none; "
            f"color: #0f1729; font-size: 16px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: #2ecc71; }}"
        )
        self._send_btn.setText("↑")
        self._send_btn.clicked.connect(self.send_clicked.emit)

        root.addWidget(input_container)

        # ── 标签行（SVG: + r=10 at x=257,y=702; 模式 w=62 x=277; 模型 w=76 x=345）──
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(0, 0, 0, 0)
        tag_row.setSpacing(8)

        self._skill_btn = QPushButton("+")
        self._skill_btn.setFixedSize(20, 20)
        self._skill_btn.setCursor(Qt.PointingHandCursor)
        self._skill_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 10px; font-size: 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        tag_row.addWidget(self._skill_btn)

        self._mode_tag = self._make_tag("模式", "ask", 62)
        self._model_tag = self._make_tag("模型", "flash", 76)
        tag_row.addWidget(self._mode_tag)
        tag_row.addWidget(self._model_tag)
        tag_row.addStretch()

        root.addLayout(tag_row)
        self.setStyleSheet(f"background-color: {C['bg_primary']};")

    def _make_tag(self, label: str, value: str, width: int) -> QWidget:
        """标签控件：label 灰色小字 + value 白色大字 + chevron，避免 QPushButton HTML 不渲染。"""
        tag = QWidget()
        tag.setFixedSize(width, 22)
        tag.setCursor(Qt.PointingHandCursor)
        tag.setStyleSheet(
            f"QWidget {{ background-color: {C['tag_bg']}; border: 0.5px solid {C['border']}; border-radius: 6px; }}"
        )
        hl = QHBoxLayout(tag)
        hl.setContentsMargins(4, 0, 4, 0)
        hl.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(font(9))
        lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(lbl)

        val = QLabel(value)
        val.setFont(font(10, bold=True))
        val.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        hl.addWidget(val)

        chev = QLabel("▼")
        chev.setFont(font(8))
        chev.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(chev)
        hl.addStretch()
        return tag


# ══════════════════════════════════════════════════════════════
# 聊天区
# ══════════════════════════════════════════════════════════════

class ChatArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._populate_demo()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        self._header = HeaderBar()
        layout.addWidget(self._header)

        # 标题栏下分隔线（SVG: y=40）
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(sep)

        # QGraphicsView 聊天区
        self._view = QGraphicsView()
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._view.setFrameShape(QGraphicsView.NoFrame)
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

        # 输入区分隔线（SVG: y=652）
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(sep2)

        # 输入区
        self._input = InputArea()
        layout.addWidget(self._input)
        self.setStyleSheet(f"background-color: {C['bg_primary']};")

    def _populate_demo(self):
        """填充 Demo 聊天内容（精确对应 ui-chat-area.svg）。"""
        scene = self._scene

        # 用户气泡
        scene.add_chat_item(UserBubble("帮我分析当前项目"))

        # 思考过程折叠（收起）
        scene.add_chat_item(FoldBlock("思考过程", "[5/7 已完成]"))

        # 工具执行折叠（展开）
        tools = FoldBlock("工具执行", "[3 工具 · 共 2.1s]")
        entry1 = ToolEntry("run_command", "0.8s")
        entry2 = ToolEntry("grep_refs", "0.3s")
        entry3 = ToolEntry("pytest", "1.0s")
        # 定位子项
        entry1.setPos(0, tools.HEADER_H + 2)
        entry2.setPos(0, tools.HEADER_H + 18)
        entry3.setPos(0, tools.HEADER_H + 34)
        tools.set_body([entry1, entry2, entry3], 50)
        tools.toggle()  # 展开
        scene.add_chat_item(tools)

        # 内部命令输出折叠（收起）
        scene.add_chat_item(FoldBlock("内部命令输出", "[212 行]"))

        # 📋 分析结果面板
        b1 = BulletItem("项目采用 v4 单轨事件总线架构")
        b2 = BulletItem("193/193 全量测试通过")
        b1.setPos(0, PhasePanel.HEADER_H + 6)
        b2.setPos(0, PhasePanel.HEADER_H + 26)
        scene.add_chat_item(PhasePanel("📋 分析结果", C["accent_blue"], [b1, b2], 48))

        # 📝 执行计划面板
        s1 = StepItem("done", "修改 v4/events.py", "新增 model 字段")
        s2 = StepItem("running", "修改 v4/main_window.py", "模型下拉框 + 持久化")
        s3 = StepItem("pending", "运行全量测试", "pytest tests/ -v")
        s1.setPos(0, PhasePanel.HEADER_H + 6)
        s2.setPos(0, PhasePanel.HEADER_H + 26)
        s3.setPos(0, PhasePanel.HEADER_H + 46)
        scene.add_chat_item(PhasePanel("📝 执行计划", C["yellow"], [s1, s2, s3], 68))

        # ✅ 完成报告面板
        t1 = TextItem("v4.0.5-alpha 存档完成")
        t1.setPos(0, PhasePanel.HEADER_H + 6)
        scene.add_chat_item(PhasePanel("✅ 完成报告", C["green"], [t1], 30))

        # 滚动到底部
        QTimer.singleShot(100, lambda: self._view.verticalScrollBar().setValue(
            self._view.verticalScrollBar().maximum()))


# ══════════════════════════════════════════════════════════════
# 右栏（400px）
# ══════════════════════════════════════════════════════════════

class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self._active_tab = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标签栏（SVG: h=28 fill=#0f1729）──
        tab_bar = QWidget()
        tab_bar.setFixedHeight(28)
        tb_layout = QHBoxLayout(tab_bar)
        tb_layout.setContentsMargins(8, 2, 8, 2)
        tb_layout.setSpacing(2)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(16, 16)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_hover']}; color: {C['text_secondary']}; "
            f"border-radius: 8px; font-size: 10px; border: none; }}"
        )
        tb_layout.addWidget(add_btn)

        # 标签按钮
        tab_names = ["v4 架构", "终端", "文件编辑器", "浏览器"]
        self._tab_btns: list[QPushButton] = []
        for i, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(24)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            tb_layout.addWidget(btn)
            self._tab_btns.append(btn)

            # SVG: close btn r=5 (d=10)
            if i > 0:  # 第一个标签不可关闭
                cls = QPushButton("✕")
                cls.setFixedSize(10, 10)
                cls.setCursor(Qt.PointingHandCursor)
                cls.setStyleSheet(
                    f"QPushButton {{ background-color: {C['bg_right']}; color: {C['text_muted']}; "
                    f"border-radius: 5px; font-size: 7px; border: none; }}"
                )
                tb_layout.addWidget(cls)

        tb_layout.addStretch()

        # 窗口控制按钮容器（由 MainWindow 注入回调）
        self._win_btns = QWidget()
        win_hl = QHBoxLayout(self._win_btns)
        win_hl.setContentsMargins(0, 0, 8, 0)
        win_hl.setSpacing(2)
        self._win_hl = win_hl
        tb_layout.addWidget(self._win_btns)

        tab_bar.setStyleSheet(f"background-color: {C['bg_right']};")
        layout.addWidget(tab_bar)

        # 标签栏下分隔线
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(sep)

        # ── 内容区（QStackedWidget）──
        self._stack = QStackedWidget()

        # Tab0: v4 架构（最近文件）
        tab0 = QWidget()
        t0l = QVBoxLayout(tab0)
        t0l.setContentsMargins(16, 8, 16, 8)
        t0l.setSpacing(4)

        t0l.addWidget(self._make_section_header("最近文件"))
        for path, t in [("v4/main_window.py", "2h 前"), ("v4/worker.py", "4h 前"),
                         ("agent_engine/engines/prompt_engine.py", "昨天")]:
            t0l.addWidget(self._make_file_row(path, t))
        t0l.addStretch()
        tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        self._stack.addWidget(tab0)

        # Tab1: 终端占位
        t1 = QLabel("终端\n（功能待实现）")
        t1.setAlignment(Qt.AlignCenter)
        t1.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px;")
        self._stack.addWidget(t1)

        # Tab2: 文件编辑器占位
        t2 = QLabel("文件编辑器\n（功能待实现）")
        t2.setAlignment(Qt.AlignCenter)
        t2.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px;")
        self._stack.addWidget(t2)

        # Tab3: 浏览器占位
        t3 = QLabel("浏览器\n（功能待实现）")
        t3.setAlignment(Qt.AlignCenter)
        t3.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px;")
        self._stack.addWidget(t3)

        layout.addWidget(self._stack, 1)
        self._switch_tab(0)
        self.setStyleSheet(f"background-color: {C['bg_right']};")

    def _make_section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 9px; font-weight: 600; "
            f"letter-spacing: 0.5px; padding: 0 0 4px 0;"
        )
        return lbl

    def _make_file_row(self, path: str, time_str: str) -> QWidget:
        row = QWidget()
        row.setFixedHeight(24)
        hl = QHBoxLayout(row)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        name_lbl = QLabel(path)
        name_lbl.setFont(font(11))
        name_lbl.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        hl.addWidget(name_lbl, 1)

        time_lbl = QLabel(time_str)
        time_lbl.setFont(font(9))
        time_lbl.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
        time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(time_lbl)

        # SVG: row fill=#16213e stroke=#2a2a4a rx=4
        row.setStyleSheet(
            f"QWidget {{ background-color: {C['bg_sidebar']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
        )
        return row

    def set_window_buttons(self, minimize_cb, maximize_cb, close_cb):
        """把系统最小化/最大化/关闭按钮嵌入右栏顶部状态栏最右侧，使用SVG图标。"""
        icons = [
            ("M 6 10 L 18 10", minimize_cb),   # 最小化：一条横线
            ("M 6 6 L 18 6 L 18 18 L 6 18 Z", maximize_cb),  # 最大化：方框
            ("M 6 6 L 18 18 M 18 6 L 6 18", close_cb),       # 关闭：X
        ]
        for path, cb in icons:
            btn = QPushButton()
            btn.setFixedSize(28, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 用 QLabel 显示 SVG 路径图标
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="20" viewBox="0 0 24 20">
                <path d="{path}" fill="none" stroke="{C['text_secondary']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
            lbl = QLabel(btn)
            lbl.setPixmap(svg_icon(svg, 24, 20))
            lbl.move(2, 0)
            btn.clicked.connect(cb)
            self._win_hl.addWidget(btn)

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            active = (i == idx)
            bg = C["bg_primary"] if active else C["bg_right"]
            fg = C["text_primary"] if active else C["text_secondary"]
            fw = 600 if active else 400
            btn.setChecked(active)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 10px; "
                f"font-size: 10px; font-weight: {fw}; text-align: left; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
                f"QPushButton:checked {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; "
                f"font-weight: 600; }}"
            )


# ══════════════════════════════════════════════════════════════
# 主窗口（QSplitter 三栏 + 独立折叠）
# ══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        self.resize(1024, 720)
        self.setMinimumWidth(800)
        self.setWindowTitle("Agent Workbench — UI Template")
        self._left_visible = True
        self._right_visible = True
        self._drag_pos = None
        self._corner_radius = 8
        self._setup_ui()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)

        # 左栏
        self._left = LeftPanel()
        self._splitter.addWidget(self._left)

        # 中栏
        self._center = ChatArea()
        self._center._header.expand_toggled.connect(self._toggle_panels)
        self._splitter.addWidget(self._center)

        # 右栏
        self._right = RightPanel()
        self._right.set_window_buttons(self.showMinimized, self._toggle_maximize, self.close)
        self._splitter.addWidget(self._right)

        self._splitter.setSizes([220, 404, 400])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        ml.addWidget(self._splitter)

        # 全局暗色主题
        self._apply_dark_palette()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _apply_rounded_mask(self):
        """Frameless窗口四角圆角遮罩。"""
        from PySide6.QtGui import QBitmap, QPainterPath, QPainter
        r = self._corner_radius
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, r, r)
        mask = QBitmap(self.size())
        mask.fill(Qt.color0)
        p = QPainter(mask)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillPath(path, Qt.color1)
        p.end()
        self.setMask(mask)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _apply_dark_palette(self):
        app = QApplication.instance()
        from PySide6.QtWidgets import QStyleFactory
        app.setStyle(QStyleFactory.create("Fusion"))
        p = QPalette()
        p.setColor(QPalette.Window, qcolor(C["bg_primary"]))
        p.setColor(QPalette.WindowText, qcolor(C["text_primary"]))
        p.setColor(QPalette.Base, qcolor(C["bg_primary"]))
        p.setColor(QPalette.Button, qcolor(C["bg_sidebar"]))
        p.setColor(QPalette.Highlight, qcolor(C["accent"]))
        app.setPalette(p)

    def _toggle_panels(self):
        """独立折叠/展开左右面板。"""
        if self._left_visible and self._right_visible:
            # 当前全展开 → 全收起
            self._left.hide()
            self._right.hide()
            self._left_visible = False
            self._right_visible = False
        elif not self._left_visible and not self._right_visible:
            # 当前全收起 → 全展开
            self._left.show()
            self._right.show()
            self._left_visible = True
            self._right_visible = True
        else:
            # 部分收起 → 全展开
            self._left.show()
            self._right.show()
            self._left_visible = True
            self._right_visible = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Workbench UI Template")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
