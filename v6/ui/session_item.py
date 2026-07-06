"""v6/ui/session_item.py — 会话列表项。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from v6.ui.base import C, font, theme


class SessionItem(QWidget):
    """会话列表项：标题/预览/时间，支持 active/hover 状态，右键菜单请求信号。"""

    selected = Signal(str)                       # sid
    action_requested = Signal(str, str)          # action, sid
    context_menu_requested = Signal(str, QPoint) # sid, global_pos

    def __init__(
        self,
        sid: str,
        title: str,
        preview: str,
        time: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sid = sid
        self._title = title
        self._preview = preview
        self._time = time
        self._active = False
        self._hover = False
        self.setMouseTracking(True)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()
        self._style()
        theme.changed.connect(self._style)

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self._title_label = QLabel(self._title)
        self._title_label.setFont(font(13, bold=True))
        self._title_label.setObjectName("title")
        self._preview_label = QLabel(self._preview)
        self._preview_label.setFont(font(11))
        self._preview_label.setObjectName("preview")
        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._preview_label)
        layout.addLayout(text_layout, 1)

        self._time_label = QLabel(self._time)
        self._time_label.setFont(font(10))
        self._time_label.setObjectName("time")
        layout.addWidget(self._time_label)

    def _style(self) -> None:
        bg = C["bg_selected"] if self._active else (C["bg_hover"] if self._hover else "transparent")
        self.setStyleSheet(
            f"SessionItem {{ background-color: {bg}; border-radius: 6px; }}"
            f"QLabel#title {{ color: {C['text_primary']}; }}"
            f"QLabel#preview {{ color: {C['text_secondary']}; }}"
            f"QLabel#time {{ color: {C['text_muted']}; }}"
        )

    def sid(self) -> str:
        return self._sid

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self._style()

    def enterEvent(self, event) -> None:
        self._hover = True
        self._style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._style()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self._sid)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self._sid, event.globalPosition().toPoint())
        super().mousePressEvent(event)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    item = SessionItem("s1", "V6 架构讨论", "讨论 UI 分层与信号契约", "10:23")
    item.selected.connect(lambda sid: print("selected", sid))
    item.context_menu_requested.connect(lambda sid, pos: print("context", sid, pos))
    item.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(800, item.close)
    sys.exit(app.exec())
