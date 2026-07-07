"""agent_workbench/ui/config_panel.py — Agent Configuration 面板。

布局：
- 左侧：模块列表（Overview / Runtime / Session / Config / Profile / Prompt / Model / Tool / Memory / Strategy / Trace）。
- 右侧：当前模块配置 JSON 编辑器 + 查看/修改/保存/应用 按钮。

第一版使用通用 JSON 编辑器满足"查看 / 修改 / 保存 / 热更新"四件事，
后续可为每个模块定制专用表单。
"""
from __future__ import annotations

import json
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agent_workbench.controller import WorkbenchController


class AgentConfigPanel(QWidget):
    """Agent Configuration 主面板。"""

    MODULES = [
        "overview",
        "runtime",
        "session",
        "config",
        "profile",
        "prompt",
        "model",
        "tool",
        "memory",
        "strategy",
        "trace",
    ]

    def __init__(self, controller: WorkbenchController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._current_module = "overview"
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        layout.addWidget(splitter)

        # 左侧模块列表
        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.addWidget(QLabel("模块", self))

        self._module_list = QListWidget(self)
        for name in self.MODULES:
            item = QListWidgetItem(name.capitalize())
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._module_list.addItem(item)
        self._module_list.currentItemChanged.connect(self._on_module_changed)
        left_layout.addWidget(self._module_list)
        splitter.addWidget(left)

        # 右侧编辑器
        right = QWidget(self)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)

        self._title_label = QLabel("Overview", self)
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self._title_label)

        self._desc_label = QLabel("", self)
        right_layout.addWidget(self._desc_label)

        self._editor = QTextEdit(self)
        self._editor.setReadOnly(True)
        right_layout.addWidget(self._editor)

        btn_layout = QHBoxLayout()
        self._edit_btn = QPushButton("修改", self)
        self._edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self._edit_btn)

        self._save_btn = QPushButton("保存", self)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        self._apply_btn = QPushButton("应用（热更新）", self)
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self._apply_btn)

        self._cancel_btn = QPushButton("取消", self)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._cancel_btn)

        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right)
        splitter.setSizes([200, 600])

    def _on_module_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        self._current_module = current.data(Qt.ItemDataRole.UserRole)
        self._refresh()

    def _refresh(self) -> None:
        """刷新当前模块显示。"""
        module = self._current_module
        self._title_label.setText(module.capitalize())

        if module == "overview":
            self._desc_label.setText("当前 Agent 运行概览。")
            data = self._controller.get_overview()
            self._editor.setReadOnly(True)
        elif module == "config":
            self._desc_label.setText("完整 YAML 配置。")
            data = self._controller.get_config_value("")
            self._editor.setReadOnly(True)
        else:
            form = self._controller.get_module_form(module)
            self._desc_label.setText(form.get("description", ""))
            data = self._controller.get_config_value(module, {})
            self._editor.setReadOnly(True)

        self._editor.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        self._edit_btn.setEnabled(module != "overview")
        self._save_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._cancel_btn.setEnabled(False)

    def _on_edit(self) -> None:
        """进入编辑模式。"""
        if self._current_module == "overview":
            return
        self._editor.setReadOnly(False)
        self._save_btn.setEnabled(True)
        self._apply_btn.setEnabled(True)
        self._cancel_btn.setEnabled(True)

    def _on_save(self) -> None:
        """保存配置到 YAML。"""
        try:
            data = json.loads(self._editor.toPlainText())
        except json.JSONDecodeError as exc:
            QMessageBox.warning(self, "格式错误", f"JSON 解析失败：\n{exc}")
            return

        module = self._current_module
        if module == "config":
            # Config 模块：直接替换整个配置
            for key, value in data.items():
                self._controller.set_config_value(key, value)
        else:
            self._controller.set_config_value(module, data)

        self._editor.setReadOnly(True)
        self._save_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)
        self._cancel_btn.setEnabled(False)
        QMessageBox.information(self, "保存成功", "配置已保存到 YAML。")

    def _on_apply(self) -> None:
        """应用配置并触发 Runtime 热更新。"""
        self._on_save()
        self._controller.apply_config_change(self._current_module)
        self._refresh()
        QMessageBox.information(self, "应用成功", f"{self._current_module.capitalize()} 模块已热更新。")

    def _on_cancel(self) -> None:
        """取消编辑，恢复原始配置。"""
        self._refresh()
