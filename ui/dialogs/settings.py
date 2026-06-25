from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
                                QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                                QWidget, QMessageBox, QTabWidget, QTextEdit)
from PySide6.QtCore import Signal
import yaml
import os


class ProviderFormDialog(QDialog):
    def __init__(self, parent=None, name="", config=None):
        super().__init__(parent)
        self.setWindowTitle("编辑提供商" if name else "添加提供商")
        self.resize(440, 280)
        self._setup_ui(name, config)

    def _setup_ui(self, name, config):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("如: tool-agent, deepseek, openai")
        layout.addRow("名称:", self.name_edit)

        self.url_edit = QLineEdit(config.get("base_url", "") if config else "")
        self.url_edit.setPlaceholderText("如: http://localhost:11434/v1")
        layout.addRow("Base URL:", self.url_edit)

        self.key_edit = QLineEdit(config.get("api_key", "") if config else "")
        self.key_edit.setPlaceholderText("API Key（本地 Ollama 填 not-needed）")
        self.key_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.key_edit)

        self.model_edit = QLineEdit(config.get("model", "") if config else "")
        self.model_edit.setPlaceholderText("如: qwen3:4b, gpt-4o, deepseek-chat")
        layout.addRow("模型:", self.model_edit)

        btn_layout = QHBoxLayout()
        test_btn = QPushButton("测试连接")
        test_btn.setStyleSheet("QPushButton { background-color: #30363D; } QPushButton:hover { background-color: #484F58; }")
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("QPushButton { background-color: #30363D; } QPushButton:hover { background-color: #484F58; }")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "名称不能为空")
            return
        if not self.url_edit.text().strip():
            QMessageBox.warning(self, "提示", "Base URL 不能为空")
            return
        self.accept()

    def _test_connection(self):
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=self.model_edit.text() or "test",
                base_url=self.url_edit.text(),
                api_key=self.key_edit.text() or "not-needed",
                timeout=8,
            )
            QMessageBox.information(self, "测试结果", "连接成功！")
        except Exception as e:
            QMessageBox.warning(self, "测试结果", f"连接失败: {str(e)[:200]}")

    def get_data(self):
        return (
            self.name_edit.text().strip(),
            {
                "base_url": self.url_edit.text().strip(),
                "api_key": self.key_edit.text().strip() or "not-needed",
                "model": self.model_edit.text().strip(),
            },
        )


class SettingsDialog(QDialog):
    providers_changed = Signal()

    def __init__(self, llm_registry, parent=None, config_path=None):
        super().__init__(parent)
        self.llm_registry = llm_registry
        self.config_path = config_path or "config.yaml"
        self.setWindowTitle("模型设置")
        self.resize(720, 520)
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

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
        provider_tab = QWidget()
        pl = QVBoxLayout(provider_tab)
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

        self.tabs.addTab(provider_tab, "LLM 提供商")

        # ── Tab 2: 用户规则 ──────────────────────
        rules_tab = QWidget()
        rl = QVBoxLayout(rules_tab)
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

        self.tabs.addTab(rules_tab, "用户规则")

        # Load rules from config
        self._load_rules()

        layout.addWidget(self.tabs)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("QPushButton { background-color: #30363D; } QPushButton:hover { background-color: #484F58; }")
        self.close_btn.clicked.connect(self.accept)
        close_layout.addWidget(self.close_btn)
        layout.addLayout(close_layout)

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
        if dlg.exec() == QDialog.Accepted:
            name, cfg = dlg.get_data()
            self.llm_registry.add_provider(name, cfg)
            self._load_table()
            self.providers_changed.emit()

    def _edit_provider(self, name):
        cfg = self.llm_registry.get_provider_config(name)
        dlg = ProviderFormDialog(self, name, cfg)
        if dlg.exec() == QDialog.Accepted:
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
        """从 config.yaml 加载用户规则"""
        try:
            import yaml
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            rules = cfg.get("user_rules", [])
            self.rules_editor.setPlainText("\n".join(rules))
        except Exception:
            pass

    def _save_rules(self):
        """保存用户规则到 config.yaml"""
        try:
            text = self.rules_editor.toPlainText().strip()
            rules = [line.strip() for line in text.split("\n") if line.strip()]
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            cfg["user_rules"] = rules
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            QMessageBox.information(self, "已保存", f"已保存 {len(rules)} 条规则。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
