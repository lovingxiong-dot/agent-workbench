"""agent_workbench/ui/dialogs/base.py — 新增配置项对话框基类。

为 Add*Dialog 提供统一布局、主题样式与 result() 契约。
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C


class AddConfigItemDialog(QDialog):
    """新增配置项对话框基类。

    子类只需在 __init__ 中向 _form 添加字段，并实现 _build_result()。
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(16, 16, 16, 16)

        self._form = QFormLayout()
        self._form.setSpacing(10)
        self._form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._layout.addLayout(self._form)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._layout.addWidget(self._button_box)

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {C['bg_primary']};
                color: {C['text_primary']};
            }}
            QLabel {{
                color: {C['text_secondary']};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {C['bg_input']};
                color: {C['text_primary']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                padding: 6px 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C['accent']};
            }}
            QComboBox {{
                background-color: {C['bg_input']};
                color: {C['text_primary']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                padding: 6px 8px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {C['bg_input']};
                color: {C['text_primary']};
                selection-background-color: {C['bg_selected']};
            }}
            QCheckBox {{
                color: {C['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                background-color: {C['bg_input']};
                border: 1px solid {C['border']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {C['accent']};
                border: 1px solid {C['accent']};
            }}
            QPlainTextEdit {{
                background-color: {C['bg_input']};
                color: {C['text_primary']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                padding: 6px 8px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {C['accent']};
            }}
            QPushButton {{
                background-color: {C['btn_bg']};
                color: {C['text_primary']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {C['btn_hover']};
            }}
            """
        )

    def result(self) -> dict[str, Any]:
        """若用户未点击 Save，返回空字典；否则返回 _build_result()。"""
        if super().result() != QDialog.DialogCode.Accepted:
            return {}
        return self._build_result()

    @abstractmethod
    def _build_result(self) -> dict[str, Any]:
        """子类实现：收集表单字段并返回配置字典。"""
        ...

    @staticmethod
    def _line_edit(placeholder: str = "") -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit
