"""agent_workbench/ui/workbench/control_bar.py — Workbench 控制栏。

位于 ToolBar 和 StatusBar 之间，提供 Agent / Provider / Model 运行时选择器。
UI 不直接访问 Runtime，所有切换通过信号通知 WorkbenchUIController。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from v6.ui.base import C, font


class ControlBar(QWidget):
    """Workbench 控制栏 — Agent / Provider / Model 选择器。

    通过信号通知外部控制器执行切换，自身不持有 Runtime 引用。
    """

    agent_changed = Signal(str)   # agent_id
    provider_changed = Signal(str)  # provider_name
    model_changed = Signal(str)    # model_name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 4, 12, 4)
        self._layout.setSpacing(12)

        # Agent 选择器
        self._agent_label = QLabel("Agent:")
        self._agent_label.setFont(font(10))
        self._agent_combo = QComboBox()
        self._agent_combo.setFont(font(10))
        self._agent_combo.setMinimumWidth(120)
        self._agent_combo.currentTextChanged.connect(self._on_agent_changed)

        # Provider 选择器
        self._provider_label = QLabel("Provider:")
        self._provider_label.setFont(font(10))
        self._provider_combo = QComboBox()
        self._provider_combo.setFont(font(10))
        self._provider_combo.setMinimumWidth(100)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)

        # Model 选择器
        self._model_label = QLabel("Model:")
        self._model_label.setFont(font(10))
        self._model_combo = QComboBox()
        self._model_combo.setFont(font(10))
        self._model_combo.setMinimumWidth(120)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)

        self._layout.addWidget(self._agent_label)
        self._layout.addWidget(self._agent_combo)
        self._layout.addWidget(self._provider_label)
        self._layout.addWidget(self._provider_combo)
        self._layout.addWidget(self._model_label)
        self._layout.addWidget(self._model_combo)
        self._layout.addStretch()

        self._suppress_signals = False
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_darker']}; border-top: 1px solid {C['border']};"
            f"border-bottom: 1px solid {C['border']};"
        )
        combo_style = (
            f"QComboBox {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 3px; padding: 2px 6px; }}"
            f"QComboBox:hover {{ border-color: {C['text_secondary']}; }}"
            f"QComboBox::drop-down {{ border: none; width: 16px; }}"
        )
        self._agent_combo.setStyleSheet(combo_style)
        self._provider_combo.setStyleSheet(combo_style)
        self._model_combo.setStyleSheet(combo_style)
        label_style = f"color: {C['text_secondary']};"
        self._agent_label.setStyleSheet(label_style)
        self._provider_label.setStyleSheet(label_style)
        self._model_label.setStyleSheet(label_style)

    def set_agents(self, agents: list[dict], active_id: str) -> None:
        """设置 Agent 下拉列表。

        Args:
            agents: [{"id": "...", "name": "..."}, ...]
            active_id: 当前活跃的 agent_id
        """
        self._suppress_signals = True
        self._agent_combo.clear()
        for a in agents:
            self._agent_combo.addItem(a["name"], a["id"])
        idx = self._agent_combo.findData(active_id)
        if idx >= 0:
            self._agent_combo.setCurrentIndex(idx)
        self._suppress_signals = False

    def set_providers(self, providers: list[str], active: str) -> None:
        """设置 Provider 下拉列表。

        Args:
            providers: ["echo", "deepseek", "agnes", ...]
            active: 当前活跃的 provider_name
        """
        self._suppress_signals = True
        self._provider_combo.clear()
        for p in providers:
            self._provider_combo.addItem(p)
        idx = self._provider_combo.findText(active)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)
        self._suppress_signals = False

    def set_models(self, models: list[str], active: str) -> None:
        """设置 Model 下拉列表。

        Args:
            models: ["echo-default", "agnes-2.0-flash", ...]
            active: 当前活跃的 model_name
        """
        self._suppress_signals = True
        self._model_combo.clear()
        for m in models:
            self._model_combo.addItem(m)
        idx = self._model_combo.findText(active)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        self._suppress_signals = False

    def _on_agent_changed(self, text: str) -> None:
        if self._suppress_signals:
            return
        idx = self._agent_combo.currentIndex()
        agent_id = self._agent_combo.itemData(idx)
        if agent_id:
            self.agent_changed.emit(agent_id)

    def _on_provider_changed(self, text: str) -> None:
        if self._suppress_signals:
            return
        self.provider_changed.emit(text)

    def _on_model_changed(self, text: str) -> None:
        if self._suppress_signals:
            return
        self.model_changed.emit(text)