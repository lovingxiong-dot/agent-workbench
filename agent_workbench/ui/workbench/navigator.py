"""agent_workbench/ui/workbench/navigator.py — 左侧 Navigator（v6.10.0 重设计）。

结构：
- 顶部固定功能 Tab（Chat / Skills / Tools）。
- 下方可折叠 Settings 区，展示配置分类（Provider / LLM / MCP 等）。
- 每个 Settings 分类右侧带 "+" 按钮，用于新增实例。

点击功能 Tab 或 Settings 分类都会发出 selection_changed(item_id)。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font


class _SettingsCategoryWidget(QWidget):
    """Settings 分类行：左侧标题/图标，右侧 "+" 按钮。"""

    def __init__(
        self,
        category_id: str,
        title: str,
        icon: str,
        list_widget: QListWidget,
        item: QListWidgetItem | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._category_id = category_id
        self._list_widget = list_widget
        self._item = item

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(8)

        self._label = QLabel(f"{icon} {title}")
        self._label.setFont(font(11))
        layout.addWidget(self._label, 1)

        self._add_btn = QPushButton("+")
        self._add_btn.setFont(font(11, bold=True))
        self._add_btn.setFixedSize(20, 20)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: none; border-radius: 4px; padding: 0px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        layout.addWidget(self._add_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setStyleSheet(f"background-color: transparent; color: {C['text_secondary']};")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._list_widget.setCurrentItem(self._item)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet(
                f"background-color: {C['bg_selected']}; color: {C['text_primary']};"
            )
            self._label.setStyleSheet(f"color: {C['text_primary']};")
        else:
            self.setStyleSheet(f"background-color: transparent; color: {C['text_secondary']};")
            self._label.setStyleSheet(f"color: {C['text_secondary']};")


class Navigator(QWidget):
    """Workbench 左侧导航。"""

    selection_changed = Signal(str)  # workspace_id or category_id
    add_requested = Signal(str)  # category_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._functional_items: dict[str, QListWidgetItem] = {}
        self._settings_items: dict[str, QListWidgetItem] = {}
        self._settings_widgets: dict[str, _SettingsCategoryWidget] = {}
        self._settings_expanded = True

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 顶部功能 Tab 列表
        self._functional_list = QListWidget(self)
        self._functional_list.setFont(font(11))
        self._functional_list.currentItemChanged.connect(self._on_functional_changed)
        self._layout.addWidget(self._functional_list)

        # Settings 折叠区
        self._settings_container = QWidget(self)
        self._settings_layout = QVBoxLayout(self._settings_container)
        self._settings_layout.setContentsMargins(0, 0, 0, 0)
        self._settings_layout.setSpacing(0)

        self._settings_header = QPushButton("▼ Settings", self._settings_container)
        self._settings_header.setFont(font(11))
        self._settings_header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_header.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {C['text_secondary']}; "
            f"border: none; padding: 8px 12px; text-align: left; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._settings_header.clicked.connect(self._toggle_settings)
        self._settings_layout.addWidget(self._settings_header)

        self._settings_list = QListWidget(self._settings_container)
        self._settings_list.setFont(font(11))
        self._settings_list.currentItemChanged.connect(self._on_settings_changed)
        self._settings_layout.addWidget(self._settings_list)

        self._layout.addWidget(self._settings_container)
        self._layout.addStretch()

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_sidebar']}; border: none; color: {C['text_primary']};"
        )
        common_list_style = (
            f"QListWidget {{ background-color: {C['bg_sidebar']}; border: none; outline: none; }}"
            f"QListWidget::item {{ padding: 0px; color: {C['text_secondary']}; }}"
            f"QListWidget::item:selected {{ background-color: {C['bg_selected']}; color: {C['text_primary']}; }}"
            f"QListWidget::item:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._functional_list.setStyleSheet(common_list_style)
        self._settings_list.setStyleSheet(common_list_style)

    def register_functional_tab(self, workspace_id: str, title: str, icon: str) -> None:
        """注册一个顶部功能 Tab。"""
        item = QListWidgetItem(f"{icon} {title}")
        item.setData(Qt.ItemDataRole.UserRole, workspace_id)
        self._functional_items[workspace_id] = item
        self._functional_list.addItem(item)

    def register_settings_category(self, category_id: str, title: str, icon: str) -> None:
        """注册一个 Settings 配置分类。"""
        widget = _SettingsCategoryWidget(
            category_id, title, icon, self._settings_list, None, self._settings_list
        )
        widget._add_btn.clicked.connect(
            lambda _checked=False, cid=category_id: self.add_requested.emit(cid)
        )
        widget.set_selected(False)

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, category_id)
        item.setSizeHint(widget.sizeHint())
        widget._item = item

        self._settings_items[category_id] = item
        self._settings_widgets[category_id] = widget
        self._settings_list.addItem(item)
        self._settings_list.setItemWidget(item, widget)

    def register_module(self, presentation) -> None:
        """兼容旧接口：将 ModulePresentation 注册为功能 Tab。"""
        self.register_functional_tab(presentation.id, presentation.name, presentation.icon)

    def clear_modules(self) -> None:
        """清空所有功能 Tab 与 Settings 分类（兼容旧接口）。"""
        self._functional_items.clear()
        self._settings_items.clear()
        self._settings_widgets.clear()
        self._functional_list.clear()
        self._settings_list.clear()

    def set_selection(self, item_id: str) -> None:
        """设置当前选中项（功能 Tab 或 Settings 分类）。"""
        if item_id in self._functional_items:
            self._functional_list.setCurrentItem(self._functional_items[item_id])
            return
        if item_id in self._settings_items:
            self._settings_list.setCurrentItem(self._settings_items[item_id])
            return

    def set_settings_expanded(self, expanded: bool) -> None:
        """展开或折叠 Settings 区。"""
        self._settings_expanded = expanded
        self._settings_list.setVisible(expanded)
        self._settings_header.setText("▼ Settings" if expanded else "▶ Settings")

    def _on_functional_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        self.selection_changed.emit(item_id)

    def _on_settings_changed(self, current: QListWidgetItem | None, _previous) -> None:
        for widget in self._settings_widgets.values():
            widget.set_selected(False)
        if current is None:
            return
        widget = self._settings_list.itemWidget(current)
        if isinstance(widget, _SettingsCategoryWidget):
            widget.set_selected(True)
        item_id = current.data(Qt.ItemDataRole.UserRole)
        self.selection_changed.emit(item_id)

    def _toggle_settings(self) -> None:
        self.set_settings_expanded(not self._settings_expanded)
