"""
chat_scene.py — QGraphicsScene 场景管理器

管理所有消息 Item 的垂直布局、折叠展开重排版、滚动控制。
坐标系原点(0,0) = 聊天区左上角，宽402px。
"""
from __future__ import annotations

from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QBrush, QColor

from .chat_items import (
    CHAT_WIDTH, LEFT_MARGIN, C_BG_PRIMARY,
    BaseMessageItem, UserBubbleItem, FoldBlockItem,
    ToolEntryItem, PhasePanelItem,
    PhaseStepItem, PhaseBulletItem, PhaseTextItem,
    SystemCardItem
)

SPACING = 8.0


class ChatScene(QGraphicsScene):
    """聊天场景：管理消息 Item 的添加、布局、折叠展开。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []
        self._current_y: float = 8.0
        self._content_h: float = 0
        self._auto_scroll = True
        self.setBackgroundBrush(QBrush(C_BG_PRIMARY))

    def add_item(self, item) -> BaseMessageItem:
        """添加任意消息 item 并自动定位。支持 BaseMessageItem 和 QGraphicsProxyWidget。"""
        self.addItem(item)
        item.setPos(0, self._current_y)
        if hasattr(item, 'item_height'):
            self._current_y += item.item_height() + SPACING
        else:
            self._current_y += item.boundingRect().height() + SPACING
        self._items.append(item)
        self._update_scene_rect()
        return item

    def add_user_message(self, text: str) -> UserBubbleItem:
        item = UserBubbleItem(text)
        return self.add_item(item)

    def add_thinking_fold(self, status: str = "") -> FoldBlockItem:
        item = FoldBlockItem("思考过程", status)
        return self.add_item(item)

    def add_tool_fold(self, status: str = "") -> FoldBlockItem:
        item = FoldBlockItem("工具执行", status)
        return self.add_item(item)

    def add_output_fold(self, status: str = "") -> FoldBlockItem:
        item = FoldBlockItem("内部命令输出", status)
        return self.add_item(item)

    def add_tool_entries_to_fold(self, fold: FoldBlockItem, entries: list[dict]) -> FoldBlockItem:
        """向工具折叠块添加工具条目列表。
        
        entries: [{"name": "run_command", "elapsed_ms": 800, "success": True}, ...]
        """
        body_items = []
        for entry in entries:
            ti = ToolEntryItem(
                tool_name=entry.get("name", "unknown"),
                elapsed_ms=entry.get("elapsed_ms", 0),
                success=entry.get("success", True)
            )
            body_items.append(ti)

        body_h = len(body_items) * ToolEntryItem(None, 0, True).item_height()
        # 定位 body items 在 fold 展开区域中（header 下方）
        y_offset = fold.HEADER_H + 2
        for i, item in enumerate(body_items):
            item.setPos(0, y_offset + i * item.item_height())

        fold.set_body(body_items, body_h)
        return fold

    def add_phase_panel(self, phase: str) -> PhasePanelItem:
        item = PhasePanelItem(phase)
        return self.add_item(item)

    def add_phase_body(self, panel: PhasePanelItem, body_items: list[QGraphicsItem], body_height: float) -> PhasePanelItem:
        """向阶段面板添加 body 内容。body_items 作为 panel 的子项，坐标相对于 panel。"""
        from .chat_items import BaseMessageItem
        valid_items = [i for i in body_items if isinstance(i, BaseMessageItem)]
        panel.set_body(valid_items, body_height)
        # 非 BaseMessageItem 直接设为 panel 子项
        for item in body_items:
            if not isinstance(item, BaseMessageItem):
                item.setParentItem(panel)
        return panel

    def add_text_item(self, html: str, y: float = 0, width: float = 362) -> QGraphicsTextItem:
        """添加独立文本项（用于流式或简单 AI 正文）。"""
        from PySide6.QtWidgets import QGraphicsTextItem
        text_item = QGraphicsTextItem()
        text_item.setHtml(html)
        text_item.setTextWidth(width)
        text_item.setPos(LEFT_MARGIN + 4, y)
        self.addItem(text_item)
        text_item.setPos(LEFT_MARGIN + 4, self._current_y)
        self._current_y += text_item.boundingRect().height() + SPACING
        self._items.append(text_item)
        self._update_scene_rect()
        return text_item

    def add_system_card(self, text: str) -> SystemCardItem:
        item = SystemCardItem(text)
        return self.add_item(item)

    # ── 折叠重新排版 ──

    def _relayout_from(self, index: int):
        """从指定 index 开始重新排版所有后续 item。"""
        if index < 0 or index >= len(self._items):
            return

        if index == 0:
            y = 8.0
        else:
            prev = self._items[index - 1]
            y = prev.pos().y() + (prev.item_height() if hasattr(prev, 'item_height') else prev.boundingRect().height()) + SPACING

        for i in range(index, len(self._items)):
            item = self._items[i]
            item.setPos(0, y)
            h = item.item_height() if hasattr(item, 'item_height') else item.boundingRect().height()
            y += h + SPACING

        self._current_y = y
        self._update_scene_rect()

    def on_fold_toggled(self, fold: FoldBlockItem):
        """折叠块状态切换后触发重新排版。"""
        try:
            idx = self._items.index(fold)
        except ValueError:
            return
        self._relayout_from(idx + 1)

    def _update_scene_rect(self):
        """更新场景矩形以适配滚动。"""
        h = max(self._current_y + 40, 720)
        self.setSceneRect(QRectF(0, 0, CHAT_WIDTH, h))

    def enable_auto_scroll(self, enabled: bool):
        self._auto_scroll = enabled

    def scroll_to_bottom(self, view: QGraphicsView):
        """滚动视图到底部。"""
        if not self._auto_scroll or view is None:
            return
        # 延迟一帧执行，让布局生效
        QTimer.singleShot(0, lambda: self._do_scroll(view))

    def _do_scroll(self, view: QGraphicsView):
        vbar = view.verticalScrollBar()
        if vbar:
            vbar.setValue(vbar.maximum())

    @property
    def items(self) -> list:
        return self._items

    def clear(self):
        super().clear()
        self._items.clear()
        self._current_y = 8.0
