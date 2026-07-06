"""v6/ui/chat_scene.py — QGraphicsScene 管理聊天项。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem

from v6.ui.base import C, qcolor, theme
from v6.ui.chat_items import (
    ChatItem,
    UserBubble,
    TextItem,
    PhasePanel,
    ToolEntry,
    SystemCard,
    FoldBlock,
    BulletItem,
    StepItem,
)


class ChatScene(QGraphicsScene):
    """管理聊天图形项，支持动态宽度与主题刷新。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[tuple[ChatItem, bool]] = []
        self._width = 800
        self._margin = 16
        self._spacing = 10
        self._keyword = ""
        self._theme = theme.name

        self._bg = QGraphicsRectItem()
        self._bg.setPen(Qt.PenStyle.NoPen)
        self._bg.setBrush(qcolor(C["bg_primary"]))
        self.addItem(self._bg)

        theme.changed.connect(self.refresh_theme)

    def set_width(self, width: int) -> None:
        self._width = max(width, 200)
        item_width = max(self._width - self._margin * 2, 120)
        for item, _ in self._items:
            item.set_width(item_width)
        self._relayout()

    def add_user_message(self, text: str) -> UserBubble:
        item = UserBubble(text, self._item_width(), self._theme)
        return self._add_item(item, align_right=True)

    def add_ai_message(self, text: str, phase: str = "") -> ChatItem:
        if phase:
            item: ChatItem = PhasePanel(phase, text, self._item_width(), self._theme)
        else:
            item = TextItem(text, self._item_width(), self._theme)
        return self._add_item(item)

    def add_tool(self, name: str, result: dict, status: str = "ok") -> ToolEntry:
        item = ToolEntry(name, result, status, self._item_width(), self._theme)
        return self._add_item(item)

    def add_system_card(self, title: str, text: str) -> SystemCard:
        item = SystemCard(title, text, self._item_width(), self._theme)
        return self._add_item(item)

    def add_fold_block(self, title: str, body: str) -> FoldBlock:
        item = FoldBlock(title, body, self._item_width(), self._theme)
        return self._add_item(item)

    def add_bullet(self, text: str) -> BulletItem:
        item = BulletItem(text, self._item_width(), self._theme)
        return self._add_item(item)

    def add_step(self, index: int, text: str) -> StepItem:
        item = StepItem(index, text, self._item_width(), self._theme)
        return self._add_item(item)

    def _item_width(self) -> int:
        return max(self._width - self._margin * 2, 120)

    def _add_item(self, item: ChatItem, align_right: bool = False):
        item.set_keyword(self._keyword)
        self.addItem(item)
        self._items.append((item, align_right))
        self._relayout()
        return item

    def set_keyword(self, keyword: str) -> None:
        self._keyword = keyword
        for item, _ in self._items:
            item.set_keyword(keyword)
        self._relayout()

    def match_items(self) -> list[ChatItem]:
        kw = self._keyword.lower()
        if not kw:
            return []
        return [item for item, _ in self._items if kw in item.text().lower()]

    def refresh_theme(self, name: str) -> None:
        self._theme = name
        self._bg.setBrush(qcolor(C["bg_primary"]))
        for item, _ in self._items:
            item.refresh_theme()
        self._relayout()

    def clear_chat(self) -> None:
        for item, _ in self._items:
            self.removeItem(item)
        self._items.clear()
        self._relayout()

    def _relayout(self) -> None:
        y = self._margin
        for item, align_right in self._items:
            rect = item.boundingRect()
            w = rect.width()
            x = self._width - self._margin - w if align_right else self._margin
            item.setPos(x, y)
            y += int(rect.height()) + self._spacing
        y += self._margin
        self._bg.setRect(0, 0, self._width, max(y, 200))
        self.setSceneRect(0, 0, self._width, max(y, 200))


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QGraphicsView
    from PySide6.QtCore import QTimer

    app = QApplication(sys.argv)
    scene = ChatScene()
    scene.add_user_message("帮我写一个快速排序。")
    scene.add_ai_message("好的，下面是 Python 实现：")
    scene.add_fold_block("quick_sort.py", "def quick_sort(arr):\n    return sorted(arr)")
    scene.add_tool("run_tests", {"passed": 5, "failed": 0}, "ok")
    scene.add_system_card("系统消息", "测试全部通过。")
    view = QGraphicsView(scene)
    view.resize(620, 500)
    view.show()
    QTimer.singleShot(300, view.close)
    sys.exit(app.exec())
