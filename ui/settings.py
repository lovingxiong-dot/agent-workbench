"""
SettingsPage — 嵌入式设置页

将原本 SettingsDialog 中的 LLM 提供商 / 用户规则 / 界面日志三栏内容
提取为可嵌入任意容器（如右侧工作区标签页）的 QWidget。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLabel, QPushButton, QTextEdit, QCheckBox, QSpinBox,
    QTabWidget, QMessageBox,
)
from PySide6.QtCore import Signal

from ui.dialogs import ProviderFormDialog


class SettingsPage(QWidget):
    """可嵌入的设置页，提供 LLM 提供商、用户规则、界面日志三个选项卡。"""

    providers_changed = Signal()
    ui_settings_changed = Signal()

    def __init__(self, llm_registry, parent=None, config_service=None):
        super().__init__(parent)
        self.llm_registry = llm_registry
        self.config_service = config_service
        self.setObjectName("settingsPage")
        self.resize(720, 520)
        self._setup_ui()
        self._load_table()
        self._load_rules()
        self._load_ui_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E6EDF3;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #30363D; border-radius: 8px; background-color: #0D1117; }
            QTabBar::tab { background: #161B22; color: #8B949E; padding: 8px 20px; border: none; }
            QTabBar::tab:selected { color: #58A6FF; border-bottom: 2px solid #58A6FF; background: #0D1117; }
        """)

        # ── Tab 1: LLM 提供商 ────────────────────
        self.tabs.addTab(self._build_providers_tab(), "LLM 提供商")
        # ── Tab 2: 用户规则 ──────────────────────
        self.tabs.addTab(self._build_rules_tab(), "用户规则")
        # ── Tab 3: 界面 / 日志 ────────────────────
        self.tabs.addTab(self._build_ui_tab(), "界面 / 日志")

        layout.addWidget(self.tabs)

    def _build_providers_tab(self):
        tab = QWidget()
        pl = QVBoxLayout(tab)
        pl.setSpacing(10)
        pl.setContentsMargins(12, 12, 12, 12)

        desc = QLabel("在此添加、编辑或删除模型提供商。")
        desc.setStyleSheet("color: #8B949E; font-size: 12px;")
        pl.addWidget(desc)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "Base URL", "模型", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        pl.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ 添加提供商")
        self.add_btn.setStyleSheet("QPushButton { background-color: #1F6FEB; } QPushButton:hover { background-color: #388BFD; }")
        self.add_btn.clicked.connect(self._add_provider)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        pl.addLayout(btn_layout)

        return tab

    def _build_rules_tab(self):
        tab = QWidget()
        rl = QVBoxLayout(tab)
        rl.setSpacing(10)
        rl.setContentsMargins(12, 12, 12, 12)

        rules_desc = QLabel("每行一条规则，将自动注入到所有模式的 system prompt 末尾。")
        rules_desc.setStyleSheet("color: #8B949E; font-size: 12px;")
        rl.addWidget(rules_desc)

        self.rules_editor = QTextEdit()
        self.rules_editor.setPlaceholderText("示例:\n始终使用中文回答\n禁止调用 mt5_place_order 除非明确要求")
        self.rules_editor.setStyleSheet("""
            QTextEdit {
                background-color: #161B22; color: #E6EDF3; border: 1px solid #30363D;
                border-radius: 8px; padding: 10px; font-size: 13px;
            }
        """)
        rl.addWidget(self.rules_editor)

        rules_btn_layout = QHBoxLayout()
        self.save_rules_btn = QPushButton("保存规则")
        self.save_rules_btn.setStyleSheet("QPushButton { background-color: #238636; } QPushButton:hover { background-color: #2EA043; }")
        self.save_rules_btn.clicked.connect(self._save_rules)
        rules_btn_layout.addStretch()
        rules_btn_layout.addWidget(self.save_rules_btn)
        rl.addLayout(rules_btn_layout)

        return tab

    def _build_ui_tab(self):
        tab = QWidget()
        ul = QVBoxLayout(tab)
        ul.setSpacing(14)
        ul.setContentsMargins(12, 12, 12, 12)

        ui_desc = QLabel("配置日志面板的显示与容量。")
        ui_desc.setStyleSheet("color: #8B949E; font-size: 12px;")
        ul.addWidget(ui_desc)

        self.log_visible_cb = QCheckBox("显示右侧 Agent 日志面板")
        self.log_visible_cb.setStyleSheet("color: #E6EDF3;")
        ul.addWidget(self.log_visible_cb)

        max_lines_layout = QHBoxLayout()
        max_lines_label = QLabel("日志最大保留行数:")
        max_lines_label.setStyleSheet("color: #E6EDF3;")
        max_lines_layout.addWidget(max_lines_label)
        self.log_max_lines_spin = QSpinBox()
        self.log_max_lines_spin.setRange(100, 10000)
        self.log_max_lines_spin.setSingleStep(100)
        self.log_max_lines_spin.setFixedWidth(120)
        max_lines_layout.addWidget(self.log_max_lines_spin)
        max_lines_layout.addStretch()
        ul.addLayout(max_lines_layout)

        ui_save_layout = QHBoxLayout()
        ui_save_layout.addStretch()
        self.save_ui_btn = QPushButton("保存界面设置")
        self.save_ui_btn.setStyleSheet("QPushButton { background-color: #238636; } QPushButton:hover { background-color: #2EA043; }")
        self.save_ui_btn.clicked.connect(self._save_ui_settings)
        ui_save_layout.addWidget(self.save_ui_btn)
        ul.addLayout(ui_save_layout)
        ul.addStretch()

        return tab

    # ── 数据加载与保存 ─────────────────────────
    def _load_table(self):
        self.table.setRowCount(0)
        providers = self.llm_registry.list_providers()
        for name, cfg in providers.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(cfg.get("base_url", "")))
            self.table.setItem(row, 2, QTableWidgetItem(cfg.get("model", "")))

            action_w = QWidget()
            al = QHBoxLayout(action_w)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(48, 22)
            edit_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 6px; }")
            edit_btn.clicked.connect(lambda checked, n=name: self._edit_provider(n))
            al.addWidget(edit_btn)

            del_btn = QPushButton("删除")
            del_btn.setFixedSize(48, 22)
            del_btn.setStyleSheet("QPushButton { background-color: #DA3633; font-size: 11px; padding: 2px 6px; } QPushButton:hover { background-color: #F85149; }")
            del_btn.clicked.connect(lambda checked, n=name: self._delete_provider(n))
            al.addWidget(del_btn)

            self.table.setCellWidget(row, 3, action_w)

    def _add_provider(self):
        dlg = ProviderFormDialog(self)
        if dlg.exec() == ProviderFormDialog.Accepted:
            name, cfg = dlg.get_data()
            self.llm_registry.add_provider(name, cfg)
            self._load_table()
            self.providers_changed.emit()

    def _edit_provider(self, name):
        cfg = self.llm_registry.get_provider_config(name)
        dlg = ProviderFormDialog(self, name, cfg)
        if dlg.exec() == ProviderFormDialog.Accepted:
            new_name, new_cfg = dlg.get_data()
            if new_name != name:
                self.llm_registry.remove_provider(name)
            self.llm_registry.add_provider(new_name, new_cfg)
            self._load_table()
            self.providers_changed.emit()

    def _delete_provider(self, name):
        reply = QMessageBox.question(self, "确认删除", f"确定要删除提供商 「{name}」吗？")
        if reply == QMessageBox.Yes:
            self.llm_registry.remove_provider(name)
            self._load_table()
            self.providers_changed.emit()

    def _load_rules(self):
        if not self.config_service:
            return
        rules = self.config_service.config.get("user_rules", [])
        if isinstance(rules, list):
            self.rules_editor.setPlainText("\n".join(rules))

    def _save_rules(self):
        if not self.config_service:
            QMessageBox.warning(self, "保存失败", "未提供配置服务")
            return
        try:
            text = self.rules_editor.toPlainText().strip()
            rules = [line.strip() for line in text.split("\n") if line.strip()]
            self.config_service.config["user_rules"] = rules
            self.config_service.save()
            QMessageBox.information(self, "已保存", f"已保存 {len(rules)} 条规则。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _load_ui_settings(self):
        if not self.config_service:
            return
        ui_cfg = self.config_service.get("ui", {}).get("log_panel", {})
        self.log_visible_cb.setChecked(ui_cfg.get("visible", True))
        self.log_max_lines_spin.setValue(ui_cfg.get("max_lines", 500))

    def _save_ui_settings(self):
        if not self.config_service:
            QMessageBox.warning(self, "保存失败", "未提供配置服务")
            return
        try:
            ui_cfg = self.config_service.config.setdefault("ui", {}).setdefault("log_panel", {})
            ui_cfg["visible"] = self.log_visible_cb.isChecked()
            ui_cfg["max_lines"] = self.log_max_lines_spin.value()
            self.config_service.save()
            self.ui_settings_changed.emit()
            QMessageBox.information(self, "已保存", "界面设置已保存。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
