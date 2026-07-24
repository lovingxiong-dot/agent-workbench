"""agent_workbench/ui/workbench/provider_workspace.py — Provider 管理工作区。

展示所有已配置的 AI Provider，支持添加、编辑、删除、测试连接。
每个 Provider 以卡片形式展示：名称、类型、模型列表、状态、操作按钮。
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font


class ProviderCard(QFrame):
    """单个 Provider 卡片。"""

    edit_requested = Signal(str)  # provider_name
    delete_requested = Signal(str)  # provider_name
    test_requested = Signal(str)  # provider_name

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            f"ProviderCard {{ background-color: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 8px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # 第一行：名称 + 类型 badge + 状态
        header = QHBoxLayout()
        header.setSpacing(10)

        name = QLabel(self._config.get("name", "Unknown"), self)
        name.setFont(font(14, bold=True))
        name.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        header.addWidget(name)

        ptype = self._config.get("type", "unknown")
        badge = QLabel(f" {ptype} ", self)
        badge.setFont(font(10))
        badge.setStyleSheet(
            f"background-color: {C['accent_blue']}22; color: {C['accent_blue']}; "
            f"border: 1px solid {C['accent_blue']}44; border-radius: 4px; padding: 2px 6px;"
        )
        header.addWidget(badge)

        enabled = self._config.get("enabled", True)
        status = QLabel("● Active" if enabled else "○ Disabled", self)
        status.setFont(font(10))
        status_color = C.get("accent_green", "#4CAF50") if enabled else C["text_muted"]
        status.setStyleSheet(f"color: {status_color}; border: none;")
        header.addWidget(status)

        header.addStretch()

        # 操作按钮
        test_btn = QPushButton("Test", self)
        test_btn.setFont(font(10))
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet(self._btn_style())
        test_btn.clicked.connect(lambda: self.test_requested.emit(self._config.get("name", "")))
        header.addWidget(test_btn)

        edit_btn = QPushButton("Edit", self)
        edit_btn.setFont(font(10))
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet(self._btn_style())
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._config.get("name", "")))
        header.addWidget(edit_btn)

        delete_btn = QPushButton("Delete", self)
        delete_btn.setFont(font(10))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['bg_card']}; color: {C.get('accent_red', '#E53935')}; "
            f"border: 1px solid {C.get('accent_red', '#E53935')}44; border-radius: 4px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ background-color: {C.get('accent_red', '#E53935')}22; }}"
        )
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._config.get("name", "")))
        header.addWidget(delete_btn)

        layout.addLayout(header)

        # 第二行：模型列表
        models = self._config.get("models", [self._config.get("model", "")])
        if isinstance(models, str):
            models = [models]
        if models:
            models_text = "Models: " + ", ".join(m for m in models if m)
            models_label = QLabel(models_text, self)
            models_label.setFont(font(11))
            models_label.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
            models_label.setWordWrap(True)
            layout.addWidget(models_label)

        # 第三行：Base URL（如果有）
        base_url = self._config.get("base_url", "")
        if base_url:
            url_label = QLabel(f"Endpoint: {base_url}", self)
            url_label.setFont(font(10))
            url_label.setStyleSheet(f"color: {C['text_muted']}; border: none;")
            url_label.setWordWrap(True)
            layout.addWidget(url_label)

    def _btn_style(self) -> str:
        return (
            f"QPushButton {{ background-color: {C['bg_card']}; color: {C['text_secondary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; color: {C['text_primary']}; }}"
        )


class ProviderWorkspaceItem(QWidget):
    """Provider 管理工作区。"""

    add_requested = Signal()
    edit_requested = Signal(str)  # provider_name
    delete_requested = Signal(str)  # provider_name
    test_requested = Signal(str)  # provider_name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._providers: list[dict[str, Any]] = []
        self._cards: list[ProviderCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._layout.addWidget(scroll)

        self._container = QWidget(scroll)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(24, 24, 24, 24)
        self._container_layout.setSpacing(16)
        scroll.setWidget(self._container)

        # 标题
        title = QLabel("Provider Management", self._container)
        title.setFont(font(20, bold=True))
        title.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        self._container_layout.addWidget(title)

        subtitle = QLabel("Configure AI model providers for your agents.", self._container)
        subtitle.setFont(font(12))
        subtitle.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
        self._container_layout.addWidget(subtitle)

        self._container_layout.addSpacing(8)

        # Provider 卡片容器
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(12)
        self._container_layout.addLayout(self._cards_layout)

        # 空状态提示
        self._empty_label = QLabel("No providers configured.\nClick '+ Add Provider' to add your first AI provider.", self._container)
        self._empty_label.setFont(font(12))
        self._empty_label.setStyleSheet(f"color: {C['text_muted']}; border: none; padding: 32px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._container_layout.addWidget(self._empty_label)

        self._container_layout.addStretch()

        # 底部添加按钮
        footer = QHBoxLayout()
        footer.addStretch()
        add_btn = QPushButton("+ Add Provider", self._container)
        add_btn.setFont(font(12, bold=True))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['accent_blue']}; color: white; "
            f"border: none; border-radius: 6px; padding: 10px 24px; }}"
            f"QPushButton:hover {{ background-color: {C['accent_blue']}DD; }}"
        )
        add_btn.clicked.connect(self.add_requested.emit)
        footer.addWidget(add_btn)
        footer.addStretch()
        self._container_layout.addLayout(footer)

        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def set_providers(self, providers: list[dict[str, Any]]) -> None:
        """刷新 Provider 卡片列表。"""
        self._providers = providers

        # 清除旧卡片
        for card in self._cards:
            card.setParent(None)
            self._cards_layout.removeWidget(card)
        self._cards.clear()

        # 显示/隐藏空状态
        self._empty_label.setVisible(len(providers) == 0)

        # 创建新卡片
        for config in providers:
            card = ProviderCard(config, self._container)
            card.edit_requested.connect(self.edit_requested.emit)
            card.delete_requested.connect(self.delete_requested.emit)
            card.test_requested.connect(self.test_requested.emit)
            self._cards_layout.addWidget(card)
            self._cards.append(card)

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: ViewModel-driven API (Configuration-Driven Principle P5)
    # ──────────────────────────────────────────────────────────

    def set_view_models(self, view_models: list[Any]) -> None:
        """通过 ProviderViewModel 列表刷新卡片（v6.10 推荐入口）。

        Args:
            view_models: provider.view_models.ProviderViewModel 列表。
        """
        self.set_providers([_view_model_to_dict(vm) for vm in view_models])


def _view_model_to_dict(vm: Any) -> dict[str, Any]:
    """ProviderViewModel → legacy dict config 转换。

    仅用于 ProviderCard 的 dict 接口（保持向后兼容）。
    """
    enabled = vm.metadata.get("enabled", "True") == "True"
    models = list(vm.models)
    return {
        "name": vm.name,
        "type": vm.protocol,
        "models": models,
        "model": models[0] if models else "",
        "base_url": vm.base_url,
        "enabled": enabled,
        "status": vm.status,
        "provider_id": vm.provider_id,
        "has_api_key": vm.has_api_key,
    }