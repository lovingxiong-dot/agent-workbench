"""V5 窗口框架与菜单组件。"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QEvent
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QCursor
from .base import theme, V5_THEMES, C, font, qcolor, svg_icon
import PySide6.QtWidgets as QtW

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

