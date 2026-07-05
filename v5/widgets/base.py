"""v5 UI 基础主题与工具组件。"""
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

V5_THEMES = {
    "dark": {
        "bg_primary":        "#0E101A",
        "bg_sidebar":        "#131629",
        "bg_right":          "#0B0D18",
        "bg_darker":         "#0B0D18",
        "bg_card":           "#161A2E",
        "bg_card_selected":  "#1E2342",
        "bg_file_row":       "#161A2E",
        "bg_input":          "#161A2E",
        "bg_tab_active":     "#0E101A",
        "accent":            "#2578E6",
        "accent_blue":       "#4A9DFF",
        "accent_light":      "#1E3A5F",
        "border":            "#222842",
        "text_primary":      "#F0F2F8",
        "text_secondary":    "#B0B8D4",
        "text_muted":        "#646E90",
        "text_inverse":      "#FFFFFF",
        "text_label":        "#646E90",
        "green":             "#3DD598",
        "yellow":            "#F4D03F",
        "mono_text":         "#D8DCEA",
        "tag_bg":            "#1E3A5F",
        "gray":              "#646E90",
        "purple":            "#A259FF",
        "btn_bg":            "#222842",
        "btn_hover":         "#2D3352",
        "bg_hover":          "#2D3352",
        "bg_selected":       "#1E2342",
        "window_shadow":     "#000000",
        "send_btn":          "#2578E6",
        "send_btn_hover":    "#4A9DFF",
        "stop_btn":          "#E5484D",
        "stop_btn_hover":    "#FF6B6B",
        "tag_text":          "#B0B8D4",
    },
    "light": {
        "bg_primary":        "#F6F8FF",
        "bg_sidebar":        "#E9EDFB",
        "bg_right":          "#FFFFFF",
        "bg_darker":         "#EEF1FC",
        "bg_card":           "#FFFFFF",
        "bg_card_selected":  "#E1E8FF",
        "bg_file_row":       "#F6F8FF",
        "bg_input":          "#FFFFFF",
        "bg_tab_active":     "#FFFFFF",
        "accent":            "#2578E6",
        "accent_blue":       "#1C6FDD",
        "accent_light":      "#E1E8FF",
        "border":            "#D0D8F0",
        "text_primary":      "#111836",
        "text_secondary":    "#4A5378",
        "text_muted":        "#8690B2",
        "text_inverse":      "#FFFFFF",
        "text_label":        "#8690B2",
        "green":             "#1A936F",
        "yellow":            "#B38600",
        "mono_text":         "#111836",
        "tag_bg":            "#E1E8FF",
        "gray":              "#8690B2",
        "purple":            "#7C3AED",
        "btn_bg":            "#E9EDFB",
        "btn_hover":         "#DDE3F7",
        "bg_hover":          "#E9EDFB",
        "bg_selected":       "#E1E8FF",
        "window_shadow":     "#ADB5BD",
        "send_btn":          "#2578E6",
        "send_btn_hover":    "#1C6FDD",
        "stop_btn":          "#E5484D",
        "stop_btn_hover":    "#C23A3E",
        "tag_text":          "#4A5378",
    },
}


class ThemeManager(QObject):
    """全局主题管理器。切换主题时发出 changed 信号。"""
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._name = "dark"
        self.C = dict(V5_THEMES[self._name])

    def set_theme(self, name: str):
        if name == self._name or name not in V5_THEMES:
            return
        self._name = name
        self.C.clear()
        self.C.update(V5_THEMES[name])
        self.changed.emit(name)

    @property
    def name(self) -> str:
        return self._name


theme = ThemeManager()
C = theme.C


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


class InvisibleResizeHandle(QWidget):
    """透明拖拽热区控件 —— 放置在 QSplitter handle 位置，提供更宽的交互区域。"""
    HOT_ZONE_WIDTH: int = 4

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
        else:
            center_y = handle_rect.center().y()
            half_h = self.HOT_ZONE_WIDTH // 2
            x = 0
            y = max(0, center_y - half_h)
            w = splitter_rect.width()
            h = self.HOT_ZONE_WIDTH
        self.setGeometry(x, y, w, h)
        self.raise_()
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_pos = event.position().toPoint()
            self._start_sizes = list(self._splitter.sizes())
            self._start_global = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._start_global
            sizes = list(self._start_sizes)
            if self._is_horizontal:
                delta_px = delta.x()
            else:
                delta_px = delta.y()
            if self._handle_index < len(sizes):
                sizes[self._handle_index] = max(0, sizes[self._handle_index] + delta_px)
                if self._handle_index + 1 < len(sizes):
                    sizes[self._handle_index + 1] = max(0, sizes[self._handle_index + 1] - delta_px)
                self._splitter.setSizes(sizes)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._start_pos = None
        self._start_sizes = []
        self._start_global = None
        super().mouseReleaseEvent(event)
