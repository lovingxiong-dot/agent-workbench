"""
ExplorerTreeView — 资源管理器树视图

基于 QTreeView，提供：
- emoji 图标渲染（通过委托）
- 节点展开/折叠、选中信号透传
- 过滤隐藏（setRowHidden）
"""
from PySide6.QtCore import Qt, Signal, QSize, QModelIndex
from PySide6.QtGui import QPainter, QFontMetrics
from PySide6.QtWidgets import (
    QStyledItemDelegate, QStyleOptionViewItem, QTreeView, QWidget,
)

from ui.models.explorer_tree_model import ExplorerTreeItem, NodeKind


class EmojiIconDelegate(QStyledItemDelegate):
    """用 emoji 作为图标的简单委托"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        icon = index.data(Qt.DecorationRole)
        icon_width = 0
        if icon and isinstance(icon, str):
            fm = QFontMetrics(option.font)
            icon_width = fm.height() + 4

        # 调整文本区域，为 emoji 留出左侧空间
        full_rect = option.rect
        if icon_width > 0:
            option.rect = full_rect.adjusted(icon_width, 0, 0, 0)

        super().paint(painter, option, index)

        # 在预留区域绘制 emoji
        if icon_width > 0 and icon:
            icon_size = icon_width - 4
            x = full_rect.left() + 2
            y = full_rect.top() + (full_rect.height() - icon_size) // 2
            painter.drawText(x, y, icon_size, icon_size, Qt.AlignCenter, icon)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        size = super().sizeHint(option, index)
        icon = index.data(Qt.DecorationRole)
        if icon and isinstance(icon, str):
            size.setWidth(size.width() + 20)
        return size


class ExplorerTreeView(QTreeView):
    """资源管理器专用 QTreeView"""

    file_clicked = Signal(str, str)        # path, kind_name
    file_double_clicked = Signal(str, str) # path, kind_name
    context_menu_requested = Signal(object, object)  # index, global_pos

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._delegate = EmojiIconDelegate(self)
        self.setItemDelegate(self._delegate)
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setObjectName("projectExplorer")
        self.setIndentation(16)
        self.setUniformRowHeights(True)
        self.expanded.connect(self._on_expanded)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _on_expanded(self, index):
        """节点展开时请求模型懒加载"""
        model = self.model()
        if model is None:
            return
        if model.canFetchMore(index):
            model.fetchMore(index)

    def _on_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
        self.context_menu_requested.emit(index, self.viewport().mapToGlobal(pos))

    def current_item(self) -> tuple[str, str]:
        """返回当前选中项的 (path, kind_name)"""
        index = self.currentIndex()
        if not index.isValid():
            return "", ""
        path = index.data(Qt.UserRole) or ""
        kind = index.data(Qt.UserRole + 1) or ""
        return path, kind

    def apply_filter(self, text: str):
        """根据文本过滤：隐藏不匹配的节点，保留父节点以显示匹配子节点"""
        text = text.strip().lower()
        model = self.model()
        if model is None:
            return
        self._apply_filter_on_index(model, QModelIndex(), text)

    def _apply_filter_on_index(self, model, parent_index, text: str) -> bool:
        any_visible = False
        rows = model.rowCount(parent_index)
        for row in range(rows):
            idx = model.index(row, 0, parent_index)
            child_visible = self._apply_filter_on_index(model, idx, text)
            name = (idx.data(Qt.DisplayRole) or "").lower()
            kind_name = idx.data(Qt.UserRole + 1) or ""
            item: ExplorerTreeItem = model.item_from_index(idx)
            is_category = kind_name == NodeKind.CATEGORY.name
            matches = (not text) or (text in name)
            visible = is_category or matches or child_visible
            self.setRowHidden(row, parent_index, not visible)
            if visible:
                any_visible = True
        return any_visible
