"""Tests for the configuration-driven Provider / AI Models loop.

验证 No-Code Registration Principle：
- ConfigurationManager 注册配置分类
- AddProviderDialog 收集 provider 信息并返回 dict
- WorkbenchUIController._on_add_requested 把结果追加到 ConfigStore
- ConfigStore.changed 信号驱动 Navigator / StatusBar 刷新
"""
from __future__ import annotations

import os
import sys
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QDialog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.controller import WorkbenchController
from agent_workbench.ui.configuration import ConfigCategory, ConfigurationManager
from agent_workbench.ui.dialogs import (
    AddMcpDialog,
    AddMemoryDialog,
    AddPromptDialog,
    AddProviderDialog,
    AddSkillDialog,
    AddWorkflowDialog,
)
from agent_workbench.ui.workbench import WorkbenchHost
from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestConfigurationManager:
    def test_register_and_lookup(self):
        manager = ConfigurationManager()
        cat = ConfigCategory(
            category_id="model",
            title="AI Models",
            icon="🤖",
            config_path="model.providers",
            dialog_factory=None,
        )
        manager.register(cat)

        assert manager.get("model") is cat
        assert manager.get("missing") is None

    def test_list_categories(self):
        manager = ConfigurationManager()
        manager.register(
            ConfigCategory("model", "AI Models", "🤖", "model.providers", None)
        )
        manager.register(
            ConfigCategory("mcp", "MCP", "🔌", "mcp.servers", None)
        )

        categories = manager.list_categories()
        assert len(categories) == 2
        assert [c.category_id for c in categories] == ["model", "mcp"]


class TestAddProviderDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddProviderDialog()
        dialog._name_edit.setText("openai-gpt4")
        dialog._type_combo.setCurrentText("openai")
        dialog._model_edit.setText("gpt-4o")
        dialog._api_key_edit.setText("sk-secret")
        dialog._base_url_edit.setText("https://api.openai.com/v1")
        dialog._enabled_check.setChecked(False)

        dialog.accept()

        assert dialog.result() == {
            "name": "openai-gpt4",
            "type": "openai",
            "model": "gpt-4o",
            "api_key": "sk-secret",
            "base_url": "https://api.openai.com/v1",
            "enabled": False,
        }

    def test_default_type_is_echo(self, qt_app):
        dialog = AddProviderDialog()
        dialog._name_edit.setText("echo-local")
        dialog.accept()

        result = dialog.result()
        assert result["type"] == "echo"
        assert result["enabled"] is True

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddProviderDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestWorkbenchUIControllerProviderLoop:
    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        workbench = WorkbenchController(config_path=str(config_path))
        return WorkbenchUIController(
            workbench=workbench,
            workbench_host=None,
            data_dir=str(tmp_path),
        )

    def test_on_add_requested_appends_provider(self, controller):
        class FakeDialog:
            def exec(self) -> int:
                return QDialog.DialogCode.Accepted

            def result(self) -> dict[str, Any]:
                return {
                    "name": "fake-echo",
                    "type": "echo",
                    "model": "default",
                    "api_key": "",
                    "base_url": "",
                    "enabled": True,
                }

        controller._config_manager.register(
            ConfigCategory(
                category_id="model",
                title="AI Models",
                icon="🤖",
                config_path="model.providers",
                dialog_factory=lambda: FakeDialog(),
            )
        )

        controller._on_add_requested("model")

        providers = controller._workbench.get_config_value("model.providers", [])
        assert len(providers) == 1
        assert providers[0]["name"] == "fake-echo"
        assert providers[0]["type"] == "echo"

    def test_provider_dialog_factory_exposes_registry_types(self, controller):
        category = controller._config_manager.get("model")
        dialog = category.dialog_factory()
        combo = dialog._type_combo
        types = {combo.itemText(i) for i in range(combo.count())}
        assert types == {
            "claude",
            "deepseek",
            "echo",
            "gemini",
            "kimi",
            "openai",
            "qwen",
        }

    def test_model_providers_update_triggers_navigator_refresh(
        self, qt_app, tmp_path
    ):
        config_path = tmp_path / "test_config.yaml"
        workbench = WorkbenchController(config_path=str(config_path))
        host = WorkbenchHost()
        controller = WorkbenchUIController(
            workbench=workbench,
            workbench_host=host,
            data_dir=str(tmp_path),
        )
        # 手动连接通用变更信号，模拟 startup 中的行为
        workbench.runtime.config.changed.connect(controller._on_config_changed)

        refresh_count = [0]
        original_refresh = controller._refresh_navigator

        def counted_refresh() -> None:
            refresh_count[0] += 1
            return original_refresh()

        controller._refresh_navigator = counted_refresh

        controller._workbench.set_config_value(
            "model.providers",
            [{"name": "refresh-provider", "type": "echo"}],
        )

        assert refresh_count[0] == 1
        # Navigator 实际也被刷新：分类数量为 ConfigurationManager 中注册的数量
        navigator = host.workbench.navigator.content
        assert navigator is not None
        assert navigator._settings_list.count() == 7


class TestAddMcpDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddMcpDialog()
        dialog._name_edit.setText("filesystem")
        dialog._command_edit.setText("npx")
        dialog._args_edit.setText("-y @modelcontextprotocol/server-filesystem /tmp")
        dialog._env_edit.setText("HOME=/tmp, DEBUG=1")
        dialog._enabled_check.setChecked(True)
        dialog.accept()

        result = dialog.result()
        assert result == {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "env": {"HOME": "/tmp", "DEBUG": "1"},
            "enabled": True,
        }

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddMcpDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestAddSkillDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddSkillDialog()
        dialog._name_edit.setText("hello")
        dialog._type_combo.setCurrentText("python")
        dialog._source_edit.setText("skills/hello.py")
        dialog._description_edit.setText("Say hello")
        dialog._enabled_check.setChecked(False)
        dialog.accept()

        assert dialog.result() == {
            "name": "hello",
            "type": "python",
            "source": "skills/hello.py",
            "description": "Say hello",
            "enabled": False,
        }

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddSkillDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestAddWorkflowDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddWorkflowDialog()
        dialog._name_edit.setText("daily-report")
        dialog._description_edit.setText("Generate daily report")
        dialog._steps_edit.setPlainText("Fetch data\nAnalyze\nWrite report")
        dialog._enabled_check.setChecked(True)
        dialog.accept()

        assert dialog.result() == {
            "name": "daily-report",
            "description": "Generate daily report",
            "steps": ["Fetch data", "Analyze", "Write report"],
            "enabled": True,
        }

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddWorkflowDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestAddPromptDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddPromptDialog()
        dialog._name_edit.setText("coder")
        dialog._description_edit.setText("Code assistant")
        dialog._template_edit.setPlainText("You are a coder.")
        dialog._enabled_check.setChecked(True)
        dialog.accept()

        assert dialog.result() == {
            "name": "coder",
            "description": "Code assistant",
            "template": "You are a coder.",
            "enabled": True,
        }

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddPromptDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestAddMemoryDialog:
    def test_result_dict_when_accepted(self, qt_app):
        dialog = AddMemoryDialog()
        dialog._name_edit.setText("default")
        dialog._provider_combo.setCurrentText("sqlite")
        dialog._path_edit.setText("storage/memory/default.db")
        dialog._enabled_check.setChecked(True)
        dialog.accept()

        assert dialog.result() == {
            "name": "default",
            "provider": "sqlite",
            "path": "storage/memory/default.db",
            "enabled": True,
        }

    def test_result_empty_when_rejected(self, qt_app):
        dialog = AddMemoryDialog()
        dialog.reject()
        assert dialog.result() == {}


class TestWorkbenchUIControllerConfigLoops:
    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        workbench = WorkbenchController(config_path=str(config_path))
        return WorkbenchUIController(
            workbench=workbench,
            workbench_host=None,
            data_dir=str(tmp_path),
        )

    def _fake_category(self, controller: WorkbenchUIController, category_id: str, config_path: str, item: dict[str, Any]) -> None:
        class FakeDialog:
            def exec(self) -> int:
                return QDialog.DialogCode.Accepted

            def result(self) -> dict[str, Any]:
                return item

        controller._config_manager.register(
            ConfigCategory(
                category_id=category_id,
                title=category_id.title(),
                icon="",
                config_path=config_path,
                dialog_factory=lambda: FakeDialog(),
            )
        )

    def test_add_mcp_appends_to_servers(self, controller):
        self._fake_category(
            controller,
            "mcp",
            "mcp.servers",
            {"name": "fs", "command": "npx", "args": [], "env": {}, "enabled": True},
        )
        controller._on_add_requested("mcp")

        servers = controller._workbench.get_config_value("mcp.servers", [])
        assert len(servers) == 1
        assert servers[0]["name"] == "fs"

    def test_add_skill_appends_to_registry(self, controller):
        self._fake_category(
            controller,
            "skill",
            "skill.registry",
            {"name": "hello", "type": "echo", "source": "", "description": "", "enabled": True},
        )
        controller._on_add_requested("skill")

        skills = controller._workbench.get_config_value("skill.registry", [])
        assert len(skills) == 1
        assert skills[0]["name"] == "hello"

    def test_add_workflow_appends_to_templates(self, controller):
        self._fake_category(
            controller,
            "workflow",
            "workflow.templates",
            {"name": "report", "description": "", "steps": [], "enabled": True},
        )
        controller._on_add_requested("workflow")

        templates = controller._workbench.get_config_value("workflow.templates", [])
        assert len(templates) == 1
        assert templates[0]["name"] == "report"

    def test_add_prompt_appends_to_templates(self, controller):
        self._fake_category(
            controller,
            "prompt",
            "prompt.templates",
            {"name": "coder", "description": "", "template": "", "enabled": True},
        )
        controller._on_add_requested("prompt")

        templates = controller._workbench.get_config_value("prompt.templates", [])
        assert len(templates) == 1
        assert templates[0]["name"] == "coder"

    def test_add_memory_appends_to_configs(self, controller, tmp_path):
        db_path = str(tmp_path / "mem.db")
        self._fake_category(
            controller,
            "memory",
            "memory.configs",
            {"name": "default", "provider": "sqlite", "path": db_path, "enabled": True},
        )
        controller._on_add_requested("memory")

        configs = controller._workbench.get_config_value("memory.configs", [])
        assert len(configs) == 1
        assert configs[0]["name"] == "default"
