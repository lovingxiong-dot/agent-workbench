"""
input_area.py — v4 输入区组件 (精确对齐 SVG 设计稿)

SVG 布局：
  [────────── 输入框 ───────────] [🔵]  发送按钮叠在输入框右边
  [+]  [模式 ask ▼]  [模型 flash ▼]       标签行在输入框下方
"""
import html

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit,
    QLabel, QMenu, QSizePolicy, QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QByteArray, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QAction
from PySide6.QtSvg import QSvgRenderer


DEFAULT_THEME = "dark"


def _svg_icon(path_data: str, color: str, size: int = 18) -> QIcon:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path_data}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class TagSelectButton(QPushButton):
    """标签样式按钮：标签名 + 值 + chevron ▼，点击弹出菜单选择。"""

    clicked_value = Signal(str)

    def __init__(self, label_text: str, theme: dict, parent=None):
        super().__init__(parent)
        self._label = label_text
        self._value = ""
        self._options: list[tuple[str, str]] = []
        self._theme = theme
        self._menu: QMenu | None = None
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._show_menu)
        self._apply_theme()

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def set_options(self, options: list[tuple[str, str]], current: str = ""):
        self._options = options
        self._menu = QMenu(self)
        for display, data in options:
            action = self._menu.addAction(display)
            action.setData(data)
            action.triggered.connect(lambda checked, d=data: self._on_select(d))
        self.set_value(current)

    def set_value(self, value: str):
        self._value = value
        self._update_text()

    def _update_text(self):
        t = self._theme
        label_color = t.get("tag_text", t["text_secondary"])
        value_color = t["text_primary"]
        self.setText(
            f'<span style="color:{label_color};font-size:9px;margin-right:4px;">{self._label}</span>'
            f'<span style="color:{value_color};font-size:10px;font-weight:500;">{self._value}</span>'
            f'<span style="color:{label_color};font-size:9px;margin-left:2px;">▼</span>'
        )

    def _show_menu(self):
        if self._menu:
            self._menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def _on_select(self, data: str):
        self.set_value(data)
        self.clicked_value.emit(data)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(
            f"QPushButton {{ background-color: {t['tag_bg']}; color: {t['tag_text']}; "
            f"border: 0.5px solid {t['border']}; border-radius: 6px; "
            f"padding: 2px 6px; font-size: 12px; text-align: left; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        self._update_text()


class SkillSendButton(QPushButton):
    """圆形发送按钮，内部绘制上箭头 SVG（r=12, d=24）。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(12, 12))
        self._refresh_icon()

    def set_theme(self, theme: dict):
        self._theme = theme
        self._refresh_icon()

    def _refresh_icon(self):
        # SVG send arrow: filled up-arrow (matching ui-full-dark.svg)
        arrow_path = "M12 5L8 11H11V17H13V11H16Z"
        color = self._theme.get("text_inverse", "#ffffff")
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
            f'viewBox="0 0 24 24" fill="{color}" stroke="none">'
            f'<path d="{arrow_path}"/></svg>'
        )
        from PySide6.QtCore import QByteArray
        from PySide6.QtGui import QPixmap, QPainter
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._theme['send_btn']}; "
            f"border-radius: 12px; border: none; }}"
            f"QPushButton:hover {{ background-color: {self._theme['send_btn_hover']}; }}"
            f"QPushButton:disabled {{ background-color: {self._theme['border']}; }}"
        )


class InputTextEdit(QTextEdit):
    """多行输入框：Enter 发送，Shift+Enter 换行。"""
    send_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入 '/' 快速使用技能")
        self.setMaximumHeight(120)
        self.setMinimumHeight(44)
        self.setFont(QFont("Segoe UI", 12))

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.insertPlainText("\n")
            else:
                self.send_requested.emit()
            return
        super().keyPressEvent(event)


class InputAreaWidget(QWidget):
    """底部输入区：输入框 + 叠放在输入框右内侧的发送按钮 + 下方标签行。"""

    send_requested = Signal()
    stop_requested = Signal()
    skill_menu_requested = Signal()
    model_changed = Signal(str)
    mode_changed = Signal(str)

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._models: dict = {}
        self._modes: list = []
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(8)

        # ── 输入框行（发送按钮叠放在输入框右内侧）──
        input_container = QWidget()
        input_container.setStyleSheet("background-color: transparent;")
        container_layout = QGridLayout(input_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 多行输入框（占满整个容器）
        self.text_edit = InputTextEdit()
        self.text_edit.send_requested.connect(self.send_requested.emit)
        container_layout.addWidget(self.text_edit, 0, 0)

        # 发送按钮叠放在输入框右内侧，用 QGridLayout 同 cell
        send_wrapper = QWidget()
        send_wrapper.setStyleSheet("background-color: transparent;")
        send_layout = QVBoxLayout(send_wrapper)
        send_layout.setContentsMargins(0, 0, 6, 6)
        send_layout.setSpacing(0)

        # 发送/停止按钮
        self.send_btn = SkillSendButton(self._theme)
        self.send_btn.clicked.connect(self.send_requested.emit)
        send_layout.addStretch()
        send_layout.addWidget(self.send_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(56, 24)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)

        # 用 QGridWidget 同 cell 放置：text_edit (大) + send_wrapper (右下角)
        container_layout.addWidget(send_wrapper, 0, 0, Qt.AlignRight | Qt.AlignBottom)

        root.addWidget(input_container)

        # ── 底部标签行：技能按钮 + 模式标签 + 模型标签 ──
        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)

        # 技能按钮（圆形，r=10 → d=20）
        self.skill_btn = QPushButton("+")
        self.skill_btn.setFixedSize(20, 20)
        self.skill_btn.setCursor(Qt.PointingHandCursor)
        self.skill_btn.setToolTip("技能菜单")
        self.skill_btn.clicked.connect(self.skill_menu_requested.emit)
        tag_row.addWidget(self.skill_btn)

        # 模式标签（SVG: w=62 h=22）
        self.mode_tag = TagSelectButton("模式", self._theme)
        self.mode_tag.setFixedWidth(62)
        self.mode_tag.clicked_value.connect(self._on_mode_changed)
        tag_row.addWidget(self.mode_tag)

        # 模型标签（SVG: w=76 h=22）
        self.model_tag = TagSelectButton("模型", self._theme)
        self.model_tag.setFixedWidth(76)
        self.model_tag.clicked_value.connect(self._on_model_changed)
        tag_row.addWidget(self.model_tag)

        tag_row.addStretch()
        root.addLayout(tag_row)
        self._apply_theme_styles()

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme_styles()
        self.send_btn.set_theme(theme)
        self.mode_tag.set_theme(theme)
        self.model_tag.set_theme(theme)

    def _apply_theme_styles(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")

        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 0.5px solid {t['border']};
                border-radius: 8px;
                padding: 8px 28px 8px 12px;
                font-size: 12px;
                line-height: 1.65;
            }}
        """)

        self.skill_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.get('tag_bg', t['bg_input'])};
                color: {t['text_secondary']};
                border: 0.5px solid {t['border']};
                border-radius: 10px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {t['bg_hover']}; }}
        """)

        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['stop_btn']};
                color: {t['text_primary']};
                border: 0.5px solid {t['border']};
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {t['stop_btn_hover']}; }}
        """)

    def set_models(self, providers: dict, current: str):
        options = []
        for name, cfg in providers.items():
            model = cfg.get("model", "?") if isinstance(cfg, dict) else "?"
            display = name if len(name) <= 8 else name[:7] + "…"
            options.append((display, name))
        self._models = providers
        self.model_tag.set_options(options, current)

    def set_modes(self, modes: list, current: str):
        self._modes = modes
        display_map = {"ask": "ask", "plan": "plan", "craft": "craft"}
        options = [(display_map.get(m, m), m) for m in modes]
        self.mode_tag.set_options(options, current)

    def set_model(self, name: str):
        self.model_tag.set_value(name)

    def set_mode(self, name: str):
        self.mode_tag.set_value(name)

    def set_streaming(self, active: bool):
        self.stop_btn.setVisible(active)
        self.send_btn.setVisible(not active)

    def set_send_enabled(self, enabled: bool):
        self.send_btn.setEnabled(enabled)

    def clear_input(self):
        self.text_edit.setPlainText("")

    def toPlainText(self) -> str:
        return self.text_edit.toPlainText()

    def setPlainText(self, text: str):
        self.text_edit.setPlainText(text)

    def setFocus(self):
        self.text_edit.setFocus()

    def _on_model_changed(self, name: str):
        if name:
            self.model_changed.emit(name)

    def _on_mode_changed(self, mode: str):
        if mode:
            self.mode_changed.emit(mode)
