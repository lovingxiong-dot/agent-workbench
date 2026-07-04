"""
ui_template.py — Agent Workbench 纯 UI 模版（零业务逻辑）v0.5-alpha

三栏 QSplitter 布局，精确对齐 SVG 设计稿（ui-full-dark.svg 1024×720）：
  左 220px | 中 stretch | 右 400px

交互：
  - 左栏 Tab 切换（功能/会话）+ 会话项动态选中 + 分组折叠
  - 中栏标题栏三按钮 + 聊天区 QGraphicsView 像素级 Demo 内容
  - 右栏标签栏 + 最近文件 + 终端/编辑器占位
  - 左栏/右栏独立折叠展开
  - QSplitter InvisibleResizeHandle 透明拖拽热区（4px交互宽度）
  - 窗口边缘 resize（WM_NCHITTEST 8px 边缘 + SizeGrip 右下角）

纯 UI 层，所有数据为 Demo 硬编码。
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QSplitter, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QSizePolicy,
    QFrame, QScrollArea, QListWidget, QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPointF, QPoint, QSize, QTimer, QObject, QEvent
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPalette, QIcon, QPixmap, QLinearGradient, QCursor, QTextOption,
)
import PySide6.QtWidgets as QtW  # for qApp access

from .repository import SessionRepository, _get_app_root
from .event_bus import MessageBus
from .orchestrator import SessionOrchestrator
from .ui_renderer import UIRenderer
from .worker_manager import WorkerManager
from services.config_service import ConfigService
from .events import (
    UserSendEvent, UserStopEvent, UserConfirmEvent,
    SessionSwitchEvent, SessionDeleteEvent, SessionPinEvent, SessionCreateEvent,
)

# ══════════════════════════════════════════════════════════════
# 主题系统（深色/浅色，精确来自 ui-full-dark.svg / ui-full-light.svg）
# ══════════════════════════════════════════════════════════════
_THEMES = {
    "dark": {
        "bg_primary":        "#1a1a2e",
        "bg_sidebar":        "#16213e",
        "bg_right":          "#0f1729",
        "bg_darker":         "#1a1a2e",
        "bg_card":           "#16213e",
        "bg_card_selected":  "#0f3460",
        "bg_file_row":       "#16213e",
        "bg_input":          "#16213e",
        "bg_tab_active":     "#1a1a2e",
        "accent":            "#007acc",
        "accent_blue":       "#569cd6",
        "accent_light":      "#0f3460",
        "border":            "#2a2a4a",
        "text_primary":      "#e0e0e0",
        "text_secondary":    "#a0a0b0",
        "text_muted":        "#6a6a8a",
        "text_inverse":      "#ffffff",
        "text_label":        "#6a6a8a",
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
        "window_shadow":     "#000000",
    },
    "light": {
        "bg_primary":        "#f8f9fa",
        "bg_sidebar":        "#e9ecef",
        "bg_right":          "#ffffff",
        "bg_darker":         "#f1f3f5",
        "bg_card":           "#ffffff",
        "bg_card_selected":  "#e7f1ff",
        "bg_file_row":       "#f8f9fa",
        "bg_input":          "#ffffff",
        "bg_tab_active":     "#ffffff",
        "accent":            "#007acc",
        "accent_blue":       "#007acc",
        "accent_light":      "#e7f1ff",
        "border":            "#dee2e6",
        "text_primary":      "#212529",
        "text_secondary":    "#495057",
        "text_muted":        "#adb5bd",
        "text_inverse":      "#ffffff",
        "text_label":        "#6c757d",
        "green":             "#198754",
        "yellow":            "#856404",
        "mono_text":         "#212529",
        "tag_bg":            "#e7f1ff",
        "gray":              "#adb5bd",
        "purple":            "#7952b3",
        "btn_bg":            "#e9ecef",
        "btn_hover":         "#dee2e6",
        "bg_hover":          "#e9ecef",
        "bg_selected":       "#e7f1ff",
        "window_shadow":     "#adb5bd",
    },
}


class ThemeManager(QObject):
    """全局主题管理器。切换主题时发出 changed 信号，各组件接到后刷新样式。"""
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._name = "dark"
        self.C = dict(_THEMES[self._name])

    def set_theme(self, name: str):
        if name == self._name or name not in _THEMES:
            return
        self._name = name
        self.C.clear()
        self.C.update(_THEMES[name])
        self.changed.emit(name)

    @property
    def name(self) -> str:
        return self._name


theme = ThemeManager()
C = theme.C
# CHAT_W / CONTENT_W / LEFT_MARGIN 迁移为 ChatScene 类属性（支持动态宽度）


def qcolor(hex_str: str) -> QColor:
    return QColor(hex_str)


def svg_icon(svg_str: str, w: int, h: int) -> QPixmap:
    """将 SVG 字符串渲染为 QPixmap。"""
    from PySide6.QtSvg import QSvgRenderer
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    renderer = QSvgRenderer(bytes(svg_str, "utf-8"))
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return pm


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
# InvisibleResizeHandle — 透明拖拽热区（解决 QSplitter handleWidth=1 无法拖拽）
# ══════════════════════════════════════════════════════════════
# 原理：在 QSplitter 的 handle 位置叠加透明 QWidget，扩展交互热区至 4px，
#       视觉上 handleWidth 仍为 1px，但鼠标在 handle 左右各 2px 内均可触发拖拽。
# 零侵入：不修改 QSplitter 任何属性，仅叠加一层透明控件。

class InvisibleResizeHandle(QWidget):
    """透明拖拽热区控件 —— 放置在 QSplitter handle 位置，提供更宽的交互区域。"""
    HOT_ZONE_WIDTH: int = 4  # 热区宽度（像素），建议 4-6px

    def __init__(self, splitter: QSplitter, handle_index: int, parent=None):
        super().__init__(parent or splitter)
        self._splitter = splitter
        self._handle_index = handle_index
        self._is_horizontal = (splitter.orientation() == Qt.Orientation.Horizontal)
        self._dragging = False
        self._start_pos = None
        self._start_sizes = []
        self._start_global = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if self._is_horizontal:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        self._update_geometry()
        splitter.splitterMoved.connect(self._on_splitter_moved)
        splitter.installEventFilter(self)

    def _on_splitter_moved(self, pos: int, index: int):
        if index == self._handle_index:
            self._update_geometry()

    def eventFilter(self, watched, event):
        if watched == self._splitter and event.type() == QEvent.Type.Resize:
            self._update_geometry()
        return super().eventFilter(watched, event)

    def _update_geometry(self):
        handle = self._splitter.handle(self._handle_index)
        if not handle:
            self.hide()
            return
        handle_rect = handle.geometry()
        splitter_rect = self._splitter.rect()
        if self._is_horizontal:
            center_x = handle_rect.center().x()
            half_w = self.HOT_ZONE_WIDTH // 2
            x = max(0, center_x - half_w)
            y = 0
            w = self.HOT_ZONE_WIDTH
            h = splitter_rect.height()
            if x + w > splitter_rect.width():
                x = splitter_rect.width() - w
        else:
            center_y = handle_rect.center().y()
            half_h = self.HOT_ZONE_WIDTH // 2
            x = 0
            y = max(0, center_y - half_h)
            w = splitter_rect.width()
            h = self.HOT_ZONE_WIDTH
            if y + h > splitter_rect.height():
                y = splitter_rect.height() - h
        self.setGeometry(x, y, w, h)
        self.raise_()
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_global = event.globalPosition().toPoint()
            self._start_sizes = list(self._splitter.sizes())
            event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging or self._start_global is None:
            return
        delta = event.globalPosition().toPoint() - self._start_global
        delta_val = delta.x() if self._is_horizontal else delta.y()
        if delta_val == 0:
            return
        new_sizes = list(self._start_sizes)
        widget_a = self._splitter.widget(self._handle_index)
        widget_b = self._splitter.widget(self._handle_index + 1)
        min_a = widget_a.minimumWidth() if self._is_horizontal else widget_a.minimumHeight()
        min_b = widget_b.minimumWidth() if self._is_horizontal else widget_b.minimumHeight()
        new_sizes[self._handle_index] += delta_val
        new_sizes[self._handle_index + 1] -= delta_val
        # 边界检查
        if new_sizes[self._handle_index] < min_a:
            diff = min_a - new_sizes[self._handle_index]
            new_sizes[self._handle_index] = min_a
            new_sizes[self._handle_index + 1] -= diff
        if new_sizes[self._handle_index + 1] < min_b:
            diff = min_b - new_sizes[self._handle_index + 1]
            new_sizes[self._handle_index + 1] = min_b
            new_sizes[self._handle_index] -= diff
        self._splitter.setSizes(new_sizes)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self._start_global = None
            self._start_sizes = []
            event.accept()

    def enterEvent(self, event):
        if self._is_horizontal:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._dragging:
            self.unsetCursor()
        super().leaveEvent(event)


def install_invisible_handles(splitter: QSplitter, hot_zone_width: int = 4):
    """为 QSplitter 的所有 handle 安装透明拖拽热区。

    使用示例:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)  # 视觉上保持 1px
        install_invisible_handles(splitter)  # 启用 4px 拖拽热区
    """
    InvisibleResizeHandle.HOT_ZONE_WIDTH = hot_zone_width
    for i in range(splitter.count() - 1):
        handle = InvisibleResizeHandle(splitter, i, parent=splitter)


# ══════════════════════════════════════════════════════════════
# AppleMenu — Apple 风格弹出菜单（圆角、hover 高亮、非原生）
# ══════════════════════════════════════════════════════════════
class AppleMenuItem(QLabel):
    """菜单项：文本标签 + hover 圆角高亮"""
    clicked = Signal()
    __ACTIVE_BG = "#007AFF1A"  # 10% accent (light & dark 通用)

    def __init__(self, text: str, is_separator=False):
        super().__init__()
        self._is_sep = is_separator
        self._hover = False
        if is_separator:
            self.setFixedHeight(1)
        else:
            self.setText(text)
            self.setFixedHeight(32)
            self.setCursor(Qt.PointingHandCursor)
            self.setMouseTracking(True)
            self.setIndent(12)
            self._style()

    def _style(self):
        if self._is_sep:
            return
        if self._hover:
            self.setStyleSheet(
                f"AppleMenuItem {{ background-color: {self.__ACTIVE_BG}; "
                f"color: {C['text_primary']}; font-size: 13px; "
                f"border-radius: 6px; margin: 1px 6px; }}"
            )
        else:
            self.setStyleSheet(
                f"AppleMenuItem {{ background-color: transparent; "
                f"color: {C['text_primary']}; font-size: 13px; "
                f"border-radius: 6px; margin: 1px 6px; }}"
            )

    def enterEvent(self, e): self._hover = True; self._style()
    def leaveEvent(self, e): self._hover = False; self._style()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and not self._is_sep:
            self.clicked.emit()


class AppleMenu(QWidget):
    """Apple 风格弹出菜单：圆角背景 + 像素级阴影边框"""
    MENU_WIDTH = 180
    CORNER = 8

    def __init__(self, parent=None):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedWidth(self.MENU_WIDTH)
        self._items: list[AppleMenuItem] = []

    def add_item(self, text: str) -> AppleMenuItem:
        item = AppleMenuItem(text)
        self._items.append(item)
        return item

    def add_separator(self):
        sep = AppleMenuItem("", is_separator=True)
        self._items.append(sep)

    def build(self):
        """构建内部布局，计算总高度"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)
        for it in self._items:
            if it._is_sep:
                sep_w = QWidget()
                sep_w.setFixedHeight(9)
                sep_w.setStyleSheet(f"border-top: 1px solid {C['border']}; margin: 4px 6px;")
                layout.addWidget(sep_w)
            else:
                layout.addWidget(it)
                it.clicked.connect(self.close)
        h = sum(it.height() if not it._is_sep else 9 for it in self._items) + 12
        self.setFixedHeight(h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # 外侧微阴影边框
        p.setBrush(QColor(0, 0, 0, 40))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), self.CORNER, self.CORNER)
        # 主背景
        p.setBrush(QColor(C["bg_card"]))
        p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), self.CORNER - 1, self.CORNER - 1)
        # 细边框
        p.setPen(QPen(QColor(C["border"]), 0.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1.5, 1.5, self.width() - 3, self.height() - 3), self.CORNER, self.CORNER)
        p.end()

    def show_at(self, pos: QPoint):
        self.build()
        self.move(pos)
        self.show()
        QTimer.singleShot(100, self._install_close_filter)

    def _install_close_filter(self):
        QtW.QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            gp = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            if not self.geometry().contains(gp):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        QtW.QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)


# ══════════════════════════════════════════════════════════════
# EdgeResizeWidget — 透明窗口边缘 resize 手柄（startSystemResize）
# ══════════════════════════════════════════════════════════════
# 原理：在 centralWidget 最上层放置 8px 宽的透明 QWidget，
#       mousePressEvent 调用 windowHandle().startSystemResize()。
# Qt 跨平台 API，不依赖 Windows WS_THICKFRAME 样式。

class EdgeResizeWidget(QWidget):
    """透明窗口边缘 resize 手柄。通过 place() 手动定位，支持 4 边 + 4 角。"""
    SIZE = 8  # 边缘宽度（像素）

    def __init__(self, edges, cursor_shape, parent=None):
        super().__init__(parent)
        self._edges = edges
        self.setCursor(QCursor(cursor_shape))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

    def place(self, x, y, w, h):
        """手动定位 + 置顶到最上层 Z 序。"""
        self.setGeometry(x, y, w, h)
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win and win.windowHandle():
                win.windowHandle().startSystemResize(self._edges)


# ══════════════════════════════════════════════════════════════
# 左栏：ConversationListPanel（220px）
# ══════════════════════════════════════════════════════════════

class SessionItem(QWidget):
    """单个会话项：精确对齐 ui-full-dark/light.svg。
       卡片 192×48 rx=6；标题/状态/时间按 SVG 坐标 x=24 左对齐。
    """
    clicked = Signal(int)

    def __init__(self, index: int, title: str, preview: str, time_str: str, parent=None):
        super().__init__(parent)
        self._index = index
        self._active = False
        self._hover = False
        self.setMinimumHeight(58)  # 高度随内容自适应，最低 58px
        self.setMinimumWidth(1)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 4)
        layout.setSpacing(5)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(font(12, bold=True))
        self._title_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setMinimumWidth(1)
        self._title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self._title_lbl)

        self._preview_lbl = QLabel(preview)
        self._preview_lbl.setFont(font(9))
        self._preview_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._preview_lbl.setWordWrap(True)
        self._preview_lbl.setMinimumWidth(1)
        self._preview_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self._preview_lbl)

        self._refresh_style()
        theme.changed.connect(self._refresh_style)
        # 清除可能残留的 QSS，由 paintEvent 全权绘制
        self.setStyleSheet("")

    def _refresh_style(self):
        """应用主题颜色到子标签，不直接设 SessionItem 样式（由 paintEvent 绘制）。"""
        if self._active:
            self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        else:
            self._title_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
            self._preview_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self.update()  # 触发 paintEvent 重绘圆角背景

    def paintEvent(self, event):
        """自定义绘制：单个圆角矩形背景（含 hover）+ 选中边框，统一包围全部内容。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        r = 6.0  # SVG rx=6

        # 背景填充（选中 > hover > 普通）
        if self._active:
            bg = C["bg_card_selected"]
        elif self._hover:
            bg = C["bg_hover"]
        else:
            bg = C["bg_card"]
        p.setBrush(QColor(bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, r, r)

        # 边框：1px 内缩确保笔完全在 widget 内，四边厚度一致（无裁切/无 sub-pixel 漂移）
        border_color = C["accent"] if self._active else C["border"]
        pen = QPen(QColor(border_color), 1.0, Qt.SolidLine)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        border_rect = QRectF(1.0, 1.0, rect.width() - 2.0, rect.height() - 2.0)
        border_r = max(r - 1.0, 0.5)
        p.drawRoundedRect(border_rect, border_r, border_r)

        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)

    def _show_context_menu(self, pos):
        """右键菜单：Apple 风格"""
        m = AppleMenu()
        new_item = m.add_item("新会话")
        proj_item = m.add_item("项目会话")
        m.add_separator()
        rename_item = m.add_item("重命名")
        m.add_separator()
        del_item = m.add_item("删除会话")
        # 点击 → 关闭菜单 → 下一帧执行业务（纯开关模式）
        new_item.clicked.connect(lambda: self._handle_menu_click("new"))
        proj_item.clicked.connect(lambda: self._handle_menu_click("project"))
        rename_item.clicked.connect(lambda: self._handle_menu_click("rename"))
        del_item.clicked.connect(lambda: self._handle_menu_click("delete"))
        m.show_at(self.mapToGlobal(pos))
        self._active_menu = m

    def _handle_menu_click(self, action: str):
        """菜单项点击 → close() → 下一帧执行，主循环不阻塞"""
        self._active_menu.close()
        QTimer.singleShot(0, lambda a=action: self._execute_menu_action(a))

    def _execute_menu_action(self, action: str):
        """菜单动作执行（菜单已关闭，主循环空闲）"""
        if action == "project":
            path = QFileDialog.getExistingDirectory(None, "选择项目路径")
            if path:
                pass  # 占位：主线接入时创建项目会话
        elif action == "new":
            pass
        elif action == "rename":
            pass
        elif action == "delete":
            pass


class SessionGroup(QWidget):
    """可折叠会话分组：分组头 + 右侧计数。"""
    session_clicked = Signal(int)

    def __init__(self, name: str, count: int, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._name = name
        self._count = count
        self._items: list[SessionItem] = []
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(4)

        # 分组头（SVG: h=20 rx=4 fill=bg_sidebar）
        self._hdr = QWidget()
        self._hdr.setFixedHeight(20)
        self._hdr.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(6)

        self._toggle_btn = QLabel("▼")
        self._toggle_btn.setFont(font(9, bold=True))
        self._toggle_btn.setFixedSize(16, 16)
        self._toggle_btn.setAlignment(Qt.AlignCenter)
        self._toggle_btn.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(self._toggle_btn)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(10, bold=True))
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        hl.addWidget(self._name_lbl, 1)

        self._cnt_lbl = QLabel(str(self._count))
        self._cnt_lbl.setFont(font(9))  # SVG font-size=9
        self._cnt_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(self._cnt_lbl)

        self._add_btn = QLabel("+")
        self._add_btn.setFont(font(11, bold=True))
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(f"color: {C['text_muted']}; background: transparent; padding: 0px 2px;")
        self._add_btn.mousePressEvent = lambda e: None  # 占位，主线接入时改为 emit new_session_requested
        hl.addWidget(self._add_btn)

        self._hdr.mousePressEvent = lambda e: self._toggle() if e.button() == Qt.LeftButton else None
        layout.addWidget(self._hdr)

        # 项容器
        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(4, 0, 4, 0)
        self._items_layout.setSpacing(4)
        layout.addLayout(self._items_layout)
        self._refresh_style()

    def _refresh_style(self):
        self._hdr.setStyleSheet(
            f"background-color: {C['bg_sidebar']}; border-radius: 4px;"
        )
        self._toggle_btn.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._cnt_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._add_btn.setStyleSheet(f"color: {C['text_muted']}; background: transparent; padding: 0px 2px;")

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


class _FuncRow(QWidget):
    """功能页通用行：自动监听主题变化。"""
    def __init__(self, height: int = 24, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        theme.changed.connect(self._refresh_style)

    def _base_style(self):
        return (
            f"QWidget {{ background-color: {C['tag_bg']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
            f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
        )

    def _refresh_style(self):
        self.setStyleSheet(self._base_style())


class _ToolRow(_FuncRow):
    def __init__(self, name: str, enabled: bool, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._enabled = enabled
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._status = QLabel("开" if self._enabled else "关")
        self._status.setFont(font(9))
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setFixedSize(26, 12)
        hl.addWidget(self._status)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        dot_color = C["green"] if self._enabled else C["gray"]
        name_color = C["text_primary"] if self._enabled else C["text_secondary"]
        status_color = C["green"] if self._enabled else C["gray"]
        self._dot.setStyleSheet(f"color: {dot_color}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {name_color}; background: transparent;")
        self._status.setStyleSheet(
            f"color: {status_color}; background-color: {status_color}33; "
            f"border-radius: 6px; padding: 0 2px;"
        )


class _McpRow(_FuncRow):
    def __init__(self, name: str, connected: bool, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._connected = connected
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._status = QLabel("已连接" if self._connected else "未连接")
        self._status.setFont(font(9))
        self._status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(self._status)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        dot_color = C["green"] if self._connected else C["gray"]
        name_color = C["text_primary"] if self._connected else C["text_secondary"]
        status_color = C["green"] if self._connected else C["gray"]
        self._dot.setStyleSheet(f"color: {dot_color}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {name_color}; background: transparent;")
        self._status.setStyleSheet(f"color: {status_color}; background: transparent;")


class _SkillRow(_FuncRow):
    def __init__(self, name: str, parent=None):
        super().__init__(26, parent)
        self._name = name
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(4)

        self._icon = QLabel("⚡")
        self._icon.setFont(font(11))
        hl.addWidget(self._icon)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        self._icon.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")


class _AutoRow(_FuncRow):
    def __init__(self, name: str, time_str: str, parent=None):
        super().__init__(24, parent)
        self._name = name
        self._time_str = time_str
        self._setup_ui()

    def _setup_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFont(font(7))
        hl.addWidget(self._dot)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font(11))
        hl.addWidget(self._name_lbl, 1)

        self._time = QLabel(self._time_str)
        self._time.setFont(font(9))
        self._time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(self._time)
        self._refresh_style()

    def _refresh_style(self):
        super()._refresh_style()
        self._dot.setStyleSheet(f"color: {C['yellow']}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._time.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")


class FunctionPage(QWidget):
    """功能页：按 ui-left-function.svg 精确绘制（工具 / MCP / 技能 / 自动化）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(14, 0, 14, 0)
        self._cl.setSpacing(0)

        # 工具区
        tool_box = self._make_section("工具", [
            _ToolRow("run_command", True),
            _ToolRow("grep_files", False),
            _ToolRow("write_file", True),
        ])
        self._cl.addWidget(tool_box)
        self._cl.addSpacing(12)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # MCP 区
        mcp_box = self._make_section("MCP", [
            _McpRow("GitHub", True),
            _McpRow("Notion", False),
        ])
        self._cl.addWidget(mcp_box)
        self._cl.addSpacing(18)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # 技能区（行高 26）
        skill_box = self._make_section("技能", [
            _SkillRow("archive"),
            _SkillRow("handoff"),
            _SkillRow("gitops"),
        ], row_spacing=4)
        self._cl.addWidget(skill_box)
        self._cl.addSpacing(18)
        self._cl.addWidget(self._sep())
        self._cl.addSpacing(18)

        # 自动化区
        auto_box = self._make_section("自动化", [
            _AutoRow("每日日报", "08:00"),
        ])
        self._cl.addWidget(auto_box)

        self._cl.addStretch()
        self._scroll.setWidget(content)
        layout.addWidget(self._scroll)
        self._refresh_theme()

    def _make_section(self, title: str, rows: list, row_spacing: int = 4) -> QWidget:
        box = QWidget()
        vl = QVBoxLayout(box)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)
        hdr = self._section_header(title)
        hdr.setObjectName("func_section_header")
        vl.addWidget(hdr)
        for r in rows:
            vl.addWidget(r)
            vl.setSpacing(row_spacing)
        return box

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {C['bg_sidebar']}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        for hdr in self.findChildren(QLabel, "func_section_header"):
            hdr.setStyleSheet(
                f"color: {C['text_label']}; font-size: 9px; font-weight: 600; "
                f"letter-spacing: 0.5px; padding: 0 0 2px 0; background: transparent;"
            )
        for sep in self.findChildren(QFrame, "func_sep"):
            sep.setStyleSheet(f"background-color: {C['border']};")

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font(9, bold=True))
        return lbl

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("func_sep")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        return sep


class LeftPanel(QWidget):
    """左栏面板：Tab切换 + 分组会话列表 + 底部控制 + 主题切换。"""
    session_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 宽度由外部 QSplitter 控制（MainWindow 中设置 min/max）
        self._current_tab = "会话"
        self._groups: list[SessionGroup] = []
        self._all_items: list[SessionItem] = []
        self._active_idx = 0
        self._file_mode = False
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ── Tab 行（SVG: 92×22 rx=6, active=#007acc 未选中=bg_tab 或透明）──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)

        self._func_btn = self._make_tab_btn("功能", active=False)
        self._sess_btn = self._make_tab_btn("会话", active=True)
        self._func_btn.clicked.connect(lambda: self._switch_tab("功能"))
        self._sess_btn.clicked.connect(lambda: self._switch_tab("会话"))

        tab_row.addWidget(self._func_btn, 1)
        tab_row.addWidget(self._sess_btn, 1)
        layout.addLayout(tab_row)

        # ── 工具行（按 Tab 切换）──
        self._tool_stack = QStackedWidget()
        self._tool_stack.setFixedHeight(22)

        # 功能页工具行（SVG ui-left-function.svg line 9-13: 搜索 156×22 + + 30×22）
        func_tools = QWidget()
        ftl = QHBoxLayout(func_tools)
        ftl.setContentsMargins(0, 0, 0, 0)
        ftl.setSpacing(6)
        self._func_search = QLineEdit()
        self._func_search.setPlaceholderText("🔍")
        self._func_search.setFixedSize(156, 22)
        self._func_add = QPushButton("+")
        self._func_add.setFixedSize(30, 22)
        self._func_add.setCursor(Qt.PointingHandCursor)
        self._func_add.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['accent']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        ftl.addWidget(self._func_search)
        ftl.addWidget(self._func_add)
        ftl.addStretch()
        self._tool_stack.addWidget(func_tools)

        # 会话页工具行（SVG ui-full-dark.svg line 18-23: 28×22 / 124×22 / 28×22）
        sess_tools = QWidget()
        stl = QHBoxLayout(sess_tools)
        stl.setContentsMargins(0, 0, 0, 0)
        stl.setSpacing(6)
        self._search_btn = self._make_small_btn("🔍", 28, 22, C["text_secondary"], 10)
        self._new_btn = self._make_new_btn()
        self._more_btn = self._make_small_btn("...", 28, 22, C["text_muted"], 11)
        stl.addWidget(self._search_btn)
        stl.addWidget(self._new_btn, 1)  # 新会话按钮自适应剩余宽度
        stl.addWidget(self._more_btn)

        # 搜索框（初始隐藏，点击🔍后展开占满 new_btn + more_btn 宽度）
        self._search_input = QLineEdit()
        self._search_input.setFixedHeight(22)
        self._search_input.setPlaceholderText("搜索会话...")
        self._search_input.hide()
        stl.addWidget(self._search_input, 1)

        # 搜索关闭按钮（初始隐藏）
        self._search_close = self._make_small_btn("✕", 28, 22, C["text_muted"], 10)
        self._search_close.hide()
        stl.addWidget(self._search_close)

        self._search_btn.clicked.connect(self._toggle_search)
        self._search_close.clicked.connect(self._close_search)
        self._more_btn.clicked.connect(self._on_more_clicked)

        self._tool_stack.addWidget(sess_tools)

        layout.addWidget(self._tool_stack)

        # 工具行下分隔线（SVG: y=76）
        self._sep1 = QFrame()
        self._sep1.setFrameShape(QFrame.HLine)
        self._sep1.setFixedHeight(1)
        layout.addWidget(self._sep1)

        # ── 内容区（QStackedWidget：功能页 / 会话列表）──
        self._stack = QStackedWidget()

        # 功能页
        func_page = FunctionPage()
        self._stack.addWidget(func_page)

        # 会话列表（可滚动）
        self._sess_scroll = QScrollArea()
        self._sess_scroll.setWidgetResizable(True)
        self._sess_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sess_widget = QWidget()
        sess_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sess_widget.setMinimumWidth(1)
        self._sess_layout = QVBoxLayout(sess_widget)
        self._sess_layout.setContentsMargins(0, 0, 0, 0)
        self._sess_layout.setSpacing(6)
        self._sess_layout.addStretch()
        self._sess_scroll.setWidget(sess_widget)
        self._stack.addWidget(self._sess_scroll)

        # 文件管理器页面（索引 2）
        self._file_page = QWidget()
        fpl = QVBoxLayout(self._file_page)
        fpl.setContentsMargins(6, 4, 6, 4)
        fpl.setSpacing(6)
        path_row = QHBoxLayout()
        path_row.setSpacing(6)
        self._file_back_btn = QPushButton("←")
        self._file_back_btn.setFixedSize(28, 22)
        self._file_back_btn.setCursor(Qt.PointingHandCursor)
        self._file_path_lbl = QLabel("agent_workbench")
        self._file_path_lbl.setFont(font(10))
        self._file_path_lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        path_row.addWidget(self._file_back_btn)
        path_row.addWidget(self._file_path_lbl, 1)
        fpl.addLayout(path_row)
        self._file_list = QListWidget()
        self._file_list.addItems(["📁 agent_engine", "📁 core", "📁 services", "📁 ui", "📁 v4", "📁 experiments"])
        self._file_list.addItems(["📄 main.py", "📄 requirements.txt", "📄 README.md", "📄 CHANGELOG.md"])
        self._file_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; color: {C['text_primary']}; font-size: 11px; }}"
            f"QListWidget::item {{ padding: 4px 8px; border-radius: 4px; }}"
            f"QListWidget::item:hover {{ background: {C['bg_hover']}; }}"
        )
        fpl.addWidget(self._file_list)
        self._stack.addWidget(self._file_page)

        self._stack.setCurrentIndex(1)
        layout.addWidget(self._stack, 1)

        # ── 底部控制（SVG: 分隔线 y=700 + 主题/设置按钮 h=12）──
        self._sep2 = QFrame()
        self._sep2.setFrameShape(QFrame.HLine)
        self._sep2.setFixedHeight(1)
        layout.addWidget(self._sep2)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        self._theme_btn = self._make_bottom_btn("🌙")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._settings_btn = self._make_bottom_btn("⚙")
        bottom_row.addWidget(self._theme_btn)
        bottom_row.addWidget(self._settings_btn)
        bottom_row.addStretch()
        layout.addLayout(bottom_row)

        # 填充 Demo 会话数据
        self._populate_sessions()

        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_sidebar']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        self._sep2.setStyleSheet(f"background-color: {C['border']};")
        # Tab 按钮恢复背景框 + 文字颜色
        for btn, active in [(self._func_btn, self._current_tab == "功能"),
                             (self._sess_btn, self._current_tab == "会话")]:
            bg = C["accent"] if active else C["btn_bg"]
            fg = C["text_inverse"] if active else C["text_secondary"]
            fw = 600 if active else 500
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )
        self._sess_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {C['bg_sidebar']}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}"
        )
        # 功能页搜索框
        self._func_search.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 0 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border: 0.5px solid {C['accent']}; }}"
        )
        # 功能页 + 按钮
        self._func_add.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['accent']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        # 会话页工具行三按钮
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 10px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._new_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._more_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_muted']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        # 搜索输入框 & 关闭按钮（主题适配）
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; padding: 2px 8px; font-size: 11px; }}"
        )
        self._search_close.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_muted']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 10px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        # 底部按钮
        self._theme_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._settings_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        # 刷新当前 Tab 按钮样式
        self._switch_tab(self._current_tab)

    def _toggle_theme(self):
        new_theme = "light" if theme.name == "dark" else "dark"
        theme.set_theme(new_theme)
        self._theme_btn.setText("☀️" if new_theme == "light" else "🌙")

    def _make_tab_btn(self, text: str, active: bool) -> QPushButton:
        """Tab 标签：SVG 92×22 rx=6 背景框，active=accent/#fff，inactive=btn_bg/text_secondary。"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(92, 22)
        bg = C["accent"] if active else C["btn_bg"]
        fg = C["text_inverse"] if active else C["text_secondary"]
        fw = 600 if active else 500
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: {fg}; "
            f"border: none; border-radius: 6px; padding: 2px 8px; "
            f"font-size: 11px; font-weight: {fw}; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
        return btn

    def _make_small_btn(self, text: str, w: int, h: int, color: str = None, font_size: int = 10) -> QPushButton:
        """小图标按钮（SVG ui-full-dark.svg line 18-23）：bg_primary 背景 + border 边框圆角卡片。"""
        btn = QPushButton(text)
        btn.setFixedSize(w, h)
        btn.setCursor(Qt.PointingHandCursor)
        fg = color if color else C["text_secondary"]
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {fg}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: {font_size}px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _make_new_btn(self) -> QPushButton:
        """新会话按钮：bg_primary + accent 边框，宽度自适应左侧栏。"""
        btn = QPushButton("+ 新会话")
        btn.setMinimumWidth(80)
        btn.setFixedHeight(22)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_primary']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _make_bottom_btn(self, text: str) -> QPushButton:
        """底部小标签（SVG ui-full-dark.svg line 70-73）：btn_bg 背景、text_secondary 字。"""
        btn = QPushButton(text)
        btn.setFixedSize(32, 12)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 6px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def _switch_tab(self, tab: str):
        self._current_tab = tab
        is_func = (tab == "功能")
        self._file_mode = False
        self._stack.setCurrentIndex(0 if is_func else 1)
        self._tool_stack.setCurrentIndex(0 if is_func else 1)
        self._func_btn.setChecked(is_func)
        self._sess_btn.setChecked(not is_func)
        for btn, active in [(self._func_btn, is_func), (self._sess_btn, not is_func)]:
            bg = C["accent"] if active else C["btn_bg"]
            fg = C["text_inverse"] if active else C["text_secondary"]
            fw = 600 if active else 500
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {fg}; "
                f"border: none; border-radius: 6px; padding: 2px 8px; "
                f"font-size: 11px; font-weight: {fw}; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )

    def _toggle_search(self):
        """展开/收起会话搜索框"""
        if self._new_btn.isVisible():
            self._new_btn.hide()
            self._more_btn.hide()
            self._search_input.show()
            self._search_close.show()
            self._search_input.setFocus()
        else:
            self._close_search()

    def _close_search(self):
        """关闭搜索框，恢复工具行"""
        self._search_input.clear()
        self._search_input.hide()
        self._search_close.hide()
        self._new_btn.show()
        self._more_btn.show()

    def _on_more_clicked(self):
        """切换文件管理器 / 会话列表"""
        if self._file_mode:
            self._file_mode = False
            self._stack.setCurrentIndex(1)
        else:
            self._file_mode = True
            self._stack.setCurrentIndex(2)

    def _populate_sessions(self):
        """填充 Demo 分组会话数据（对应 SVG 设计稿）。"""
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
        for g in reversed(self._groups):
            self._sess_layout.insertWidget(self._sess_layout.count() - 1, g)
        for g in self._groups:
            g.session_clicked.connect(self._on_session_clicked)
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
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class UserBubble(ChatItem):
    """SVG: x=240 y=56 w=148 h=26 rx=8 fill=#007acc, text x=365 text-anchor=end"""
    PAD_X = 12.0
    PAD_Y = 8.0
    RIGHT_PAD = 14.0

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fnt = font(11)
        max_text_w = max(40.0, ChatScene.CONTENT_W - 2 * self.PAD_X)
        tw, th = _wrap_text_size(text, fnt, max_text_w)
        bw = max(60.0, min(float(ChatScene.CONTENT_W), tw + 2 * self.PAD_X))
        bh = th + 2 * self.PAD_Y
        bx = ChatScene.CHAT_W - self.RIGHT_PAD - bw
        self._brect = QRectF(bx, 0, bw, bh)
        self._trect = QRectF(bx + self.PAD_X, self.PAD_Y, bw - 2 * self.PAD_X, th)
        self._h = bh + 8
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self._brect, 8, 8)
        painter.fillPath(path, qcolor(C["accent"]))
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_inverse"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        to.setAlignment(Qt.AlignRight)
        painter.drawText(self._trect, self._text, to)


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
            # 外层卡片（dark bg_card #16213e; light bg_card #ffffff）
            outer = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H + self._body_h)
            p = QPainterPath()
            p.addRoundedRect(outer, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))

            # Header bar
            hr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H)
            hp = QPainterPath()
            hp.addRoundedRect(hr, self.RX, self.RX)
            hp.addRect(ChatScene.LEFT_MARGIN, y0 + self.HEADER_H - self.RX, ChatScene.CONTENT_W, self.RX)
            painter.fillPath(hp, qcolor(C["bg_darker"]))

            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 10, y0 + 10, down=True)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)
        else:
            fr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.FOLD_H)
            p = QPainterPath()
            p.addRoundedRect(fr, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))
            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 12, y0 + 11, down=False)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)

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
            hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
            if hr.contains(event.pos()):
                self.toggle()
                event.accept()
                return
        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
        self.setCursor(Qt.PointingHandCursor if hr.contains(event.pos()) else Qt.ArrowCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class ToolEntry(ChatItem):
    """SVG: 4px左bar + ✓ + 工具名 + 耗时 + ▶参数"""
    def __init__(self, name: str, elapsed: str, success: bool = True, parent=None):
        super().__init__(parent)
        self._name = name
        self._elapsed = elapsed
        self._icon = "✓" if success else "✗"
        self._success = success
        self._h = 16
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 1.0
        # 4px bar（SVG dark #2a2a4a=border; light #e9ecef=bg_sidebar）
        bar_color = C["border"] if theme.name == "dark" else C["bg_sidebar"]
        br = QRectF(ChatScene.LEFT_MARGIN + 10, y, 4, 14)
        bp = QPainterPath()
        bp.addRoundedRect(br, 2, 2)
        painter.fillPath(bp, qcolor(bar_color))
        # icon：运行时读取当前主题色，避免实例化时固定深色
        icon_color = C["green"] if self._success else "#f14c4c"
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(icon_color))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 22, y + 11), self._icon)
        # name
        painter.setPen(qcolor(C["mono_text"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 33, y + 11), self._name)
        # elapsed
        painter.setFont(mono_font(9))
        painter.setPen(qcolor(C["text_muted"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 134, y + 11), self._elapsed)
        # args chevron
        painter.setPen(qcolor(C["accent_blue"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 189, y + 11), "▶ 参数")


class PhasePanel(ChatItem):
    """阶段面板：rx=8卡片 + 4px accent bar + header + body（body 自动垂直堆叠）。"""
    HEADER_H = 24.0
    RX = 8.0
    BODY_TOP = 8.0
    # 颜色键（避免类定义时捕获固定颜色）
    PHASE_COLORS = {
        "analyze": "accent_blue", "execute": "yellow",
        "archive": "green", "verify": "purple",
    }

    def __init__(self, title: str, accent_key: str, body_items: list = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._accent_key = accent_key
        self._body_items = body_items or []
        # 自动布局 body items 并计算总高度
        y = self.HEADER_H + self.BODY_TOP
        for item in self._body_items:
            item.setParentItem(self)
            item.setPos(ChatScene.LEFT_MARGIN, y)
            y += item.height() + 6
        self._body_h = max(0.0, y - self.HEADER_H - self.BODY_TOP)
        self._h = self.HEADER_H + self._body_h + 16

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4.0
        card_h = self.HEADER_H + self._body_h + 8

        # 卡片（dark bg_sidebar #16213e; light bg_card #ffffff）
        cr = QRectF(ChatScene.LEFT_MARGIN, y, ChatScene.CONTENT_W, card_h)
        cp = QPainterPath()
        cp.addRoundedRect(cr, self.RX, self.RX)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        pen = QPen(qcolor(C["border"]), 0.5)
        painter.setPen(pen)
        painter.drawPath(cp)

        # accent bar：运行时读取当前主题色
        accent = C.get(self._accent_key, C["accent_blue"])
        ar = QRectF(ChatScene.LEFT_MARGIN, y, 4, card_h)
        ap = QPainterPath()
        ap.addRoundedRect(ar, 2, 2)
        painter.fillPath(ap, qcolor(accent))

        # header
        hr = QRectF(ChatScene.LEFT_MARGIN + 4, y, ChatScene.CONTENT_W - 4, self.HEADER_H)
        hp = QPainterPath()
        hp.addRoundedRect(hr, 6, 6)
        hp.addRect(ChatScene.LEFT_MARGIN + 4, y + self.HEADER_H - 6, ChatScene.CONTENT_W - 4, 6)
        painter.fillPath(hp, qcolor(C["bg_darker"]))
        painter.setPen(qcolor(C["text_primary"]))
        painter.setFont(font(12, bold=True))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 14, y + 17), self._title)


class BulletItem(ChatItem):
    """● + 文本（自动换行）"""
    INDENT = 23.0
    TOP = 14.0

    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        fnt = font(10)
        max_w = max(40.0, ChatScene.CONTENT_W - self.INDENT - 10)
        _, th = _wrap_text_size(text, fnt, max_w)
        self._h = max(20.0, th + 10)
        self._text_rect = QRectF(ChatScene.LEFT_MARGIN + self.INDENT, 4, max_w, th)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        color = qcolor(C[self._color_key])
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(ChatScene.LEFT_MARGIN + 13, self.TOP), 3, 3)
        painter.setFont(font(10))
        painter.setPen(color)
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._text_rect, self._text, to)


class StepItem(ChatItem):
    """执行步骤：✓/⟳/○ + 名称 + 详情（自动换行）"""
    ICONS = {"done": ("✓", "green"), "running": ("⟳", "yellow"),
             "pending": ("○", "text_muted"), "fail": ("✗", "#f14c4c")}
    ICON_X = 14.0
    TEXT_X = 29.0

    def __init__(self, status: str, name: str, detail: str = "", parent=None):
        super().__init__(parent)
        self._icon, self._ic_key = self.ICONS.get(status, ("○", "text_muted"))
        self._name = name
        self._detail = detail
        name_fnt = font(10)
        detail_fnt = font(9)
        max_w = max(40.0, ChatScene.CONTENT_W - self.TEXT_X - 10)
        _, name_h = _wrap_text_size(name, name_fnt, max_w)
        self._name_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 4, max_w, name_h)
        if detail:
            _, detail_h = _wrap_text_size(detail, detail_fnt, max_w)
            self._detail_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 6 + name_h, max_w, detail_h)
            self._h = max(20.0, 6 + name_h + detail_h + 6)
        else:
            self._detail_rect = None
            self._h = max(20.0, name_h + 10)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        # 图标颜色运行时解析
        ic = C.get(self._ic_key, C["text_muted"]) if self._ic_key.startswith("#") is False else self._ic_key
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(ic))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + self.ICON_X, 16), self._icon)
        painter.setFont(font(10))
        painter.setPen(qcolor(C["text_primary"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._name_rect, self._name, to)
        if self._detail_rect:
            painter.setFont(font(9))
            painter.setPen(qcolor(C["text_muted"]))
            painter.drawText(self._detail_rect, self._detail, to)


class TextItem(ChatItem):
    """纯文本块（自动换行）。"""
    TEXT_X = 14.0

    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        fnt = font(10)
        max_w = max(40.0, ChatScene.CONTENT_W - self.TEXT_X - 10)
        _, th = _wrap_text_size(text, fnt, max_w)
        self._h = max(22.0, th + 10)
        self._text_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 4, max_w, th)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(font(10))
        painter.setPen(qcolor(C[self._color_key]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._text_rect, self._text, to)


class SystemCard(ChatItem):
    """居中系统卡片（支持自动换行）。"""
    PAD_X = 14.0
    PAD_Y = 10.0

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fnt = font(11)
        max_text_w = max(40.0, ChatScene.CONTENT_W - 2 * self.PAD_X)
        tw, th = _wrap_text_size(text, fnt, max_text_w)
        cw = min(ChatScene.CONTENT_W, tw + 2 * self.PAD_X)
        ch = th + 2 * self.PAD_Y
        self._crect = QRectF((ChatScene.CHAT_W - cw) / 2, 4, cw, ch)
        self._text_rect = QRectF(self._crect.left() + self.PAD_X, self._crect.top() + self.PAD_Y,
                                 cw - 2 * self.PAD_X, th)
        self._h = ch + 8

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        cp = QPainterPath()
        cp.addRoundedRect(self._crect, 8, 8)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        painter.setPen(QPen(qcolor(C["border"]), 0.5))
        painter.drawPath(cp)
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_primary"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        to.setAlignment(Qt.AlignCenter)
        painter.drawText(self._text_rect, self._text, to)


# ══════════════════════════════════════════════════════════════
# 聊天场景
# ══════════════════════════════════════════════════════════════

def _wrap_text_size(text: str, fnt: QFont, max_w: float, line_spacing: int = 2) -> tuple[float, float]:
    """计算文本在指定最大宽度下自动换行后的包围盒尺寸。"""
    fm = QFontMetrics(fnt)
    rect = fm.boundingRect(QRect(0, 0, max(1, int(max_w)), 1000000), Qt.TextWordWrap, text)
    # boundingRect 返回的是 tight rect，实际行高用 fm.height()
    lines = max(1, int(rect.height() / fm.height() + 0.5))
    h = lines * fm.height() + (lines - 1) * line_spacing
    return rect.width(), h


class ChatScene(QGraphicsScene):
    CHAT_W = 402
    LEFT_MARGIN = 20
    CONTENT_W = 362

    @classmethod
    def set_width(cls, w: float):
        cls.CHAT_W = w
        cls.CONTENT_W = max(120.0, w - 40)

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
        self.setSceneRect(QRectF(0, 0, ChatScene.CHAT_W, h))

    def clear_items(self):
        super().clear()
        self._items.clear()
        self._y = 8.0

    def refresh(self):
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))
        for item in self._items:
            item.update()


# ══════════════════════════════════════════════════════════════
# MoreDropdown — "..." 按钮下拉面板（进度 + 文件）
# ══════════════════════════════════════════════════════════════
class MoreDropdown(QWidget):
    WIDTH = 260
    CORNER = 8

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

        # 步骤列表
        for s, t in [("✓", "v4 架构升级 已完成"), ("✓", "代码片段咨询 已完成"), ("○", "量化策略回测 进行中")]:
            row = QHBoxLayout()
            row.setSpacing(6)
            icon = QLabel(s)
            icon.setFont(font(9))
            icon.setStyleSheet(f"color: {C['accent']}; background: transparent;")
            lbl = QLabel(t)
            lbl.setFont(font(9))
            lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
            row.addWidget(icon)
            row.addWidget(lbl, 1)
            layout.addLayout(row)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"color: {C['border']};")
        layout.addWidget(sep)

        # 文件区
        file_hdr = QLabel("📁 文件 (5)")
        file_hdr.setFont(font(11, bold=True))
        file_hdr.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        layout.addWidget(file_hdr)

        for f in ["📄 main.py", "📄 requirements.txt", "📄 CHANGELOG.md", "📁 agent_engine/", "📁 experiments/"]:
            lbl = QLabel(f)
            lbl.setFont(font(10))
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
            layout.addWidget(lbl)

        self.setFixedHeight(258)
        self.hide()

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
    left_expand_toggled = Signal()
    expand_toggled = Signal()
    search_clicked = Signal()
    more_clicked = Signal()
    double_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧折叠按钮（与右侧对称）
        self._left_expand_btn = self._icon_btn("折叠左侧面板")
        self._left_expand_btn.clicked.connect(self.left_expand_toggled.emit)
        layout.addWidget(self._left_expand_btn)
        layout.addSpacing(4)

        # 双行标题（SVG: title y=16, env y=30）
        title_block = QVBoxLayout()
        title_block.setContentsMargins(6, 4, 0, 4)
        title_block.setSpacing(2)

        self._title_lbl = QLabel("v4 架构升级")
        self._title_lbl.setFont(font(12))
        title_block.addWidget(self._title_lbl)

        self._env_lbl = QLabel("F:\\Agent\\agent_workbench")
        self._env_lbl.setFont(font(10))
        title_block.addWidget(self._env_lbl)
        layout.addLayout(title_block, 1)

        # 垂直分隔线（SVG: x1=331）
        self._vsep = QLabel()
        self._vsep.setFixedSize(1, 24)
        layout.addWidget(self._vsep)
        layout.addSpacing(6)

        # 搜索输入栏（初始隐藏，点击🔍展开，位于分隔线与按钮区之间）
        self._search_input = QLineEdit()
        self._search_input.setFixedHeight(24)
        self._search_input.setPlaceholderText("搜索会话内容...")
        self._search_input.hide()
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_card']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; padding: 2px 8px; font-size: 11px; }}"
        )
        layout.addWidget(self._search_input, 1)

        self._search_close = QPushButton("✕")
        self._search_close.setFixedSize(20, 22)
        self._search_close.setCursor(Qt.PointingHandCursor)
        self._search_close.hide()
        self._search_close.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {C['text_muted']}; "
            f"border: none; font-size: 10px; }}"
            f"QPushButton:hover {{ color: {C['text_primary']}; }}"
        )
        layout.addWidget(self._search_close)

        self._btn_block = QWidget()
        btn_hl = QHBoxLayout(self._btn_block)
        btn_hl.setContentsMargins(0, 0, 0, 0)
        btn_hl.setSpacing(8)  # 拉开按钮间隔

        self._search_btn = self._icon_btn("搜索")
        self._search_btn.clicked.connect(self.search_clicked.emit)
        self._search_close.clicked.connect(lambda: self.search_clicked.emit())
        self._more_btn = self._icon_btn("更多操作")
        self._more_btn.clicked.connect(self.more_clicked.emit)
        self._expand_btn = self._icon_btn("折叠右侧面板")
        self._expand_btn.clicked.connect(self.expand_toggled.emit)

        btn_hl.addWidget(self._search_btn)
        btn_hl.addWidget(self._more_btn)
        btn_hl.addWidget(self._expand_btn)
        layout.addWidget(self._btn_block)

        layout.addSpacing(12)
        self._refresh_theme()

    def _icon_btn(self, tooltip: str) -> QPushButton:
        """18×22 图标按钮：透明背景，仅保留图标；hover 微亮。"""
        btn = QPushButton()
        btn.setFixedSize(18, 22)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        lbl = QLabel(btn)
        lbl.setObjectName("icon_lbl")
        lbl.move(0, 1)
        return btn

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._title_lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        self._env_lbl.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._vsep.setStyleSheet(f"background-color: {C['border']};")

        # 搜索框 & 文件面板主题
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_card']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['accent']}; border-radius: 6px; padding: 2px 8px; font-size: 11px; }}"
        )

        stroke = C['text_secondary'] if theme.name == "dark" else C['text_label']
        # Apple 风格搜索图标: 偏心圆 + 粗短手柄
        search_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
            <circle cx="8" cy="7.5" r="4.5" fill="none" stroke="{stroke}" stroke-width="1.4"/>
            <line x1="11.2" y1="10.7" x2="15.5" y2="15" stroke="{stroke}" stroke-width="1.8" stroke-linecap="round"/>
        </svg>'''
        more_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
            <circle cx="6" cy="10" r="1.2" fill="{stroke}"/>
            <circle cx="10" cy="10" r="1.2" fill="{stroke}"/>
            <circle cx="14" cy="10" r="1.2" fill="{stroke}"/>
        </svg>'''
        # 左侧折叠图标: 窗格框体 + 左侧纵向分割线
        left_expand_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
            <rect x="2" y="3" width="14" height="12" rx="2" fill="none" stroke="{stroke}" stroke-width="1.5"/>
            <line x1="6" y1="5.5" x2="6" y2="12.5" stroke="{stroke}" stroke-width="1.2" stroke-linecap="round"/>
        </svg>'''
        # 右侧折叠图标: 窗格框体 + 纵向分割线，表达"右侧面板可折叠"
        expand_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
            <rect x="2" y="3" width="14" height="12" rx="2" fill="none" stroke="{stroke}" stroke-width="1.5"/>
            <line x1="12" y1="5.5" x2="12" y2="12.5" stroke="{stroke}" stroke-width="1.2" stroke-linecap="round"/>
        </svg>'''
        for btn, svg in [(self._left_expand_btn, left_expand_svg),
                         (self._search_btn, search_svg),
                         (self._more_btn, more_svg),
                         (self._expand_btn, expand_svg)]:
            lbl = btn.findChild(QLabel, "icon_lbl")
            if lbl:
                lbl.setPixmap(svg_icon(svg, 18, 22))
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; border-radius: 4px; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )

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
# 输入区
# ══════════════════════════════════════════════════════════════

class InputArea(QWidget):
    send_clicked = Signal()

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

        root.addLayout(bottom_row)
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

        chev = QLabel("▾")
        chev.setFont(font(9))
        chev.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(chev)
        hl.addStretch()
        return tag


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
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialized = False
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(80)
        self._rebuild_timer.timeout.connect(self._debounced_rebuild)
        self._setup_ui()
        self._populate_demo()
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
        layout.addWidget(self._header)

        # 标题栏下分隔线（SVG: y=40）
        self._sep1 = QFrame()
        self._sep1.setFixedHeight(1)
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep1)

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

        # "..." 下拉面板（内嵌子控件，跟随主窗口，非独立顶层窗口）
        self._more_dropdown = MoreDropdown(self)
        self._more_dropdown.raise_()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._sep1.setStyleSheet(f"background-color: {C['border']};")
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
        # 下拉面板随窗口 resize 重新定位
        if hasattr(self, '_more_dropdown') and self._more_dropdown.isVisible():
            self._more_dropdown.position_under(self._header._more_btn)
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
        self._scene.clear_items()
        self._populate_demo()
        self._scene.refresh()

    def _toggle_search(self):
        """切换搜索框显隐"""
        if self._header._search_input.isHidden():
            self._header._search_input.show()
            self._header._search_close.show()
            self._header._search_input.setFocus()
        else:
            self._header._search_input.hide()
            self._header._search_close.hide()
            self._header._search_input.clear()

    def _toggle_file_panel(self):
        """点击 ... 切换下拉面板显隐（内嵌子控件，跟随主窗口）。"""
        dd = self._more_dropdown
        if dd.isHidden():
            dd.position_under(self._header._more_btn)
            dd.show()
            dd.raise_()
        else:
            dd.hide()

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
        scene.add_chat_item(PhasePanel("📋 分析结果", "accent_blue", [b1, b2]))

        # 📝 执行计划面板
        s1 = StepItem("done", "修改 v4/events.py", "新增 model 字段")
        s2 = StepItem("running", "修改 v4/main_window.py", "模型下拉框 + 持久化")
        s3 = StepItem("pending", "运行全量测试", "pytest tests/ -v")
        scene.add_chat_item(PhasePanel("📝 执行计划", "yellow", [s1, s2, s3]))

        # ✅ 完成报告面板
        t1 = TextItem("v4.0.5-alpha 存档完成")
        scene.add_chat_item(PhasePanel("✅ 完成报告", "green", [t1]))

        # 滚动到底部
        QTimer.singleShot(100, lambda: self._view.verticalScrollBar().setValue(
            self._view.verticalScrollBar().maximum()))


# ══════════════════════════════════════════════════════════════
# 右栏（400px）
# ══════════════════════════════════════════════════════════════

class TabButton(QWidget):
    """右栏标签按钮：标签文本与关闭圆钮共用同一背景，实现 SVG 中的透明圆框高亮效果。
       SVG: rect rx=6 h=24; close circle r=5 fill=tab_bg 与标签同色。
    """
    clicked = Signal()
    close_clicked = Signal()

    def __init__(self, text: str, width: int, active: bool = False, closable: bool = True, parent=None):
        super().__init__(parent)
        self._text = text
        self._active = active
        self._closable = closable
        self.setMinimumWidth(30)  # 可被压缩，仅保留关闭/文本最小空间
        self.setMaximumHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        self._lbl = QLabel(self._text, self)
        self._lbl.setFont(font(10))
        self._lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._lbl.setStyleSheet("background: transparent;")

        if self._closable:
            self._close = QPushButton("✕", self)
            self._close.setFixedSize(10, 10)
            self._close.setFont(font(9))
            self._close.setCursor(Qt.PointingHandCursor)
            self._close.clicked.connect(self.close_clicked.emit)
        else:
            self._close = None
        self._update_child_geometry()
        self._refresh_style()

    def _update_child_geometry(self):
        w = self.width()
        self._lbl.setGeometry(10, 0, max(10, w - 28), 24)
        if self._close:
            self._close.setGeometry(max(4, w - 17), 7, 10, 10)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_child_geometry()

    def _refresh_style(self):
        is_dark = theme.name == "dark"
        bg = (C["bg_darker"] if is_dark else C["bg_card"]) if self._active else (C["bg_right"] if is_dark else C["bg_darker"])
        fg = C["text_primary"] if self._active else C["text_secondary"]
        fw = 600 if self._active else 500
        self.setStyleSheet(f"TabButton {{ background-color: {bg}; border-radius: 6px; }}")
        self._lbl.setStyleSheet(f"color: {fg}; background: transparent; font-weight: {fw};")
        if self._close:
            self._close.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {C['text_muted']}; "
                f"border-radius: 5px; font-size: 9px; border: none; }}"
                f"QPushButton:hover {{ color: {C['text_primary']}; }}"
            )

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._close is None or not self._close.geometry().contains(event.pos()):
                self.clicked.emit()
        super().mousePressEvent(event)


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 宽度由外部 QSplitter 控制（MainWindow 中设置 min）
        self._active_tab = 0
        self._setup_ui()
        self.setMinimumWidth(120)
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标签栏（SVG dark h=28 fill=#0f1729; light fill=#f1f3f5）──
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(28)
        tb_layout = QHBoxLayout(self._tab_bar)
        tb_layout.setContentsMargins(8, 2, 0, 2)
        tb_layout.setSpacing(0)

        # 标签 + 搜索区域（可随右侧栏宽度压缩/拉伸）
        self._tab_container = QWidget()
        self._tab_container.setMinimumWidth(1)
        self._tab_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tc_layout = QHBoxLayout(self._tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(2)

        # SVG: add btn circle r=7 (d=14) fill=#2a2a4a / #e9ecef
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(14, 14)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tc_layout.addWidget(self._add_btn)

        # 标签按钮（宽度可随容器伸缩）
        tab_defs = [("v4 架构", 86, False), ("终端", 74, True), ("文件编辑器", 100, True), ("浏览器", 74, True)]
        self._tab_btns: list[TabButton] = []
        for i, (name, width, closable) in enumerate(tab_defs):
            btn = TabButton(name, width, active=(i == 0), closable=closable)
            btn.clicked.connect(lambda idx=i: self._switch_tab(idx))
            btn.close_clicked.connect(lambda idx=i: self._on_close_tab(idx))
            tc_layout.addWidget(btn, 1)  # 允许拉伸/压缩
            self._tab_btns.append(btn)

        # SVG: 搜索按钮 x=930 y=6 w=16 h=16 rx=3 fill=#2a2a4a / #e9ecef
        self._search_btn = QPushButton("🔍")
        self._search_btn.setFixedSize(16, 16)
        self._search_btn.setCursor(Qt.PointingHandCursor)
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tc_layout.addSpacing(4)
        tc_layout.addWidget(self._search_btn)

        tb_layout.addWidget(self._tab_container, 1)

        # 窗口控制按钮容器（固定在最右侧，不被拖拽收窄/隐藏）
        self._win_btns = QWidget()
        self._win_btns.setFixedWidth(92)  # 3×28 + 2×2 + 左右留白
        win_hl = QHBoxLayout(self._win_btns)
        win_hl.setContentsMargins(0, 0, 8, 0)
        win_hl.setSpacing(2)
        win_hl.addStretch()
        self._win_hl = win_hl
        tb_layout.addWidget(self._win_btns)

        layout.addWidget(self._tab_bar)

        # 标签栏下分隔线
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep)

        # ── 内容区（QStackedWidget）──
        self._stack = QStackedWidget()

        # Tab0: v4 架构（最近文件）
        self._tab0 = QWidget()
        t0l = QVBoxLayout(self._tab0)
        t0l.setContentsMargins(16, 8, 16, 8)
        t0l.setSpacing(4)

        t0l.addWidget(self._make_section_header("最近文件"))
        self._file_rows: list[QWidget] = []
        for path, t in [("v4/main_window.py", "2h 前"), ("v4/worker.py", "4h 前"),
                         ("agent_engine/engines/prompt_engine.py", "昨天")]:
            row = self._make_file_row(path, t)
            t0l.addWidget(row)
            self._file_rows.append(row)
        t0l.addStretch()
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        self._stack.addWidget(self._tab0)

        # Tab1-3: 占位
        self._placeholders: list[QLabel] = []
        for text in ["终端", "文件编辑器", "浏览器"]:
            lbl = QLabel(f"{text}\n（功能待实现）")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px; background: transparent;")
            self._stack.addWidget(lbl)
            self._placeholders.append(lbl)

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

        # SVG dark: fill=#16213e stroke=#2a2a4a rx=4; light: fill=#f8f9fa stroke=#dee2e6
        row.setStyleSheet(
            f"QWidget {{ background-color: {C['bg_file_row']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
            f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
        )
        return row

    def set_window_buttons(self, minimize_cb, maximize_cb, close_cb):
        """把系统最小化/最大化/关闭按钮嵌入右栏顶部状态栏最右侧，使用SVG图标。"""
        icons = [
            ("M 6 10 L 18 10", minimize_cb),   # 最小化：横线
            # 标准还原框：前后两个重叠矩形
            ("M 7 5 L 16 5 L 16 14 L 7 14 Z M 5 7 L 14 7 L 14 16 L 5 16 Z", maximize_cb),
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
            btn.set_active(i == idx)

    def _on_close_tab(self, idx: int):
        # Demo 关闭逻辑：关闭非首个标签后切回第一个
        if idx > 0 and idx < len(self._tab_btns):
            self._tab_btns[idx].setVisible(False)
            self._switch_tab(0)

    def _refresh_theme(self):
        is_dark = theme.name == "dark"
        tab_bar_bg = C["bg_right"] if is_dark else C["bg_darker"]
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._tab_bar.setStyleSheet(f"background-color: {tab_bar_bg};")
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        for lbl in self._placeholders:
            lbl.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px; background: transparent;")
        icon_fg = C['text_secondary'] if theme.name == "dark" else C['text_label']
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        for row in self._file_rows:
            row.setStyleSheet(
                f"QWidget {{ background-color: {C['bg_file_row']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
                f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 刷新内部 label 颜色
            for child in row.findChildren(QLabel):
                if child.alignment() & Qt.AlignRight:
                    child.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
                else:
                    child.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        # 刷新窗口控制按钮图标颜色
        for btn in self._win_btns.findChildren(QPushButton):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            lbl = btn.findChild(QLabel)
            if lbl:
                # 重新渲染图标（stroke 颜色更新）
                pass  # 图标在主题切换后颜色不变即可，此处省略重渲染
        self._switch_tab(self._active_tab)


# ══════════════════════════════════════════════════════════════
# 主窗口（QSplitter 三栏 + 独立折叠）
# ══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self, worker_mgr=None):
        super().__init__(None, Qt.FramelessWindowHint)
        self.resize(1400, 900)
        self.setMinimumWidth(1200)
        self.setWindowTitle("Agent Workbench")
        self._right_visible = True
        self._drag_pos = None
        self._corner_radius = 8

        # 1. 初始化配置与主题
        self._config = ConfigService(config_path="config/config.yaml")
        self._theme_name = self._config.get("app.theme", theme.name)
        if self._theme_name not in _THEMES:
            self._theme_name = theme.name
        theme.set_theme(self._theme_name)

        # 2. 初始化 v4 核心组件
        self._repo = SessionRepository()
        self._bus = MessageBus(trace=False)
        self._bus.connect_dispatch()

        # 3. 八引擎 + WorkerManager
        self._engines = self._init_engines()
        self._worker_mgr = worker_mgr or WorkerManager(
            message_bus=self._bus,
            parent=self,
        )

        # 4. 会话协调器
        self._orchestrator = SessionOrchestrator(
            repository=self._repo,
            message_bus=self._bus,
            worker_manager=self._worker_mgr,
            parent=self,
        )

        # 5. 设置 UI
        self._setup_ui()

        # 6. UI 渲染器
        self._ui_renderer = UIRenderer(
            message_bus=self._bus,
            chat_view=self._center,
            conversation_list=self._left,
            right_panel=self._right,
            current_session_provider=lambda: self._orchestrator.current_session_id or "",
            parent=self,
        )

        # 7. 草稿窗口状态
        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._current_model_name = self._config.get("app.last_model", "tool-agent")
        self._current_mode = self._config.get("app.last_mode", "ask")

        # 8. 信号连接与默认会话
        self._connect_signals()
        self._init_default_session()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()
        self._update_edge_positions()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)
        install_invisible_handles(self._splitter)  # 启用 4px 透明拖拽热区

        # 左栏：最小 180，最大固定为当前默认值 220
        self._left = LeftPanel()
        self._left.setMinimumWidth(180)
        self._left.setMaximumWidth(220)
        self._splitter.addWidget(self._left)

        # 中栏：最小宽度保证内容可读
        self._center = ChatArea()
        self._center.setMinimumWidth(280)
        self._center._header.left_expand_toggled.connect(self._toggle_left_panel)
        self._center._header.expand_toggled.connect(self._toggle_right_panel)
        self._center._header.double_clicked.connect(self._toggle_maximize)
        self._splitter.addWidget(self._center)

        # 右栏
        self._right = RightPanel()
        self._right.setMinimumWidth(200)
        self._right.set_window_buttons(self.showMinimized, self._toggle_maximize, self.close)
        self._splitter.addWidget(self._right)

        self._splitter.setSizes([220, 404, 400])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)
        ml.addWidget(self._splitter)

        # 全局主题调色板
        theme.changed.connect(self._apply_theme_palette)
        self._apply_theme_palette()

        # 8 个窗口边缘 resize 手柄（startSystemResize 方案）
        from PySide6.QtCore import Qt as QtEdge
        self._edge_widgets = [
            EdgeResizeWidget(QtEdge.TopEdge | QtEdge.LeftEdge,     Qt.SizeFDiagCursor, self.centralWidget()),   # 0 TL
            EdgeResizeWidget(QtEdge.TopEdge,                       Qt.SizeVerCursor,   self.centralWidget()),   # 1 T
            EdgeResizeWidget(QtEdge.TopEdge | QtEdge.RightEdge,    Qt.SizeBDiagCursor, self.centralWidget()),   # 2 TR
            EdgeResizeWidget(QtEdge.LeftEdge,                      Qt.SizeHorCursor,   self.centralWidget()),   # 3 L
            EdgeResizeWidget(QtEdge.RightEdge,                     Qt.SizeHorCursor,   self.centralWidget()),   # 4 R
            EdgeResizeWidget(QtEdge.BottomEdge | QtEdge.LeftEdge,  Qt.SizeBDiagCursor, self.centralWidget()),   # 5 BL
            EdgeResizeWidget(QtEdge.BottomEdge,                    Qt.SizeVerCursor,   self.centralWidget()),   # 6 B
            EdgeResizeWidget(QtEdge.BottomEdge | QtEdge.RightEdge, Qt.SizeFDiagCursor, self.centralWidget()),   # 7 BR
        ]
        self._update_edge_positions()

    def _update_edge_positions(self):
        """根据当前窗口尺寸重新定位 8 个 EdgeResizeWidget。"""
        S = EdgeResizeWidget.SIZE
        W, H = self.width(), self.height()
        tl, t, tr, l, r, bl, b, br = self._edge_widgets
        tl.place(0, 0, S, S)              # 左上角
        t.place(S, 0, W - 2 * S, S)       # 上边
        tr.place(W - S, 0, S, S)          # 右上角
        l.place(0, S, S, H - 2 * S)       # 左边
        r.place(W - S, S, S, H - 2 * S)   # 右边
        bl.place(0, H - S, S, S)          # 左下角
        b.place(S, H - S, W - 2 * S, S)   # 下边
        br.place(W - S, H - S, S, S)      # 右下角

    def _on_splitter_moved(self, pos: int, index: int):
        """QSplitter 拖拽后重建聊天内容，使气泡/面板适配新宽度。"""
        QTimer.singleShot(0, self._center._rebuild_content)

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

    def _apply_theme_palette(self):
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

    # ── 八引擎初始化 ──────────────────────────────
    def _init_engines(self) -> dict:
        from agent_engine.llm_registry import LLMRegistry
        from agent_engine.engines import (
            PromptEngine, InferenceEngine, ToolEngine,
            MemoryEngine, MetricsEngine, PolicyEngine,
        )
        config = self._config.config if self._config else {}
        registry = LLMRegistry("config/config.yaml", "config/config.yaml")
        policy = PolicyEngine(config.get("ai_engine", {}))
        metrics = MetricsEngine()
        engines = {
            "registry": registry, "policy": policy, "metrics": metrics,
            "prompt": PromptEngine(
                base_prompts={m: c.get("system_prompt", "") for m, c in config.get("manual_modes", {}).items()},
                user_rules=config.get("user_rules", []),
                app_version=config.get("app", {}).get("version", "v5.0"),
            ),
            "inference": InferenceEngine(policy_engine=policy, metrics_engine=metrics, llm_registry=registry),
            "tool": ToolEngine(),
            "memory": MemoryEngine(
                app_root=_get_app_root(),
                config=config.get("self_context", {}), policy_engine=policy,
            ),
        }
        return engines

    def _connect_signals(self):
        """连接新 UI 控件信号到 v4 事件槽（逐步填充）。"""
        # P2 阶段先保持最小连接，避免引用不存在的 API
        pass

    def _init_default_session(self):
        """启动时进入草稿窗口状态，不自动创建 DB 会话。"""
        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._orchestrator.clear_current() if hasattr(self._orchestrator, "clear_current") else None

    def _get_project_path(self) -> str:
        """获取当前项目路径（当前可返回空字符串）。"""
        return ""

    def _toggle_left_panel(self):
        """切换左侧面板显示/隐藏，中间聊天区自动延伸/收缩。"""
        if self._left.isVisible():
            self._left.hide()
            total = self.width()
            rw = self._right.width() if self._right_visible else 0
            self._splitter.setSizes([0, total - rw, rw])
        else:
            self._left.show()
            rw = 400 if self._right_visible else 0
            self._splitter.setSizes([220, self.width() - 220 - rw, rw])
        QApplication.processEvents()
        self._center._rebuild_content()

    def _toggle_right_panel(self):
        """切换右侧面板显示/隐藏，中间聊天区自动延伸/收缩。"""
        if self._right_visible:
            self._right.hide()
            total = self.width()
            self._splitter.setSizes([220, total - 220, 0])
            self._right_visible = False
        else:
            self._right.show()
            self._splitter.setSizes([220, 404, 400])
            self._right_visible = True
        QApplication.processEvents()
        self._center._rebuild_content()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Workbench UI Template")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
