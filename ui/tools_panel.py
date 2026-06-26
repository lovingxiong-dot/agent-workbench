"""
ToolsPanel — 工具启用/禁用面板

以树形分组展示全部已注册工具，提供启用复选框与描述 tooltip，
供用户根据当前场景快速开关工具。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton,
)
from PySide6.QtCore import Qt, Signal


# 工具分类映射（基于 TOOL_DEFINITIONS 中的 priority/description 规则）
_TOOL_CATEGORIES = {
    "web_fetch": "网络 / 信息",
    "fetch_financial_news": "网络 / 信息",
    "fetch_macro_data": "网络 / 信息",
    "fetch_stock_data": "量化 / 金融",
    "read_file": "文件 / 系统",
    "write_file": "文件 / 系统",
    "list_dir": "文件 / 系统",
    "run_command": "文件 / 系统",
    "run_as_admin": "文件 / 系统",
    "run_python": "文件 / 系统",
    "run_powershell": "文件 / 系统",
    "run_bash": "文件 / 系统",
    "clipboard_read": "文件 / 系统",
    "clipboard_write": "文件 / 系统",
    "send_notification": "文件 / 系统",
    "list_processes": "文件 / 系统",
    "kill_process": "文件 / 系统",
    "mt5_get_price": "MT5 / 交易",
    "mt5_place_order": "MT5 / 交易",
    "run_backtest": "量化 / 金融",
    "screen_capture": "屏幕 / 媒体",
    "screen_info": "屏幕 / 媒体",
}


class ToolsPanel(QWidget):
    """工具启用面板，按分类展示并允许勾选/取消勾选。"""

    tool_toggled = Signal(str, bool)
    selection_changed = Signal(list)

    def __init__(self, tool_definitions=None, enabled_tools=None, parent=None):
        super().__init__(parent)
        self.setObjectName("toolsPanel")
        self._tool_definitions = tool_definitions or []
        self._enabled_tools = set(enabled_tools or [])
        self._checkboxes = {}
        self._setup_ui()
        self._build_tree()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("工具开关")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #E6EDF3;")
        layout.addWidget(header)

        desc = QLabel("勾选允许 AI 调用的工具；未勾选工具不会出现在 LLM 的工具列表中。")
        desc.setStyleSheet("color: #8B949E; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 6px;
            }
            QTreeWidget::item {
                color: #E6EDF3;
                padding: 4px 0;
            }
            QTreeWidget::item:hover {
                background-color: #1C2128;
            }
        """)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        self.enable_all_btn = QPushButton("全部启用")
        self.enable_all_btn.clicked.connect(self.enable_all)
        btn_layout.addWidget(self.enable_all_btn)

        self.disable_all_btn = QPushButton("全部禁用")
        self.disable_all_btn.clicked.connect(self.disable_all)
        btn_layout.addWidget(self.disable_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _build_tree(self):
        self.tree.clear()
        self._checkboxes.clear()

        # 按分类分组
        groups = {}
        for tool in self._tool_definitions:
            func = tool.get("function", {})
            name = func.get("name", "")
            if not name:
                continue
            category = _TOOL_CATEGORIES.get(name, "其他")
            groups.setdefault(category, []).append(tool)

        for category in sorted(groups.keys()):
            items = groups[category]
            category_item = QTreeWidgetItem(self.tree)
            category_item.setText(0, f"{category} ({len(items)})")
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            category_item.setExpanded(True)

            for tool in sorted(items, key=lambda t: t.get("function", {}).get("name", "")):
                func = tool["function"]
                name = func.get("name", "")
                description = func.get("description", "")

                tool_item = QTreeWidgetItem(category_item)
                tool_item.setFlags(tool_item.flags() | Qt.ItemIsUserCheckable)
                tool_item.setCheckState(0, Qt.Checked if name in self._enabled_tools else Qt.Unchecked)
                tool_item.setText(0, name)
                tool_item.setToolTip(0, description)
                tool_item.setData(0, Qt.UserRole, name)
                self._checkboxes[name] = tool_item

        self.tree.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item, column):
        name = item.data(0, Qt.UserRole)
        if not name:
            return
        checked = item.checkState(0) == Qt.Checked
        if checked:
            self._enabled_tools.add(name)
        else:
            self._enabled_tools.discard(name)
        self.tool_toggled.emit(name, checked)
        self.selection_changed.emit(list(self._enabled_tools))

    def enable_all(self):
        for item in self._checkboxes.values():
            item.setCheckState(0, Qt.Checked)

    def disable_all(self):
        for item in self._checkboxes.values():
            item.setCheckState(0, Qt.Unchecked)

    def get_enabled_tools(self) -> list:
        """返回当前勾选的工具名称列表。"""
        return list(self._enabled_tools)

    def set_enabled_tools(self, names: list):
        """批量设置启用状态。"""
        self._enabled_tools = set(names)
        for name, item in self._checkboxes.items():
            item.setCheckState(0, Qt.Checked if name in self._enabled_tools else Qt.Unchecked)
