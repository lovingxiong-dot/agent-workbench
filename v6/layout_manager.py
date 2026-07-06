"""v6/layout_manager.py — 三栏布局管理器。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from v6.ui.base import install_invisible_handles


class LayoutManager:
    """管理左/中/右三栏 QSplitter，支持独立折叠/展开。"""

    LEFT_WIDTH = 220
    RIGHT_WIDTH = 400
    MIN_MIDDLE = 240

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent
        self._left = QWidget(parent)
        self._chat = QWidget(parent)
        self._right = QWidget(parent)
        for w in (self._left, self._chat, self._right):
            QVBoxLayout(w).setContentsMargins(0, 0, 0, 0)
        self._left.setMinimumWidth(self.LEFT_WIDTH)
        self._right.setMinimumWidth(self.RIGHT_WIDTH)
        self._chat.setMinimumWidth(self.MIN_MIDDLE)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, parent)
        self._splitter.setHandleWidth(1)
        self._splitter.addWidget(self._left)
        self._splitter.addWidget(self._chat)
        self._splitter.addWidget(self._right)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        install_invisible_handles(self._splitter, 4)
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._splitter)
        self._splitter.setSizes([self.LEFT_WIDTH, 640, self.RIGHT_WIDTH])
        self._left_width = self.LEFT_WIDTH
        self._right_width = self.RIGHT_WIDTH

    @property
    def left_panel(self) -> QWidget:
        return self._left

    @property
    def chat_area(self) -> QWidget:
        return self._chat

    @property
    def right_panel(self) -> QWidget:
        return self._right

    def toggle_left(self) -> None:
        if self._left.maximumWidth() == 0:
            self._left.setMaximumWidth(16777215)
            sizes = self._splitter.sizes()
            self._splitter.setSizes([self._left_width, sizes[1], sizes[2]])
        else:
            self._left_width = max(self._splitter.sizes()[0], self.LEFT_WIDTH)
            self._left.setMaximumWidth(0)

    def toggle_right(self) -> None:
        if self._right.maximumWidth() == 0:
            self._right.setMaximumWidth(16777215)
            sizes = self._splitter.sizes()
            self._splitter.setSizes([sizes[0], sizes[1], self._right_width])
        else:
            self._right_width = max(self._splitter.sizes()[2], self.RIGHT_WIDTH)
            self._right.setMaximumWidth(0)
