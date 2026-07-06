"""v6/ui/base.py — V6 主题系统与基础 UI 工具。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

import sys
from typing import List

from PySide6.QtCore import Qt, Signal, QObject, QEvent, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QCursor
from PySide6.QtWidgets import QApplication, QSplitter, QWidget, QVBoxLayout


V6_THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_sidebar": "#16213e",
        "bg_right": "#0f1729",
        "bg_darker": "#1a1a2e",
        "bg_card": "#16213e",
        "bg_card_selected": "#0f3460",
        "bg_file_row": "#16213e",
        "bg_input": "#16213e",
        "bg_tab_active": "#1a1a2e",
        "accent": "#007acc",
        "accent_blue": "#569cd6",
        "accent_light": "#0f3460",
        "border": "#2a2a4a",
        "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0b0",
        "text_muted": "#6a6a8a",
        "text_inverse": "#ffffff",
        "text_label": "#6a6a8a",
        "green": "#4ec9b0",
        "yellow": "#dcdcaa",
        "mono_text": "#d4d4d4",
        "tag_bg": "#0f3460",
        "gray": "#858585",
        "purple": "#c586c0",
        "btn_bg": "#2a2a4a",
        "btn_hover": "#3a3a5a",
        "bg_hover": "#2a2a4a",
        "bg_selected": "#0f3460",
        "window_shadow": "#000000",
    },
    "light": {
        "bg_primary": "#f8f9fa",
        "bg_sidebar": "#e9ecef",
        "bg_right": "#ffffff",
        "bg_darker": "#f1f3f5",
        "bg_card": "#ffffff",
        "bg_card_selected": "#e7f1ff",
        "bg_file_row": "#f8f9fa",
        "bg_input": "#ffffff",
        "bg_tab_active": "#ffffff",
        "accent": "#007acc",
        "accent_blue": "#007acc",
        "accent_light": "#e7f1ff",
        "border": "#dee2e6",
        "text_primary": "#212529",
        "text_secondary": "#495057",
        "text_muted": "#adb5bd",
        "text_inverse": "#ffffff",
        "text_label": "#6c757d",
        "green": "#198754",
        "yellow": "#856404",
        "mono_text": "#212529",
        "tag_bg": "#e7f1ff",
        "gray": "#adb5bd",
        "purple": "#7952b3",
        "btn_bg": "#e9ecef",
        "btn_hover": "#dee2e6",
        "bg_hover": "#e9ecef",
        "bg_selected": "#e7f1ff",
        "window_shadow": "#adb5bd",
    },
}


class ThemeManager(QObject):
    """全局主题管理器。切换主题时发出 changed(str) 信号。"""
    changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._name = "dark"
        self.C: dict = dict(V6_THEMES[self._name])

    def set_theme(self, name: str) -> None:
        if name == self._name or name not in V6_THEMES:
            return
        self._name = name
        self.C.clear()
        self.C.update(V6_THEMES[name])
        self.changed.emit(name)

    @property
    def name(self) -> str:
        return self._name


theme = ThemeManager()
C = theme.C


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


class InvisibleResizeHandle(QWidget):
    """QSplitter 透明拖拽热区：视觉 1px，交互 HOT_ZONE_WIDTH px。"""

    HOT_ZONE_WIDTH: int = 4

    def __init__(self, splitter: QSplitter, handle_index: int, parent: QWidget | None = None):
        super().__init__(parent or splitter)
        self._splitter = splitter
        self._handle_index = handle_index
        self._is_horizontal = splitter.orientation() == Qt.Orientation.Horizontal
        self._dragging = False
        self._start_global = None
        self._start_sizes: List[int] = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(
            QCursor(Qt.CursorShape.SizeHorCursor if self._is_horizontal else Qt.CursorShape.SizeVerCursor)
        )
        self._update_geometry()
        splitter.splitterMoved.connect(self._on_splitter_moved)
        splitter.installEventFilter(self)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        if index == self._handle_index:
            self._update_geometry()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        try:
            if watched is self._splitter and event.type() == QEvent.Type.Resize:
                self._update_geometry()
        except AttributeError:
            return False
        return super().eventFilter(watched, event)

    def _update_geometry(self) -> None:
        handle = self._splitter.handle(self._handle_index)
        if not handle:
            self.hide()
            return
        handle_rect = handle.geometry()
        splitter_rect = self._splitter.rect()
        half = self.HOT_ZONE_WIDTH // 2
        if self._is_horizontal:
            x = max(0, handle_rect.center().x() - half)
            y = 0
            w = self.HOT_ZONE_WIDTH
            h = splitter_rect.height()
            if x + w > splitter_rect.width():
                x = splitter_rect.width() - w
        else:
            x = 0
            y = max(0, handle_rect.center().y() - half)
            w = splitter_rect.width()
            h = self.HOT_ZONE_WIDTH
            if y + h > splitter_rect.height():
                y = splitter_rect.height() - h
        self.setGeometry(x, y, w, h)
        self.raise_()
        self.show()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_global = event.globalPosition().toPoint()
            self._start_sizes = list(self._splitter.sizes())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if not self._dragging or self._start_global is None:
            return
        delta = event.globalPosition().toPoint() - self._start_global
        delta_val = delta.x() if self._is_horizontal else delta.y()
        if delta_val == 0:
            return
        new_sizes = list(self._start_sizes)
        widget_a = self._splitter.widget(self._handle_index)
        widget_b = self._splitter.widget(self._handle_index + 1)
        if widget_a is None or widget_b is None:
            return
        min_a = widget_a.minimumWidth() if self._is_horizontal else widget_a.minimumHeight()
        min_b = widget_b.minimumWidth() if self._is_horizontal else widget_b.minimumHeight()
        new_sizes[self._handle_index] += delta_val
        new_sizes[self._handle_index + 1] -= delta_val
        if new_sizes[self._handle_index] < min_a:
            diff = min_a - new_sizes[self._handle_index]
            new_sizes[self._handle_index] = min_a
            new_sizes[self._handle_index + 1] -= diff
        if new_sizes[self._handle_index + 1] < min_b:
            diff = min_b - new_sizes[self._handle_index + 1]
            new_sizes[self._handle_index + 1] = min_b
            new_sizes[self._handle_index] -= diff
        self._splitter.setSizes(new_sizes)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self._start_global = None
            self._start_sizes = []
            event.accept()

    def enterEvent(self, event) -> None:
        self.setCursor(
            QCursor(Qt.CursorShape.SizeHorCursor if self._is_horizontal else Qt.CursorShape.SizeVerCursor)
        )
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._dragging:
            self.unsetCursor()
        super().leaveEvent(event)


def install_invisible_handles(splitter: QSplitter, hot_zone_width: int = 4) -> None:
    """为 QSplitter 的所有 handle 安装透明拖拽热区。"""
    InvisibleResizeHandle.HOT_ZONE_WIDTH = hot_zone_width
    for i in range(splitter.count() - 1):
        InvisibleResizeHandle(splitter, i, parent=splitter)


class EdgeResizeWidget(QWidget):
    """透明窗口边缘 resize 手柄；mousePressEvent 调用 startSystemResize。"""

    SIZE: int = 8

    def __init__(self, edges: Qt.Edge, cursor_shape: Qt.CursorShape, parent: QWidget | None = None):
        super().__init__(parent)
        self._edges = edges
        self.setCursor(QCursor(cursor_shape))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

    def place(self, x: int, y: int, w: int, h: int) -> None:
        """手动定位并置顶。"""
        self.setGeometry(x, y, w, h)
        self.raise_()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win and win.windowHandle():
                win.windowHandle().startSystemResize(self._edges)


if __name__ == "__main__":
    from PySide6.QtWidgets import QMainWindow, QFrame, QPushButton
    from PySide6.QtGui import QPalette

    app = QApplication(sys.argv)
    assert theme.name == "dark" and C["bg_primary"] == V6_THEMES["dark"]["bg_primary"]
    theme.set_theme("light")
    assert theme.name == "light" and C["bg_primary"] == V6_THEMES["light"]["bg_primary"]

    class DemoWindow(QMainWindow):
        def __init__(self):
            super().__init__(None, Qt.FramelessWindowHint)
            self.resize(640, 360)
            self.setMinimumSize(200, 120)
            central = QFrame()
            central.setStyleSheet(f"background-color: {C['bg_primary']};")
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setContentsMargins(8, 8, 8, 8)
            splitter = QSplitter(Qt.Orientation.Horizontal)
            left = QFrame()
            left.setStyleSheet(f"background-color: {C['bg_sidebar']}; border-radius: 6px;")
            left.setMinimumWidth(80)
            right = QFrame()
            right.setStyleSheet(f"background-color: {C['bg_right']}; border-radius: 6px;")
            right.setMinimumWidth(80)
            splitter.addWidget(left)
            splitter.addWidget(right)
            splitter.setHandleWidth(1)
            install_invisible_handles(splitter, 6)
            splitter.setSizes([200, 400])
            layout.addWidget(splitter)
            btn = QPushButton("切换主题")
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
                f"border: 1px solid {C['border']}; border-radius: 4px; padding: 6px; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )
            btn.clicked.connect(lambda: theme.set_theme("light" if theme.name == "dark" else "dark"))
            layout.addWidget(btn)
            self._edges = [
                EdgeResizeWidget(Qt.TopEdge | Qt.LeftEdge, Qt.CursorShape.SizeFDiagCursor, central),
                EdgeResizeWidget(Qt.TopEdge, Qt.CursorShape.SizeVerCursor, central),
                EdgeResizeWidget(Qt.TopEdge | Qt.RightEdge, Qt.CursorShape.SizeBDiagCursor, central),
                EdgeResizeWidget(Qt.LeftEdge, Qt.CursorShape.SizeHorCursor, central),
                EdgeResizeWidget(Qt.RightEdge, Qt.CursorShape.SizeHorCursor, central),
                EdgeResizeWidget(Qt.BottomEdge | Qt.LeftEdge, Qt.CursorShape.SizeBDiagCursor, central),
                EdgeResizeWidget(Qt.BottomEdge, Qt.CursorShape.SizeVerCursor, central),
                EdgeResizeWidget(Qt.BottomEdge | Qt.RightEdge, Qt.CursorShape.SizeFDiagCursor, central),
            ]
            self._update_edges()

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._update_edges()

        def _update_edges(self):
            S = EdgeResizeWidget.SIZE
            W, H = self.width(), self.height()
            tl, t, tr, l, r, bl, b, br = self._edges
            tl.place(0, 0, S, S)
            t.place(S, 0, W - 2 * S, S)
            tr.place(W - S, 0, S, S)
            l.place(0, S, S, H - 2 * S)
            r.place(W - S, S, S, H - 2 * S)
            bl.place(0, H - S, S, S)
            b.place(S, H - S, W - 2 * S, S)
            br.place(W - S, H - S, S, S)

    pal = QPalette()
    pal.setColor(QPalette.Window, qcolor(C["bg_primary"]))
    pal.setColor(QPalette.WindowText, qcolor(C["text_primary"]))
    app.setPalette(pal)
    win = DemoWindow()
    win.show()
    QTimer.singleShot(50, win.close)
    sys.exit(app.exec())
