"""v6/ui/browser_widget.py — 浏览器组件。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton,
)

from v6.ui.base import C, font, theme


class BrowserWidget(QWidget):
    """浏览器占位：地址栏 + 页面内容区，显示 Demo URL 与内容。"""

    load_requested = Signal(str)
    DEMO_URL = "https://www.bing.com/search?q=Agent+Workbench+V6"
    DEMO_TITLE = "Agent Workbench V6 - 搜索"
    DEMO_BODY = (
        "V6 项目\n"
        "================\n\n"
        "• 从零重写，严格分层\n"
        "• MainWindow → UIController → Manager → Runtime → Engines\n"
        "• 纯 UI 先行，所有占位均以 Demo 数据填充\n\n"
        "[此区域为浏览器占位，后续接入真实 Web 引擎]"
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self.load_url(self.DEMO_URL)
        self.refresh_theme()
        theme.changed.connect(self.refresh_theme)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        self._addr = QLineEdit()
        self._addr.setPlaceholderText("URL...")
        self._addr.returnPressed.connect(self._on_load)
        top.addWidget(self._addr, 1)
        self._load_btn = QPushButton("加载")
        self._load_btn.setFixedWidth(56)
        self._load_btn.clicked.connect(self._on_load)
        top.addWidget(self._load_btn)
        layout.addLayout(top)

        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setFont(font(12))
        self._content.setAcceptRichText(False)
        layout.addWidget(self._content, 1)

    def _on_load(self) -> None:
        url = self._addr.text().strip()
        if url:
            self.load_requested.emit(url)
            self.load_url(url)

    def load_url(self, url: str) -> None:
        """加载 URL 并显示 Demo 内容。"""
        self._addr.setText(url)
        self._content.setPlainText(f"URL: {url}\n标题: {self.DEMO_TITLE}\n\n{self.DEMO_BODY}")

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._addr.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 6px; }}"
        )
        self._content.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_primary']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 6px; }}"
        )
        self._load_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
