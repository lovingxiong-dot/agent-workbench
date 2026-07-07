"""agent_workbench/ui/workbench/navigator.py — 左侧动态导航。

Navigator 不写死节点，由外部注册 ModulePresentation 后自动生成列表。
用户选中某个模块时，发出 selection_changed 信号。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from v6.ui.base import C, font
from agent_workbench.ui.workbench.presentation import ModulePresentation


class Navigator(QWidget):
    """Workbench 左侧导航。"""

    selection_changed = Signal(str)  # module_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._modules: dict[str, ModulePresentation] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._list = QListWidget(self)
        self._list.setFont(font(11))
        self._list.currentItemChanged.connect(self._on_current_changed)
        self._layout.addWidget(self._list)
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_sidebar']}; border: none; color: {C['text_primary']};"
        )
        self._list.setStyleSheet(
            f"QListWidget {{ background-color: {C['bg_sidebar']}; border: none; outline: none; }}"
            f"QListWidget::item {{ padding: 8px 12px; color: {C['text_secondary']}; }}"
            f"QListWidget::item:selected {{ background-color: {C['bg_selected']}; color: {C['text_primary']}; }}"
            f"QListWidget::item:hover {{ background-color: {C['bg_hover']}; }}"
        )

    def register_module(self, presentation: ModulePresentation) -> None:
        """注册一个模块到导航。"""
        self._modules[presentation.id] = presentation
        item = QListWidgetItem(f"{presentation.icon} {presentation.name}")
        item.setData(Qt.ItemDataRole.UserRole, presentation.id)
        self._list.addItem(item)

    def clear_modules(self) -> None:
        """清空所有模块。"""
        self._modules.clear()
        self._list.clear()

    def set_selection(self, module_id: str) -> None:
        """设置当前选中项。"""
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == module_id:
                self._list.setCurrentItem(item)
                return

    def _on_current_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        module_id = current.data(Qt.ItemDataRole.UserRole)
        self.selection_changed.emit(module_id)
