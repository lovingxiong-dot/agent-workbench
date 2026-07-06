"""v6/ui/session_group.py — 可折叠会话分组。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from v6.ui.base import C, font, theme
from v6.ui.session_item import SessionItem


class GroupHeader(QWidget):
    """分组标题头，点击可折叠/展开。"""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SessionGroup(QWidget):
    """可折叠会话分组：标题、计数、会话项列表。"""

    session_selected = Signal(str)
    session_action = Signal(str, str)       # action, sid
    context_menu_requested = Signal(str, QPoint)

    def __init__(
        self,
        group_id: str,
        title: str,
        sessions: list[dict],
        expanded: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._group_id = group_id
        self._title = title
        self._expanded = expanded
        self._items: list[SessionItem] = []
        self._build(sessions)
        self._style()
        theme.changed.connect(self._style)

    def _build(self, sessions: list[dict]) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)

        self._header = GroupHeader(self)
        self._header.clicked.connect(self._toggle)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(6, 6, 6, 6)
        self._title_label = QLabel(self._title)
        self._title_label.setFont(font(12, bold=True))
        self._count_label = QLabel(str(len(sessions)))
        self._count_label.setFont(font(10))
        header_layout.addWidget(self._title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self._count_label)
        layout.addWidget(self._header)

        self._list = QWidget(self)
        list_layout = QVBoxLayout(self._list)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)
        for s in sessions:
            item = SessionItem(s["sid"], s["title"], s["preview"], s["time"])
            item.selected.connect(self.session_selected.emit)
            item.context_menu_requested.connect(self.context_menu_requested.emit)
            self._items.append(item)
            list_layout.addWidget(item)
        list_layout.addStretch(1)
        layout.addWidget(self._list)
        self._list.setVisible(self._expanded)

    def _style(self) -> None:
        self._header.setStyleSheet(
            f"GroupHeader {{ background-color: transparent; border-radius: 4px; }}"
            f"GroupHeader:hover {{ background-color: {C['bg_hover']}; }}"
            f"QLabel {{ color: {C['text_secondary']}; }}"
        )
        self._count_label.setStyleSheet(
            f"color: {C['text_muted']}; background-color: {C['btn_bg']}; "
            f"border-radius: 8px; padding: 0 6px;"
        )

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._list.setVisible(self._expanded)

    def group_id(self) -> str:
        return self._group_id

    def items(self) -> list[SessionItem]:
        return list(self._items)

    def set_active(self, sid: str) -> None:
        for item in self._items:
            item.set_active(item.sid() == sid)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    demo = [
        {"sid": "s1", "title": "V6 架构讨论", "preview": "讨论 UI 分层与信号契约", "time": "10:23"},
        {"sid": "s2", "title": "base.py 实现", "preview": "主题系统与基础工具", "time": "09:15"},
    ]
    group = SessionGroup("today", "今天", demo)
    group.session_selected.connect(lambda sid: print("selected", sid))
    group.context_menu_requested.connect(lambda sid, pos: print("context", sid))
    group.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(800, group.close)
    sys.exit(app.exec())
