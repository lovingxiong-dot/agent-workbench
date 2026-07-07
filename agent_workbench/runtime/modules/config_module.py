"""agent_workbench/runtime/modules/config_module.py — Config 模块。

职责：
- 作为 ConfigStore 的 facade 暴露给 UI。
- 本身不持有状态，所有配置通过 ConfigStore 读写。
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule


class ConfigModule(BaseRuntimeModule):
    """配置模块：提供当前配置的查看与编辑入口。"""

    @property
    def namespace(self) -> str:
        return "config"

    def apply_config(self, store: ConfigStore) -> None:
        """Config 模块无需额外 apply，配置本身即状态。"""
        pass

    def to_form(self) -> Dict[str, Any]:
        """返回可编辑配置树。"""
        return {
            "title": "Config",
            "description": "查看和编辑当前 YAML 配置。",
            "fields": [
                {"name": "raw", "type": "json", "label": "Current Configuration"},
            ],
        }
