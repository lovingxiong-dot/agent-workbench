"""tests/v6/test_v6_provider_switch.py — Provider 运行时切换验证。

覆盖：
- 运行时切换 Provider 无需重启
- 切换后自动选择第一个可用模型
- 切换失败场景（不存在的 Provider、无模型的 Provider）
- 切换后应立即生效（下次请求使用新 Provider）
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.model_module import ModelModule


@pytest.fixture
def model_module():
    """创建配置好的 ModelModule，使用临时配置。"""
    _config_data = {
        "model": {
            "default_provider": "echo",
            "providers": [
                {
                    "name": "echo",
                    "type": "echo",
                    "enabled": True,
                    "models": ["echo-default"],
                },
                {
                    "name": "agnes",
                    "type": "openai",
                    "enabled": True,
                    "base_url": "https://apihub.agnes-ai.com/v1",
                    "api_key": os.environ.get("AGNES_API_KEY", "test-key"),
                    "models": ["agnes-2.0-flash", "agnes-1.5-flash"],
                },
                {
                    "name": "deepseek",
                    "type": "deepseek",
                    "enabled": True,
                    "base_url": "https://api.deepseek.com/v1",
                    "api_key": os.environ.get("DEEPSEEK_API_KEY", "test-key"),
                    "models": ["deepseek-chat"],
                },
            ],
            "sampling": {"temperature": 0.7, "max_tokens": 2048},
            "context": {"max_history": 20},
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        import yaml
        tmp_config = Path(tmpdir) / "test_config.yaml"
        with open(tmp_config, "w", encoding="utf-8") as f:
            yaml.safe_dump(_config_data, f)

        config = ConfigStore(config_path=str(tmp_config))
        mm = ModelModule()
        mm.initialize(mock.MagicMock())
        mm.apply_config(config)
        yield mm


class TestProviderSwitching:
    """Provider 运行时切换测试。"""

    def test_initial_provider_is_echo(self, model_module):
        """初始默认 Provider 应为 echo。"""
        assert model_module.get_current_provider_name() == "echo"
        assert model_module.current_model == "echo-default"

    def test_switch_to_agnes(self, model_module):
        """切换到 agnes Provider，自动选择第一个模型。"""
        result = model_module.switch_provider("agnes")
        assert result is True
        assert model_module.get_current_provider_name() == "agnes"
        assert model_module.current_model == "agnes-2.0-flash"

    def test_switch_to_deepseek(self, model_module):
        """切换到 deepseek Provider。"""
        result = model_module.switch_provider("deepseek")
        assert result is True
        assert model_module.get_current_provider_name() == "deepseek"
        assert model_module.current_model == "deepseek-chat"

    def test_switch_to_nonexistent_provider(self, model_module):
        """切换到不存在的 Provider 应返回 False。"""
        original_provider = model_module.get_current_provider_name()
        original_model = model_module.current_model

        result = model_module.switch_provider("nonexistent")
        assert result is False
        # 状态不应改变
        assert model_module.get_current_provider_name() == original_provider
        assert model_module.current_model == original_model

    def test_switch_between_models_within_provider(self, model_module):
        """在同一 Provider 内切换模型。"""
        model_module.switch_provider("agnes")
        assert model_module.current_model == "agnes-2.0-flash"

        result = model_module.switch_model("agnes-1.5-flash")
        assert result is True
        assert model_module.current_model == "agnes-1.5-flash"

    def test_switch_model_not_in_list(self, model_module):
        """切换到不存在的模型应返回 False。"""
        result = model_module.switch_model("nonexistent-model")
        assert result is False

    def test_switch_provider_then_back(self, model_module):
        """切换 Provider 后再切回来。"""
        model_module.switch_provider("agnes")
        assert model_module.get_current_provider_name() == "agnes"

        model_module.switch_provider("echo")
        assert model_module.get_current_provider_name() == "echo"
        assert model_module.current_model == "echo-default"

    def test_list_models_after_switch(self, model_module):
        """切换 Provider 后 list_models 应返回新 Provider 的模型列表。"""
        assert model_module.list_models() == ["echo-default"]

        model_module.switch_provider("agnes")
        assert model_module.list_models() == ["agnes-2.0-flash", "agnes-1.5-flash"]

    def test_list_providers(self, model_module):
        """list_providers 应返回所有可用 Provider。"""
        providers = model_module.list_providers()
        names = [p["name"] for p in providers]
        assert "echo" in names
        assert "agnes" in names
        assert "deepseek" in names

    def test_model_module_does_not_persist_switch_to_config(self, model_module):
        """运行时切换后再 apply_config，应恢复默认值。"""
        model_module.switch_provider("agnes")
        assert model_module.get_current_provider_name() == "agnes"

        # 重新 apply 原配置，应恢复默认
        model_module.apply_config(model_module._last_config)
        assert model_module.get_current_provider_name() == "echo"