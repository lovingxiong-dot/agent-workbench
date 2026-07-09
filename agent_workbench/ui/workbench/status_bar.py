"""agent_workbench/ui/workbench/status_bar.py — 底部状态栏。

状态栏不持有 Runtime，只接收并聚合 PresentationModel.statistics。
新增 Module 的统计项会自动出现在状态栏，无需修改本文件。
"""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from v6.ui.base import C, font

from agent_workbench.ui.workbench.presentation import StatisticPresentation


class StatusBar(QWidget):
    """Workbench 状态栏。

    通过 set_statistics() 接收聚合后的 StatisticPresentation 列表，
    动态重建状态项。UI 只认识 PresentationModel，不认识 Runtime 对象。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 6, 12, 6)
        self._layout.setSpacing(16)
        self._items: dict[str, QLabel] = {}
        self._layout.addStretch()
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_darker']}; color: {C['text_secondary']}; border-top: 1px solid {C['border']};"
        )

    def set_statistics(self, statistics: list[StatisticPresentation]) -> None:
        """用聚合后的统计列表重建状态栏。

        Args:
            statistics: 来自一个或多个 ModulePresentation 的 StatisticPresentation。
        """
        for lbl in self._items.values():
            lbl.deleteLater()
        self._items.clear()

        for stat in statistics:
            lbl = QLabel(self._format(stat), self)
            lbl.setFont(font(10))
            lbl.setToolTip(stat.description)
            # 插入到 stretch 之前，保证右侧留白
            self._layout.insertWidget(self._layout.count() - 1, lbl)
            self._items[stat.name] = lbl

    def _format(self, stat: StatisticPresentation) -> str:
        value = stat.value
        if stat.format == "bytes" and isinstance(value, (int, float)):
            value = self._format_bytes(value)
        elif stat.format == "percent" and isinstance(value, (int, float)):
            value = f"{value}%"
        elif stat.format == "duration" and isinstance(value, (int, float)):
            unit = stat.unit or "s"
            value = f"{value:.1f}{unit}"
        elif isinstance(value, float):
            value = f"{value:.1f}"
        unit = f" {stat.unit}" if stat.unit and stat.format != "duration" else ""
        return f"{stat.label}: {value}{unit}"

    @staticmethod
    def _format_bytes(value: float) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    def values(self) -> dict[str, str]:
        """返回当前所有状态项文本，供测试使用。"""
        return {key: lbl.text() for key, lbl in self._items.items()}
