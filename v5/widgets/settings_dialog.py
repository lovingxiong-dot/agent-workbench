"""V5 设置对话框 — 编辑 app.theme / last_mode / last_model。"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
)
from PySide6.QtCore import Qt, Signal
from .base import theme, V5_THEMES, C, font


class SettingsDialog(QDialog):
    """轻量设置对话框：主题、默认模式、默认模型。"""
    settings_applied = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self._config = config
        self.setWindowTitle("设置")
        self.setFixedWidth(320)
        self._setup_ui()
        self._load_values()
        self._apply_theme_style()
        theme.changed.connect(self._apply_theme_style)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 主题
        theme_row = QHBoxLayout()
        theme_row.addWidget(self._label("主题"))
        self._theme_box = QComboBox()
        self._theme_box.addItems(list(V5_THEMES.keys()))
        theme_row.addWidget(self._theme_box, 1)
        layout.addLayout(theme_row)

        # 默认模式
        mode_row = QHBoxLayout()
        mode_row.addWidget(self._label("默认模式"))
        self._mode_box = QComboBox()
        self._mode_box.addItems(["ask", "plan", "craft"])
        mode_row.addWidget(self._mode_box, 1)
        layout.addLayout(mode_row)

        # 默认模型
        model_row = QHBoxLayout()
        model_row.addWidget(self._label("默认模型"))
        self._model_box = QComboBox()
        providers = self._config.get("llm_providers", {}) if self._config else {}
        self._model_box.addItems(list(providers.keys()) if providers else ["tool-agent"])
        model_row.addWidget(self._model_box, 1)
        layout.addLayout(model_row)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font(10))
        lbl.setFixedWidth(64)
        lbl.setStyleSheet(f"color: {C['text_primary']}; background: transparent;")
        return lbl

    def _load_values(self):
        self._theme_box.setCurrentText(self._config.get("app.theme", theme.name))
        self._mode_box.setCurrentText(self._config.get("app.last_mode", "ask"))
        self._model_box.setCurrentText(self._config.get("app.last_model", "tool-agent"))

    def _on_save(self):
        self._config.set("app.theme", self._theme_box.currentText())
        self._config.set("app.last_mode", self._mode_box.currentText())
        self._config.set("app.last_model", self._model_box.currentText())
        self._config.save()
        self.settings_applied.emit()
        self.accept()

    def _apply_theme_style(self):
        self.setStyleSheet(f"background-color: {C['bg_card']};")
        for box in (self._theme_box, self._mode_box, self._model_box):
            box.setStyleSheet(
                f"QComboBox {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 4px; padding: 2px 6px; }}"
            )
