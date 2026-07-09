"""agent_workbench/ui/workbench/tool_bar.py — 快捷工具栏。

根据当前选中的 ModulePresentation.actions 动态生成按钮。
ToolBar 不持有 Runtime，只接收 ActionPresentation 列表。
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from v6.ui.base import C, font

from agent_workbench.ui.workbench.presentation import ActionPresentation


class ToolBar(QWidget):
    """Workbench 快捷工具栏。

    通过 set_actions() 接收 ActionPresentation 列表，动态重建按钮。
    按钮触发 action_triggered(name) 信号。
    """

    action_triggered = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 6, 12, 6)
        self._layout.setSpacing(8)
        self._buttons: dict[str, QPushButton] = {}
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_darker']}; color: {C['text_secondary']}; border-top: 1px solid {C['border']};"
        )

    def set_actions(self, actions: list[ActionPresentation]) -> None:
        """用 ActionPresentation 列表重建工具栏按钮。

        Args:
            actions: 当前选中 ModulePresentation 的操作列表。
        """
        for btn in self._buttons.values():
            btn.deleteLater()
        self._buttons.clear()

        for action in sorted(actions, key=lambda a: a.order):
            btn = QPushButton(action.icon + action.label, self)
            btn.setFont(font(10))
            btn.setToolTip(action.description)
            btn.setEnabled(action.enabled)
            if action.danger:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: #dc3545; color: {C['text_inverse']}; border: none; border-radius: 4px; padding: 4px 12px; }}"
                )
            btn.clicked.connect(lambda _checked, name=action.name: self.action_triggered.emit(name))
            self._layout.addWidget(btn)
            self._buttons[action.name] = btn

        self._layout.addStretch()

    def actions_state(self) -> dict[str, bool]:
        """返回当前按钮的启用状态，供测试使用。"""
        return {name: btn.isEnabled() for name, btn in self._buttons.items()}
