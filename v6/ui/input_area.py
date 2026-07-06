"""v6/ui/input_area.py — 中区输入区。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy

from v6.ui.base import C, font


class InputArea(QWidget):
    """输入区：文本框、技能按钮、模式/模型标签、发送/停止按钮。"""

    send_clicked = Signal()
    stop_clicked = Signal()
    mode_tag_clicked = Signal()
    model_tag_clicked = Signal()
    skill_btn_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self.setMaximumHeight(200)
        self._mode = "Agent"
        self._model = "gpt-4o"
        self._running = False
        self._build()
        self.refresh_theme()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self._skill_btn = QPushButton("⚡ 技能")
        self._skill_btn.setFixedSize(72, 34)
        self._skill_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skill_btn.clicked.connect(self.skill_btn_clicked.emit)
        layout.addWidget(self._skill_btn)

        tag_layout = QHBoxLayout()
        tag_layout.setSpacing(6)
        self._mode_btn = self._tag_btn(self._mode)
        self._mode_btn.clicked.connect(self.mode_tag_clicked.emit)
        self._model_btn = self._tag_btn(self._model)
        self._model_btn.clicked.connect(self.model_tag_clicked.emit)
        tag_layout.addWidget(self._mode_btn)
        tag_layout.addWidget(self._model_btn)
        tag_layout.addStretch()
        layout.addLayout(tag_layout)

        self._text = QTextEdit()
        self._text.setPlaceholderText("输入消息，Enter 发送，Shift+Enter 换行...")
        self._text.setAcceptRichText(False)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._text.setFont(font(13))
        layout.addWidget(self._text, 1)

        self._send_btn = self._action_btn("发送", C["accent"], C["text_inverse"])
        self._send_btn.clicked.connect(self.send_clicked.emit)
        self._stop_btn = self._action_btn("停止", C["btn_bg"], C["text_primary"])
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        self._stop_btn.hide()
        layout.addWidget(self._send_btn)
        layout.addWidget(self._stop_btn)

    def _tag_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['text_secondary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 0 8px; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {C['text_primary']}; background-color: {C['bg_hover']}; }}"
        )
        return btn

    def _action_btn(self, text: str, bg: str, fg: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(64, 34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg}; color: {fg}; border: none; border-radius: 6px; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue'] if text == '发送' else C['btn_hover']}; }}"
        )
        return btn

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._mode_btn.setText(mode)

    def set_model(self, model: str) -> None:
        self._model = model
        self._model_btn.setText(model)

    def text(self) -> str:
        return self._text.toPlainText()

    def clear_text(self) -> None:
        self._text.clear()

    def set_running(self, running: bool) -> None:
        self._running = running
        if running:
            self._send_btn.hide()
            self._stop_btn.show()
        else:
            self._stop_btn.hide()
            self._send_btn.show()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if self.text().strip():
                self.send_clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']}; border-top: 1px solid {C['border']};")
        self._text.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 8px; padding: 6px; }}"
        )
        self._mode_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['text_secondary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 0 8px; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {C['text_primary']}; background-color: {C['bg_hover']}; }}"
        )
        self._model_btn.setStyleSheet(self._mode_btn.styleSheet())
        self._skill_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['accent']}; color: {C['text_inverse']}; "
            f"border: none; border-radius: 6px; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue']}; }}"
        )
        self._stop_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = InputArea()
    w.show()
    from PySide6.QtCore import QTimer

    QTimer.singleShot(300, w.close)
    sys.exit(app.exec())
