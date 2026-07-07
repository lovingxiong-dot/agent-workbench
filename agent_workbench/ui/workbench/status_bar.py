"""agent_workbench/ui/workbench/status_bar.py — 底部状态栏。

实时显示 Runtime 核心状态：Runtime / Provider / Model / Session / Token / Latency / Profile / Trace / Memory。
状态栏不持有 Runtime，只接收 PresentationModel 更新。
"""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from v6.ui.base import C, font


class StatusBar(QWidget):
    """Workbench 状态栏。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 6, 12, 6)
        self._layout.setSpacing(16)

        self._items: dict[str, QLabel] = {
            "runtime": self._add_item("Runtime", "● Stopped"),
            "provider": self._add_item("Provider", "—"),
            "model": self._add_item("Model", "—"),
            "session": self._add_item("Session", "—"),
            "token": self._add_item("Token", "—"),
            "latency": self._add_item("Latency", "—"),
            "profile": self._add_item("Profile", "—"),
            "trace": self._add_item("Trace", "—"),
            "memory": self._add_item("Memory", "—"),
        }

        self._layout.addStretch()
        self._style()

    def _add_item(self, label: str, value: str) -> QLabel:
        text = f"{label}: {value}"
        lbl = QLabel(text, self)
        lbl.setFont(font(10))
        self._layout.addWidget(lbl)
        return lbl

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_darker']}; color: {C['text_secondary']}; border-top: 1px solid {C['border']};"
        )

    def set_runtime(self, status: str) -> None:
        self._items["runtime"].setText(f"Runtime: ● {status}")

    def set_provider(self, name: str) -> None:
        self._items["provider"].setText(f"Provider: {name}")

    def set_model(self, name: str) -> None:
        self._items["model"].setText(f"Model: {name}")

    def set_session(self, info: str) -> None:
        self._items["session"].setText(f"Session: {info}")

    def set_token(self, used: int, total: int) -> None:
        self._items["token"].setText(f"Token: {used} / {total}")

    def set_latency(self, ms: float) -> None:
        self._items["latency"].setText(f"Latency: {ms:.1f}s")

    def set_profile(self, name: str) -> None:
        self._items["profile"].setText(f"Profile: {name}")

    def set_trace(self, level: str) -> None:
        self._items["trace"].setText(f"Trace: {level}")

    def set_memory(self, status: str) -> None:
        self._items["memory"].setText(f"Memory: {status}")
