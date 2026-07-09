"""agent_workbench/ui/dialogs/feedback_dialog.py — Feedback 提交对话框。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font


class FeedbackDialog(QDialog):
    """收集用户反馈并保存为 markdown 的轻量对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Feedback")
        self.setMinimumWidth(480)
        self.setMinimumHeight(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("💡 Send Feedback")
        header.setFont(font(16, bold=True))
        layout.addWidget(header)

        hint = QLabel("Share what feels off, missing, or great. One sentence is enough.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Title (e.g. Welcome page feels empty)")
        layout.addWidget(self._title_edit)

        self._content_edit = QPlainTextEdit()
        self._content_edit.setPlaceholderText("Describe your experience...")
        layout.addWidget(self._content_edit, 1)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self._button_box.accepted.connect(self._on_save)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

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

    def _on_save(self) -> None:
        """禁止空标题或空内容提交。"""
        if not self._title_edit.text().strip() or not self._content_edit.toPlainText().strip():
            return
        self.accept()

    def feedback(self) -> tuple[str, str]:
        """返回 (title, content)。仅在 exec() == Accepted 后调用。"""
        return self._title_edit.text().strip(), self._content_edit.toPlainText().strip()
