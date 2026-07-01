"""
input_area.py — v4 输入区组件

包含：
- SkillSendButton：圆形 SVG 箭头发送按钮
- InputAreaWidget：多行输入框 + 技能按钮 + mode/model 标签 + 发送/停止按钮
"""
import html

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit,
    QLabel, QComboBox, QMenu, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QByteArray, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QAction
from PySide6.QtSvg import QSvgRenderer


DEFAULT_THEME = "dark"


def _svg_icon(path_data: str, color: str, size: int = 18) -> QIcon:
    """根据 SVG path 数据渲染矢量图标。"""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
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


class SkillSendButton(QPushButton):
    """圆形发送按钮，内部绘制上箭头 SVG。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(18, 18))
        self._refresh_icon()
        self.setStyleSheet(
            "QPushButton { border-radius: 18px; border: none; }"
            "QPushButton:hover { background-color: rgba(128,128,128,0.15); }"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._refresh_icon()

    def _refresh_icon(self):
        # 上箭头 path
        arrow_path = "M12 19V5M5 12l7-7 7 7"
        color = self._theme.get("text_inverse", "#ffffff")
        self.setIcon(_svg_icon(arrow_path, color, 18))
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._theme['send_btn']}; "
            f"border-radius: 18px; border: none; }}"
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
        self.setFont(QFont("Segoe UI", 13))

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
    """底部输入区：输入框 + 技能按钮 + mode/model 标签 + 发送/停止按钮。"""

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
        root.setContentsMargins(24, 12, 24, 16)
        root.setSpacing(8)

        # ── 输入框行 ──
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        # 技能按钮
        self.skill_btn = QPushButton("+")
        self.skill_btn.setFixedSize(32, 32)
        self.skill_btn.setCursor(Qt.PointingHandCursor)
        self.skill_btn.setToolTip("技能菜单")
        self.skill_btn.clicked.connect(self.skill_menu_requested.emit)
        input_row.addWidget(self.skill_btn)

        # 多行输入框
        self.text_edit = InputTextEdit()
        self.text_edit.send_requested.connect(self.send_requested.emit)
        input_row.addWidget(self.text_edit, 1)

        # 发送/停止按钮
        self.send_btn = SkillSendButton(self._theme)
        self.send_btn.clicked.connect(self.send_requested.emit)
        input_row.addWidget(self.send_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(64, 36)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        input_row.addWidget(self.stop_btn)

        root.addLayout(input_row)

        # ── 底部标签行 ──
        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)
        tag_row.addStretch()

        # 模式下拉（以标签样式展示）
        self.mode_selector = QComboBox()
        self.mode_selector.setFixedWidth(70)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)
        tag_row.addWidget(self.mode_selector)

        # 模型下拉（以标签样式展示）
        self.model_selector = QComboBox()
        self.model_selector.setFixedWidth(90)
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        tag_row.addWidget(self.model_selector)

        root.addLayout(tag_row)
        self._apply_theme_styles()

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme_styles()
        self.send_btn.set_theme(theme)

    def _apply_theme_styles(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")

        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                line-height: 1.65;
            }}
        """)

        self.skill_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['tag_bg']};
                color: {t['tag_text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                font-size: 16px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {t['bg_hover']}; }}
        """)

        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['stop_btn']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {t['stop_btn_hover']}; }}
        """)

        combo_style = f"""
            QComboBox {{
                background-color: {t['tag_bg']};
                color: {t['tag_text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 14px; }}
            QComboBox QAbstractItemView {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
            }}
        """
        self.mode_selector.setStyleSheet(combo_style)
        self.model_selector.setStyleSheet(combo_style)

    def set_models(self, providers: dict, current: str):
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        self._models = providers
        for name, cfg in providers.items():
            model = cfg.get("model", "?") if isinstance(cfg, dict) else "?"
            self.model_selector.addItem(f"{name}", name)
        idx = self.model_selector.findData(current)
        if idx >= 0:
            self.model_selector.setCurrentIndex(idx)
        self.model_selector.blockSignals(False)

    def set_modes(self, modes: list, current: str):
        self.mode_selector.blockSignals(True)
        self.mode_selector.clear()
        self._modes = modes
        display_map = {"ask": "ask", "plan": "plan", "craft": "craft"}
        for mode in modes:
            self.mode_selector.addItem(display_map.get(mode, mode), mode)
        idx = self.mode_selector.findData(current)
        if idx >= 0:
            self.mode_selector.setCurrentIndex(idx)
        self.mode_selector.blockSignals(False)

    def set_model(self, name: str):
        idx = self.model_selector.findData(name)
        if idx >= 0:
            self.model_selector.setCurrentIndex(idx)

    def set_mode(self, name: str):
        idx = self.mode_selector.findData(name)
        if idx >= 0:
            self.mode_selector.setCurrentIndex(idx)

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

    def _on_model_changed(self):
        name = self.model_selector.currentData()
        if name:
            self.model_changed.emit(name)

    def _on_mode_changed(self):
        mode = self.mode_selector.currentData()
        if mode:
            self.mode_changed.emit(mode)
