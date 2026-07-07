"""agent_workbench/runtime/modules/config_module.py — Config 模块。

职责：
- 作为 ConfigStore 的 facade 暴露给 UI。
- 本身不持有状态，所有配置通过 ConfigStore 读写。
"""
from __future__ import annotations

import yaml

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule


class ConfigModule(BaseRuntimeModule):
    """配置模块：提供当前配置的查看与编辑入口。"""

    def __init__(self) -> None:
        self._store: ConfigStore | None = None

    @property
    def namespace(self) -> str:
        return "config"

    def apply_config(self, store: ConfigStore) -> None:
        """Config 模块无需额外 apply，但保存 store 引用供 metadata 使用。"""
        self._store = store

    def metadata(self) -> ModuleMetadata:
        """返回 Config Capability Metadata。"""
        raw = ""
        if self._store is not None:
            raw = yaml.safe_dump(self._store.snapshot(), sort_keys=False, allow_unicode=True)
        return ModuleMetadata(
            id="config",
            type="config",
            name="Config",
            description="当前 YAML 配置的唯一真相源。",
            icon="file-code",
            properties=[
                PropertyMetadata(
                    name="raw",
                    label="Current Configuration",
                    type="textarea",
                    value=raw,
                    editable=True,
                ),
            ],
            statistics=[],
            actions=[
                ActionMetadata(name="save", label="Save", icon="save"),
                ActionMetadata(name="reload", label="Reload", icon="refresh"),
            ],
        )
