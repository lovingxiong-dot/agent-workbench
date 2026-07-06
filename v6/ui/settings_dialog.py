"""v6/ui/settings_dialog.py — 设置对话框占位。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
)

from v6.ui.base import C, font, theme


class SettingsDialog(QDialog):
    """设置对话框占位：主题/模式/模型下拉选择。"""

    theme_changed = Signal(str)
    mode_changed = Signal(str)
    model_changed = Signal(str)

    THEMES = ["dark", "light"]
    MODES = ["chat", "agent", "coding"]
    MODELS = ["gpt-4o", "claude-3-5-sonnet", "deepseek-chat"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(320, 220)
        self._build()
        self._style()
        theme.changed.connect(self._style)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        self._theme = self._add_row(layout, "主题", self.THEMES)
        self._mode = self._add_row(layout, "模式", self.MODES)
        self._model = self._add_row(layout, "模型", self.MODELS)
        self._theme.currentTextChanged.connect(self.theme_changed.emit)
        self._mode.currentTextChanged.connect(self.mode_changed.emit)
        self._model.currentTextChanged.connect(self.model_changed.emit)
        layout.addStretch(1)
        close = QPushButton("关闭")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_row(self, layout: QVBoxLayout, label: str, items: list[str]) -> QComboBox:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFont(font(12))
        combo = QComboBox()
        combo.addItems(items)
        row.addWidget(lbl)
        row.addWidget(combo, 1)
        layout.addLayout(row)
        return combo

    def _style(self) -> None:
        self.setStyleSheet(
            f"QDialog {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; }}"
            f"QLabel {{ color: {C['text_primary']}; }}"
            f"QComboBox {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px; }}"
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dlg = SettingsDialog()
    dlg.theme_changed.connect(lambda t: print("theme", t))
    dlg.mode_changed.connect(lambda m: print("mode", m))
    dlg.model_changed.connect(lambda m: print("model", m))
    dlg.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(1000, dlg.close)
    sys.exit(app.exec())
