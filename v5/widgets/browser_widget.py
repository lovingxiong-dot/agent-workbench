"""V5 嵌入式浏览器组件 — 基于 QWebEngineView。"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFont
from .base import theme, C, font, svg_icon

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _WEBENGINE_AVAILABLE = True
except Exception:
    _WEBENGINE_AVAILABLE = False


class BrowserWidget(QWidget):
    """嵌入式浏览器：地址栏、前进/后退/刷新/主页。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._home_url = "https://www.bing.com"
        self._setup_ui()
        self._apply_theme()
        theme.changed.connect(self._apply_theme)
        if _WEBENGINE_AVAILABLE:
            self.load_url(self._home_url)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if not _WEBENGINE_AVAILABLE:
            lbl = QLabel("当前环境未安装 PySide6 WebEngine，浏览器不可用。")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {C['text_muted']};")
            layout.addWidget(lbl)
            return

        # 地址栏
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        self._back_btn = QPushButton("◀")
        self._back_btn.setFixedSize(28, 28)
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setToolTip("后退")
        self._back_btn.clicked.connect(self._on_back)
        nav_row.addWidget(self._back_btn)

        self._forward_btn = QPushButton("▶")
        self._forward_btn.setFixedSize(28, 28)
        self._forward_btn.setCursor(Qt.PointingHandCursor)
        self._forward_btn.setToolTip("前进")
        self._forward_btn.clicked.connect(self._on_forward)
        nav_row.addWidget(self._forward_btn)

        self._refresh_btn = QPushButton("↻")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.setToolTip("刷新")
        self._refresh_btn.clicked.connect(self._on_refresh)
        nav_row.addWidget(self._refresh_btn)

        self._home_btn = QPushButton("⌂")
        self._home_btn.setFixedSize(28, 28)
        self._home_btn.setCursor(Qt.PointingHandCursor)
        self._home_btn.setToolTip("主页")
        self._home_btn.clicked.connect(self._on_home)
        nav_row.addWidget(self._home_btn)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("输入网址...")
        self._url_input.returnPressed.connect(self._on_navigate)
        nav_row.addWidget(self._url_input, 1)

        self._go_btn = QPushButton("Go")
        self._go_btn.setFixedWidth(44)
        self._go_btn.setCursor(Qt.PointingHandCursor)
        self._go_btn.clicked.connect(self._on_navigate)
        nav_row.addWidget(self._go_btn)

        layout.addLayout(nav_row)

        # 浏览器视图
        self._web_view = QWebEngineView()
        self._web_view.loadFinished.connect(self._on_load_finished)
        self._web_view.urlChanged.connect(self._on_url_changed)
        layout.addWidget(self._web_view, 1)

    def _apply_theme(self):
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        if not _WEBENGINE_AVAILABLE:
            return
        btn_style = (
            f"QPushButton {{ background-color: {C['tag_bg']}; color: {C['text_secondary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._back_btn.setStyleSheet(btn_style)
        self._forward_btn.setStyleSheet(btn_style)
        self._refresh_btn.setStyleSheet(btn_style)
        self._home_btn.setStyleSheet(btn_style)
        self._go_btn.setStyleSheet(btn_style)
        self._url_input.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        )

    def set_home_page(self, url: str):
        self._home_url = url

    def load_url(self, url: str):
        if not _WEBENGINE_AVAILABLE:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self._web_view.setUrl(QUrl(url))
        self._url_input.setText(url)

    def load_html(self, html: str):
        if not _WEBENGINE_AVAILABLE:
            return
        self._web_view.setHtml(html)

    def _on_navigate(self):
        self.load_url(self._url_input.text().strip())

    def _on_back(self):
        if _WEBENGINE_AVAILABLE:
            self._web_view.back()

    def _on_forward(self):
        if _WEBENGINE_AVAILABLE:
            self._web_view.forward()

    def _on_refresh(self):
        if _WEBENGINE_AVAILABLE:
            self._web_view.reload()

    def _on_home(self):
        self.load_url(self._home_url)

    def _on_load_finished(self, ok: bool):
        if not ok and _WEBENGINE_AVAILABLE:
            self._web_view.setHtml("<h3>页面加载失败</h3>")

    def _on_url_changed(self, url: QUrl):
        self._url_input.setText(url.toString())
