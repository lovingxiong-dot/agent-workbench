"""v6/ui/header_bar.py — 中区标题栏。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy

from v6.ui.base import C, qcolor, font


class HeaderBar(QWidget):
    """标题栏：左侧折叠、双行标题、搜索/更多/右侧折叠，支持拖拽与双击最大化。"""

    left_expand_toggled = Signal()
    expand_toggled = Signal()
    search_clicked = Signal()
    more_clicked = Signal(QPoint)
    double_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setMouseTracking(True)
        self._drag_start: QPoint | None = None
        self._build()
        self.refresh_theme()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._btn_left = self._icon_btn("☰", "折叠/展开左栏")
        self._btn_left.clicked.connect(self.left_expand_toggled.emit)
        layout.addWidget(self._btn_left)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(8, 0, 8, 0)
        self._title = QLabel("V6 Chat")
        self._title.setFont(font(14, bold=True))
        self._title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._subtitle = QLabel("未选择项目")
        self._subtitle.setFont(font(10))
        title_layout.addWidget(self._title)
        title_layout.addWidget(self._subtitle)
        title_container = QWidget()
        title_container.setLayout(title_layout)
        title_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(title_container, 1)

        self._btn_search = self._icon_btn("🔍", "搜索 (Ctrl+F)")
        self._btn_search.clicked.connect(self.search_clicked.emit)
        layout.addWidget(self._btn_search)

        self._btn_more = self._icon_btn("⋯", "更多")
        self._btn_more.clicked.connect(self._on_more)
        layout.addWidget(self._btn_more)

        self._btn_right = self._icon_btn("»", "折叠/展开右栏")
        self._btn_right.clicked.connect(self.expand_toggled.emit)
        layout.addWidget(self._btn_right)

    def _icon_btn(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {C['text_secondary']}; border: none; "
            f"border-radius: 6px; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def set_title(self, title: str, subtitle: str) -> None:
        self._title.setText(title)
        self._subtitle.setText(subtitle)

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border-bottom: 1px solid {C['border']};")
        for btn in (self._btn_left, self._btn_search, self._btn_more, self._btn_right):
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {C['text_secondary']}; border: none; "
                f"border-radius: 6px; font-size: 14px; }}"
                f"QPushButton:hover {{ background-color: {C['btn_hover']}; color: {C['text_primary']}; }}"
            )
        self._title.setStyleSheet(f"color: {C['text_primary']};")
        self._subtitle.setStyleSheet(f"color: {C['text_muted']};")

    def _on_more(self) -> None:
        pos = self._btn_more.mapToGlobal(QPoint(0, self._btn_more.height()))
        self.more_clicked.emit(pos)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            win = self.window()
            if win.isMaximized():
                win.showNormal()
            else:
                win.showMaximized()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    win.resize(640, 80)
    central = QWidget()
    QVBoxLayout(central).addWidget(HeaderBar(central))
    win.setCentralWidget(central)
    win.show()
    QTimer_single = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer_single.singleShot(200, win.close)
    sys.exit(app.exec())
