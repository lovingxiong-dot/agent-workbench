"""v6/ui/tab_button.py — 左栏/右栏 Tab 切换按钮。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton

from v6.ui.base import C, font, theme


class TabType:
    """右栏标签类型常量。"""

    FILE = "file"
    TERMINAL = "terminal"
    BROWSER = "browser"


class TabButton(QPushButton):
    """Tab 按钮。支持左侧栏的简单模式与右栏带关闭按钮的模式。"""

    close_clicked = Signal()

    def __init__(
        self,
        text: str,
        tab_type: str = "",
        width: int = 0,
        active: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._tab_type = tab_type
        self._active = active
        self._close_btn: QPushButton | None = None
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        if width:
            self.setFixedWidth(width)
        if tab_type:
            self._add_close_button()
        self.setChecked(active)
        self._style()
        theme.changed.connect(self._style)

    @property
    def tab_type(self) -> str:
        return self._tab_type

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.setChecked(active)
            self._style()

    def _add_close_button(self) -> None:
        btn = QPushButton("×", self)
        btn.setFixedSize(14, 14)
        btn.setFont(font(10, bold=True))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {C['text_secondary']}; "
            f"border: none; font-size: 12px; }}"
            f"QPushButton:hover {{ color: {C['text_primary']}; }}"
        )
        btn.clicked.connect(lambda: self.close_clicked.emit())
        self._close_btn = btn
        self._place_close_button()

    def _place_close_button(self) -> None:
        if self._close_btn:
            self._close_btn.move(self.width() - 18, 9)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_close_button()

    def _style(self) -> None:
        if self._active:
            bg = C["bg_tab_active"]
            fg = C["text_primary"]
            border = C["border"]
        else:
            bg = "transparent"
            fg = C["text_secondary"]
            border = "transparent"
        self.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: {fg}; text-align: left; padding-left: 8px; "
            f"border: 1px solid {border}; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
