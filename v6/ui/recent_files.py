"""v6/ui/recent_files.py — 最近文件/文件管理器占位。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel

from v6.ui.base import C, font, theme


class FileItem(QWidget):
    """单个文件项。"""

    selected = Signal(str)

    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = path
        self._hover = False
        self.setMouseTracking(True)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        icon = QLabel("□")
        icon.setFont(font(12))
        label = QLabel(path)
        label.setFont(font(11))
        layout.addWidget(icon)
        layout.addWidget(label, 1)
        self._style()
        theme.changed.connect(self._style)

    def _style(self) -> None:
        bg = C["bg_hover"] if self._hover else "transparent"
        self.setStyleSheet(
            f"FileItem {{ background-color: {bg}; border-radius: 4px; }}"
            f"QLabel {{ color: {C['text_primary']}; }}"
        )

    def enterEvent(self, event) -> None:
        self._hover = True
        self._style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self.selected.emit(self._path)
        super().mousePressEvent(event)


class RecentFiles(QScrollArea):
    """最近文件列表占位，使用真实 Demo 数据填充。"""

    file_selected = Signal(str)

    DEMO_FILES = [
        "README.md",
        "docs/v6/SPEC.md",
        "v6/ui/base.py",
        "v6/ui/left_panel.py",
        "tests/v6/test_v6_smoke.py",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        for path in self.DEMO_FILES:
            item = FileItem(path)
            item.selected.connect(self.file_selected.emit)
            layout.addWidget(item)
        layout.addStretch(1)
