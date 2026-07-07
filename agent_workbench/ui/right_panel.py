"""agent_workbench/ui/right_panel.py — V6 右栏扩展。

在 v6.ui.right_panel.RightPanel 基础上新增「配置」标签页，用于内嵌
Agent Configuration 面板。完全保留 V6 右栏的设计与信号契约。
"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from v6.ui.right_panel import RightPanel as V6RightPanel
from v6.ui.tab_button import TabButton


class WorkbenchRightPanel(V6RightPanel):
    """Agent Workbench 专用右栏：新增配置标签页。"""

    CONFIG_TAB_TYPE = "config"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_idx = len(self._tab_btns)
        self._tab_defs.append(("配置", self.CONFIG_TAB_TYPE, 70))

        btn = TabButton("配置", self.CONFIG_TAB_TYPE, width=70, active=False)
        btn.clicked.connect(lambda _c=False, idx=self._config_idx: self._switch_tab(idx))
        btn.close_clicked.connect(lambda idx=self._config_idx: self._close_tab(idx))
        self._tab_btns.append(btn)

        # 在标签栏的 stretch 之前插入配置按钮
        tb_layout = self._tab_bar.layout()
        insert_idx = max(tb_layout.count() - 2, 0)
        tb_layout.insertWidget(insert_idx, btn)

        # 配置页容器
        self._config_page = QWidget()
        self._config_page.setLayout(QVBoxLayout())
        self._config_page.layout().setContentsMargins(0, 0, 0, 0)
        self._config_page.layout().setSpacing(0)
        self._stack.addWidget(self._config_page)

    def set_config_panel(self, widget: QWidget) -> None:
        """将 Agent Configuration 面板设置到配置标签页中。"""
        layout = self._config_page.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        layout.addWidget(widget)
