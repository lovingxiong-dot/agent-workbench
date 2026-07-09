"""agent_workbench/ui/workbench/title_bar.py — Workbench 顶部标题栏。

职责：
- 显示应用标题与 Runtime 状态指示。
- 提供窗口控制按钮（最小化 / 最大化 / 关闭）。
- 支持拖拽移动窗口、双击最大化/还原。

这是 Host 级 UI，不属于 Workbench 骨架本身。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from v6.ui.base import C, font


class WorkbenchTitleBar(QWidget):
    """Workbench 顶部标题栏。"""

    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    feedback_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setMouseTracking(True)
        self._drag_start: QPoint | None = None
        self._build()
        self._apply_theme()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # 左侧：图标 + 标题 + 状态
        self._icon = QLabel("◆")
        self._icon.setFont(font(12, bold=True))
        self._icon.setStyleSheet(f"color: {C['accent']};")
        layout.addWidget(self._icon)

        self._title = QLabel("Agent Workbench")
        self._title.setFont(font(12, bold=True))
        self._title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._title)

        self._status_icon = QLabel("●")
        self._status_icon.setFont(font(10))
        self._status_icon.setStyleSheet("color: #10B981;")  # green
        layout.addWidget(self._status_icon)

        self._status_text = QLabel("Running")
        self._status_text.setFont(font(10))
        layout.addWidget(self._status_text)

        # 右侧：Feedback + 窗口按钮
        self._btn_feedback = self._window_btn("💡 Feedback", "提交反馈")
        self._btn_feedback.setFixedWidth(90)
        self._btn_feedback.clicked.connect(self.feedback_requested.emit)
        layout.addWidget(self._btn_feedback)

        self._btn_min = self._window_btn("−", "最小化")
        self._btn_max = self._window_btn("□", "最大化/还原")
        self._btn_close = self._window_btn("×", "关闭")
        self._btn_min.clicked.connect(self.minimize_requested.emit)
        self._btn_max.clicked.connect(self.maximize_requested.emit)
        self._btn_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(self._btn_min)
        layout.addWidget(self._btn_max)
        layout.addWidget(self._btn_close)

    def _window_btn(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {C['text_secondary']}; border: none; "
            f"border-radius: 4px; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; color: {C['text_primary']}; }}"
        )
        return btn

    def set_status(self, running: bool) -> None:
        """更新 Runtime 状态显示。"""
        if running:
            self._status_icon.setStyleSheet("color: #10B981;")
            self._status_text.setText("Running")
        else:
            self._status_icon.setStyleSheet("color: #EF4444;")
            self._status_text.setText("Stopped")

    def set_title(self, title: str) -> None:
        """更新窗口标题。"""
        self._title.setText(title)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_primary']}; border-bottom: 1px solid {C['border']};"
        )
        self._title.setStyleSheet(f"color: {C['text_primary']};")
        self._status_text.setStyleSheet(f"color: {C['text_secondary']};")

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
            self.maximize_requested.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
