"""v6/ui/window_frame.py — 无边框窗口辅助组件与 Apple 风格弹出菜单。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

import sys
from pathlib import Path

# 支持直接以脚本运行：python v6/ui/window_frame.py
if __package__ is None and __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import Qt, Signal, QObject, QEvent, QTimer, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QCursor, QBitmap, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QVBoxLayout, QPushButton, QFrame,
)

from v6.ui.base import C, qcolor


class AppleMenuItem(QLabel):
    """Apple 风格菜单项：文本标签 + hover 圆角高亮。"""

    clicked = Signal()
    _ACTIVE_BG = "#007AFF1A"  # 10% accent（深浅主题通用）

    def __init__(self, text: str = "", is_separator: bool = False):
        super().__init__()
        self._is_sep = is_separator
        self._hover = False
        if is_separator:
            self.setFixedHeight(1)
        else:
            self.setText(text)
            self.setFixedHeight(32)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setMouseTracking(True)
            self.setIndent(12)
            self._style()

    def _style(self) -> None:
        if self._is_sep:
            return
        bg = self._ACTIVE_BG if self._hover else "transparent"
        self.setStyleSheet(
            f"AppleMenuItem {{ background-color: {bg}; color: {C['text_primary']}; "
            f"font-size: 13px; border-radius: 6px; margin: 1px 6px; }}"
        )

    def enterEvent(self, event) -> None:
        self._hover = True
        self._style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._style()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._is_sep:
            self.clicked.emit()


class AppleMenu(QWidget):
    """Apple 风格弹出菜单：圆角背景 + 像素级阴影边框 + 外部点击关闭。"""

    MENU_WIDTH = 180
    CORNER = 8

    def __init__(self, parent: QWidget | None = None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(self.MENU_WIDTH)
        self._items: list[AppleMenuItem] = []

    def add_item(self, text: str) -> AppleMenuItem:
        item = AppleMenuItem(text)
        self._items.append(item)
        return item

    def add_separator(self) -> None:
        self._items.append(AppleMenuItem("", is_separator=True))

    def build(self) -> None:
        """构建内部布局并计算总高度。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)
        for it in self._items:
            if it._is_sep:
                sep_w = QFrame()
                sep_w.setFixedHeight(9)
                sep_w.setStyleSheet(f"border-top: 1px solid {C['border']}; margin: 4px 6px;")
                layout.addWidget(sep_w)
            else:
                layout.addWidget(it)
                it.clicked.connect(self.close)
        h = sum(it.height() if not it._is_sep else 9 for it in self._items) + 12
        self.setFixedHeight(h)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 外侧微阴影
        p.setBrush(QColor(0, 0, 0, 40))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), self.CORNER, self.CORNER)
        # 主背景
        p.setBrush(QColor(C["bg_card"]))
        p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), self.CORNER - 1, self.CORNER - 1)
        # 细边框
        p.setPen(QPen(QColor(C["border"]), 0.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(
            self.rect().adjusted(1, 1, -2, -2).toRectF(), self.CORNER, self.CORNER
        )
        p.end()

    def show_at(self, pos: QPoint) -> None:
        self.build()
        self.move(pos)
        self.show()
        QTimer.singleShot(100, self._install_close_filter)

    def _install_close_filter(self) -> None:
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            gp = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            if not self.geometry().contains(gp):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        super().closeEvent(event)


# ══════════════════════════════════════════════════════════════
# 无边框窗口辅助组件
# ══════════════════════════════════════════════════════════════
def apply_rounded_window_mask(window: QMainWindow, radius: int = 8) -> None:
    """为 FramelessWindowHint 窗口应用四角圆角遮罩。"""
    path = QPainterPath()
    path.addRoundedRect(window.rect(), radius, radius)
    mask = QBitmap(window.size())
    mask.fill(Qt.GlobalColor.color0)
    p = QPainter(mask)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillPath(path, Qt.GlobalColor.color1)
    p.end()
    window.setMask(mask)


class FramelessWindowHelper(QObject):
    """为无边框主窗口自动管理 8 个 EdgeResizeWidget 与圆角遮罩。

    用法：
        helper = FramelessWindowHelper(window, edge_size=8, radius=8)
    """

    def __init__(
        self,
        window: QMainWindow,
        central: QWidget | None = None,
        edge_size: int = 8,
        radius: int = 8,
    ):
        super().__init__(window)
        self._window = window
        self._central = central or window.centralWidget()
        self._edge_size = edge_size
        self._radius = radius
        from v6.ui.base import EdgeResizeWidget

        S = Qt.CursorShape
        E = Qt.Edge
        self._edges = [
            EdgeResizeWidget(E.TopEdge | E.LeftEdge, S.SizeFDiagCursor, self._central),
            EdgeResizeWidget(E.TopEdge, S.SizeVerCursor, self._central),
            EdgeResizeWidget(E.TopEdge | E.RightEdge, S.SizeBDiagCursor, self._central),
            EdgeResizeWidget(E.LeftEdge, S.SizeHorCursor, self._central),
            EdgeResizeWidget(E.RightEdge, S.SizeHorCursor, self._central),
            EdgeResizeWidget(E.BottomEdge | E.LeftEdge, S.SizeBDiagCursor, self._central),
            EdgeResizeWidget(E.BottomEdge, S.SizeVerCursor, self._central),
            EdgeResizeWidget(E.BottomEdge | E.RightEdge, S.SizeFDiagCursor, self._central),
        ]
        window.installEventFilter(self)
        self._place_edges()
        if radius:
            apply_rounded_window_mask(window, radius)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        try:
            if obj is self._window and event.type() == QEvent.Type.Resize:
                self._place_edges()
                if self._radius:
                    apply_rounded_window_mask(self._window, self._radius)
        except AttributeError:
            return False
        return super().eventFilter(obj, event)

    def _place_edges(self) -> None:
        if self._central is None:
            return
        s = self._edge_size
        W, H = self._window.width(), self._window.height()
        tl, t, tr, l, r, bl, b, br = self._edges
        tl.place(0, 0, s, s)
        t.place(s, 0, W - 2 * s, s)
        tr.place(W - s, 0, s, s)
        l.place(0, s, s, H - 2 * s)
        r.place(W - s, s, s, H - 2 * s)
        bl.place(0, H - s, s, s)
        b.place(s, H - s, W - 2 * s, s)
        br.place(W - s, H - s, s, s)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    class DemoWindow(QMainWindow):
        def __init__(self):
            super().__init__(None, Qt.WindowType.FramelessWindowHint)
            self.resize(500, 300)
            self.setMinimumSize(200, 120)
            central = QFrame()
            central.setStyleSheet(f"background-color: {C['bg_primary']};")
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setContentsMargins(16, 16, 16, 16)

            btn = QPushButton("打开 AppleMenu")
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
                f"border: 1px solid {C['border']}; border-radius: 6px; padding: 8px 16px; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            )
            btn.clicked.connect(lambda: self._show_menu(btn))
            layout.addWidget(btn)

            self._helper = FramelessWindowHelper(self, edge_size=8, radius=8)
            self._menu: AppleMenu | None = None

        def _show_menu(self, btn: QPushButton) -> None:
            self._menu = AppleMenu(self)
            self._menu.add_item("新建项目").clicked.connect(lambda: print("新建项目"))
            self._menu.add_item("打开...").clicked.connect(lambda: print("打开"))
            self._menu.add_separator()
            self._menu.add_item("退出").clicked.connect(self.close)
            gp = btn.mapToGlobal(QPoint(0, btn.height()))
            self._menu.show_at(gp)

    win = DemoWindow()
    win.show()
    QTimer.singleShot(50, win.close)
    sys.exit(app.exec())
