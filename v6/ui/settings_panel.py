"""v6/ui/settings_panel.py — 设置面板。

大厂 Agent 风格内联参数配置面板：
- 模型参数 (temperature, max_tokens, top_p)
- Agent 配置 (system prompt, model, tools)
- 主题设置 (dark/light)
- Provider 设置 (API key, base URL)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QLineEdit, QTextEdit, QScrollArea, QSizePolicy,
    QComboBox, QCheckBox, QFrame,
)

from v6.ui.base import C, font, mono_font, theme


class _SectionHeader(QWidget):
    """可折叠区域标题栏。"""

    toggled = Signal()

    def __init__(self, title: str, expanded: bool = True, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expanded = expanded
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(6)
        self._arrow = QLabel("\u25bc" if expanded else "\u25b6")
        self._arrow.setFont(font(9))
        self._arrow.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        hl.addWidget(self._arrow)
        self._title = QLabel(title)
        self._title.setFont(font(12, bold=True))
        self._title.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        hl.addWidget(self._title, 1)

    def mousePressEvent(self, event) -> None:
        self._expanded = not self._expanded
        self._arrow.setText("\u25bc" if self._expanded else "\u25b6")
        self.toggled.emit()
        super().mousePressEvent(event)

    def is_expanded(self) -> bool:
        return self._expanded

    def refresh_theme(self) -> None:
        self._arrow.setStyleSheet(f"color: {C['text_muted']}; background: transparent;")
        self._title.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")


class _SliderRow(QWidget):
    """标签 + 滑块 + 数值显示。"""

    value_changed = Signal(float)

    def __init__(self, label: str, min_v: float, max_v: float, step: float, current: float, parent=None):
        super().__init__(parent)
        self._step = step
        self.setFixedHeight(36)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFont(font(10))
        lbl.setFixedWidth(80)
        hl.addWidget(lbl)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(int(min_v / step), int(max_v / step))
        self._slider.setValue(int(current / step))
        self._slider.valueChanged.connect(self._on_slide)
        hl.addWidget(self._slider, 1)
        self._val = QLabel(f"{current:.1f}")
        self._val.setFont(mono_font(10))
        self._val.setFixedWidth(36)
        self._val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hl.addWidget(self._val)

    def _on_slide(self) -> None:
        v = self._slider.value() * self._step
        self._val.setText(f"{v:.1f}")
        self.value_changed.emit(v)

    def value(self) -> float:
        return self._slider.value() * self._step

    def set_value(self, v: float) -> None:
        self._slider.setValue(int(v / self._step))
        self._val.setText(f"{v:.1f}")

    def refresh_theme(self) -> None:
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {C['border']}; height: 4px; border-radius: 2px; }}"
            f"QSlider::handle:horizontal {{ background: {C['accent']}; width: 12px; height: 12px; "
            f"margin: -4px 0; border-radius: 6px; }}"
            f"QSlider::sub-page:horizontal {{ background: {C['accent']}; border-radius: 2px; }}"
        )


class _ComboRow(QWidget):
    """标签 + 下拉框。"""

    value_changed = Signal(str)

    def __init__(self, label: str, options: list[str], current: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFont(font(10))
        lbl.setFixedWidth(80)
        hl.addWidget(lbl)
        self._combo = QComboBox()
        self._combo.addItems(options)
        self._combo.setCurrentText(current)
        self._combo.currentTextChanged.connect(self.value_changed.emit)
        hl.addWidget(self._combo, 1)

    def value(self) -> str:
        return self._combo.currentText()

    def set_value(self, v: str) -> None:
        self._combo.setCurrentText(v)

    def refresh_theme(self) -> None:
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._combo.setStyleSheet(
            f"QComboBox {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 11px; }}"
            f"QComboBox:hover {{ border-color: {C['accent']}; }}"
            f"QComboBox QAbstractItemView {{ background-color: {C['bg_card']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; selection-background-color: {C['accent']}; }}"
        )


class _InputRow(QWidget):
    """标签 + 文本输入。"""

    text_changed = Signal(str)

    def __init__(self, label: str, placeholder: str, current: str, password: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFont(font(10))
        lbl.setFixedWidth(80)
        hl.addWidget(lbl)
        self._edit = QLineEdit()
        self._edit.setText(current)
        self._edit.setPlaceholderText(placeholder)
        if password:
            self._edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit.textChanged.connect(self.text_changed.emit)
        hl.addWidget(self._edit, 1)

    def value(self) -> str:
        return self._edit.text()

    def set_value(self, v: str) -> None:
        self._edit.setText(v)

    def refresh_theme(self) -> None:
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._edit.setStyleSheet(
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 4px 8px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border-color: {C['accent']}; }}"
        )


class _ToggleRow(QWidget):
    """标签 + 复选框。"""

    toggled = Signal(bool)

    def __init__(self, label: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFont(font(10))
        lbl.setFixedWidth(80)
        hl.addWidget(lbl)
        self._check = QCheckBox()
        self._check.setChecked(checked)
        self._check.toggled.connect(self.toggled.emit)
        hl.addWidget(self._check)
        hl.addStretch(1)

    def is_checked(self) -> bool:
        return self._check.isChecked()

    def set_checked(self, v: bool) -> None:
        self._check.setChecked(v)

    def refresh_theme(self) -> None:
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {C['text_secondary']}; background: transparent;")
        self._check.setStyleSheet(
            f"QCheckBox {{ color: {C['text_primary']}; spacing: 4px; }}"
            f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; "
            f"border: 1px solid {C['border']}; background-color: {C['bg_input']}; }}"
            f"QCheckBox::indicator:checked {{ background-color: {C['accent']}; border-color: {C['accent']}; }}"
        )


class SettingsPanel(QScrollArea):
    """设置面板 — 大厂 Agent 风格内联参数配置。"""

    # 模型参数
    temperature_changed = Signal(float)
    max_tokens_changed = Signal(int)
    top_p_changed = Signal(float)
    # Agent 配置
    system_prompt_changed = Signal(str)
    agent_model_changed = Signal(str)
    tools_enabled_toggled = Signal(bool)
    # 主题
    theme_changed = Signal(str)
    # Provider
    api_key_changed = Signal(str)
    provider_url_changed = Signal(str)
    # 关卡
    apply_clicked = Signal()
    reset_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._rows: list = []
        self._build()

    def _build(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标题 ──
        title = QLabel("\u2699 \u8bbe\u7f6e")
        title.setFont(font(14, bold=True))
        title.setFixedHeight(40)
        title.setContentsMargins(16, 0, 16, 0)
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── 模型参数 ──
        model_header = _SectionHeader("\u6a21\u578b\u53c2\u6570")
        model_header.toggled.connect(lambda: self._toggle_section(model_header, model_content))
        layout.addWidget(model_header)
        model_content = QWidget()
        mcl = QVBoxLayout(model_content)
        mcl.setContentsMargins(0, 0, 0, 0)
        mcl.setSpacing(4)
        self._temp = _SliderRow("\u6e29\u5ea6", 0.0, 2.0, 0.1, 0.7)
        self._temp.value_changed.connect(self.temperature_changed.emit)
        mcl.addWidget(self._temp)
        self._max_tok = _SliderRow("\u6700\u5927 token", 256, 32768, 256, 4096)
        self._max_tok.value_changed.connect(lambda v: self.max_tokens_changed.emit(int(v)))
        mcl.addWidget(self._max_tok)
        self._top_p = _SliderRow("Top P", 0.0, 1.0, 0.05, 1.0)
        self._top_p.value_changed.connect(self.top_p_changed.emit)
        mcl.addWidget(self._top_p)
        layout.addWidget(model_content)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        # ── Agent 配置 ──
        agent_header = _SectionHeader("Agent \u914d\u7f6e")
        agent_header.toggled.connect(lambda: self._toggle_section(agent_header, agent_content))
        layout.addWidget(agent_header)
        agent_content = QWidget()
        acl = QVBoxLayout(agent_content)
        acl.setContentsMargins(0, 0, 0, 0)
        acl.setSpacing(4)
        self._sys_prompt = QTextEdit()
        self._sys_prompt.setPlaceholderText("\u7cfb\u7edf\u63d0\u793a\u8bcd...")
        self._sys_prompt.setMaximumHeight(80)
        self._sys_prompt.setFont(font(10))
        self._sys_prompt.textChanged.connect(
            lambda: self.system_prompt_changed.emit(self._sys_prompt.toPlainText())
        )
        acl.addWidget(self._sys_prompt)
        self._agent_model = _ComboRow("\u9ed8\u8ba4\u6a21\u578b", ["gpt-4o", "gpt-4o-mini", "claude-3.5"], "gpt-4o")
        self._agent_model.value_changed.connect(self.agent_model_changed.emit)
        acl.addWidget(self._agent_model)
        self._tools_enabled = _ToggleRow("\u542f\u7528\u5de5\u5177", True)
        self._tools_enabled.toggled.connect(self.tools_enabled_toggled.emit)
        acl.addWidget(self._tools_enabled)
        layout.addWidget(agent_content)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setFixedHeight(1)
        layout.addWidget(sep3)

        # ── 主题 ──
        theme_header = _SectionHeader("\u4e3b\u9898")
        theme_header.toggled.connect(lambda: self._toggle_section(theme_header, theme_content))
        layout.addWidget(theme_header)
        theme_content = QWidget()
        tcl = QVBoxLayout(theme_content)
        tcl.setContentsMargins(0, 0, 0, 0)
        tcl.setSpacing(4)
        self._theme_combo = _ComboRow("\u4e3b\u9898\u6a21\u5f0f", ["\u6df1\u8272", "\u6d45\u8272"], "\u6df1\u8272")
        self._theme_combo.value_changed.connect(
            lambda v: self.theme_changed.emit("dark" if v == "\u6df1\u8272" else "light")
        )
        tcl.addWidget(self._theme_combo)
        layout.addWidget(theme_content)

        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setFixedHeight(1)
        layout.addWidget(sep4)

        # ── Provider ──
        provider_header = _SectionHeader("Provider")
        provider_header.toggled.connect(lambda: self._toggle_section(provider_header, provider_content))
        layout.addWidget(provider_header)
        provider_content = QWidget()
        pcl = QVBoxLayout(provider_content)
        pcl.setContentsMargins(0, 0, 0, 0)
        pcl.setSpacing(4)
        self._api_key = _InputRow("API Key", "sk-...", "", password=True)
        self._api_key.text_changed.connect(self.api_key_changed.emit)
        pcl.addWidget(self._api_key)
        self._provider_url = _InputRow("Base URL", "https://api.openai.com/v1", "https://api.openai.com/v1")
        self._provider_url.text_changed.connect(self.provider_url_changed.emit)
        pcl.addWidget(self._provider_url)
        layout.addWidget(provider_content)

        layout.addStretch(1)

        # ── 底部操作按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 8, 12, 8)
        btn_row.setSpacing(8)
        self._apply_btn = QPushButton("\u5e94\u7528")
        self._apply_btn.setFixedHeight(32)
        self._apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_btn.clicked.connect(self.apply_clicked.emit)
        self._reset_btn = QPushButton("\u91cd\u7f6e")
        self._reset_btn.setFixedHeight(32)
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.clicked.connect(self.reset_clicked.emit)
        btn_row.addWidget(self._apply_btn, 1)
        btn_row.addWidget(self._reset_btn, 1)
        layout.addLayout(btn_row)

        self.setWidget(container)
        self._rows = [
            model_header, agent_header, theme_header, provider_header,
            self._temp, self._max_tok, self._top_p,
            self._sys_prompt, self._agent_model, self._tools_enabled,
            self._theme_combo, self._api_key, self._provider_url,
        ]
        self._apply_theme()

    def _toggle_section(self, header: _SectionHeader, content: QWidget) -> None:
        content.setVisible(header.is_expanded())

    def get_values(self) -> dict:
        return {
            "temperature": self._temp.value(),
            "max_tokens": int(self._max_tok.value()),
            "top_p": self._top_p.value(),
            "system_prompt": self._sys_prompt.toPlainText(),
            "agent_model": self._agent_model.value(),
            "tools_enabled": self._tools_enabled.is_checked(),
            "theme": "dark" if self._theme_combo.value() == "\u6df1\u8272" else "light",
            "api_key": self._api_key.value(),
            "provider_url": self._provider_url.value(),
        }

    def set_values(self, values: dict) -> None:
        if "temperature" in values:
            self._temp.set_value(values["temperature"])
        if "max_tokens" in values:
            self._max_tok.set_value(values["max_tokens"])
        if "top_p" in values:
            self._top_p.set_value(values["top_p"])
        if "system_prompt" in values:
            self._sys_prompt.setPlainText(values["system_prompt"])
        if "agent_model" in values:
            self._agent_model.set_value(values["agent_model"])
        if "tools_enabled" in values:
            self._tools_enabled.set_checked(values["tools_enabled"])
        if "theme" in values:
            self._theme_combo.set_value("\u6df1\u8272" if values["theme"] == "dark" else "\u6d45\u8272")
        if "api_key" in values:
            self._api_key.set_value(values["api_key"])
        if "provider_url" in values:
            self._provider_url.set_value(values["provider_url"])

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"QScrollArea {{ background-color: {C['bg_card']}; border: none; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 3px; border: none; margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {C['border']}; min-height: 24px; max-width: 3px; border-radius: 1px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}"
        )
        self._apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['accent']}; color: {C['text_inverse']}; "
            f"border: none; border-radius: 6px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue']}; }}"
        )
        self._reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        for row in self._rows:
            if hasattr(row, "refresh_theme"):
                row.refresh_theme()
        self._sys_prompt.setStyleSheet(
            f"QTextEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 6px; font-size: 10px; }}"
            f"QTextEdit:focus {{ border-color: {C['accent']}; }}"
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.resize(380, 720)
    panel = SettingsPanel()
    win.setCentralWidget(panel)
    win.show()
    QTimer = __import__("PySide6.QtCore", fromlist=["QTimer"]).QTimer
    QTimer.singleShot(200, win.close)
    sys.exit(app.exec())