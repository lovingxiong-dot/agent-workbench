"""v4 聊天场景。"""
from __future__ import annotations
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush
from .base import theme, C, qcolor


class ChatScene(QGraphicsScene):
    CHAT_W = 402
    LEFT_MARGIN = 20
    CONTENT_W = 362

    @classmethod
    def set_width(cls, w: float):
        cls.CHAT_W = w
        cls.CONTENT_W = max(120.0, w - 40)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._y = 8.0
        self._items: list = []
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))

    def add_chat_item(self, item: ChatItem) -> ChatItem:
        self.addItem(item)
        item.setPos(0, self._y)
        self._y += item.height() + 8
        self._items.append(item)
        self._update_rect()
        return item

    def _update_rect(self):
        h = max(self._y + 40, 720)
        self.setSceneRect(QRectF(0, 0, ChatScene.CHAT_W, h))

    def clear_items(self):
        super().clear()
        self._items.clear()
        self._y = 8.0

    def refresh(self):
        self.setBackgroundBrush(QBrush(qcolor(C["bg_primary"])))
        for item in self._items:
            item.update()

