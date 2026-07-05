"""v4 UI 基础主题与工具组件。"""
from PySide6.QtWidgets import (
    QApplication, QWidget, QSplitter, QLabel, QPushButton,
    QGraphicsItem, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPointF, QPoint, QSize, QTimer, QObject, QEvent
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPalette, QIcon, QPixmap, QLinearGradient, QCursor, QTextOption,
)
import PySide6.QtWidgets as QtW

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
        # 兼容旧 UI 组件（v4/input_area.py、v4/right_panel.py）的测试
        "send_btn":          "#007acc",
        "send_btn_hover":    "#569cd6",
        "stop_btn":          "#dc3545",
        "stop_btn_hover":    "#ff4d5e",
        "tag_text":          "#a0a0b0",
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
        # 兼容旧 UI 组件（v4/input_area.py、v4/right_panel.py）的测试
        "send_btn":          "#007acc",
        "send_btn_hover":    "#005fa3",
        "stop_btn":          "#dc3545",
        "stop_btn_hover":    "#bb2d3b",
        "tag_text":          "#495057",
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

