"""agent_workbench/config/loader.py — Agent Workbench V6 配置加载器。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 支持从 YAML 文件加载配置，并提供默认 fallback。
- 未来可扩展为从环境变量、用户目录、远程配置加载。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigLoader:
    """Demo Agent 配置加载器。"""

    def __init__(self, config_path: str | os.PathLike | None = None) -> None:
        self._config_path = config_path
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """加载配置文件；不存在时返回空字典（使用代码默认值）。"""
        path = self._resolve_path()
        if path is None or not os.path.exists(path):
            self._config = {}
            return self._config

        with open(path, "r", encoding="utf-8") as fh:
            self._config = yaml.safe_load(fh) or {}
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """点分键访问配置，例如 'agent.name'。"""
        keys = key.split(".")
        value: Any = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def _resolve_path(self) -> Path | None:
        if self._config_path is not None:
            return Path(self._config_path)
        # 默认查找当前文件同级目录下的 default.yaml
        here = Path(__file__).parent
        default = here / "default.yaml"
        if default.exists():
            return default
        return None


def default_config() -> Dict[str, Any]:
    """返回默认配置；当配置文件不存在时使用。"""
    return {
        "agent": {
            "name": "Agent Workbench V6",
            "version": "v6.9.0-alpha-workbench",
        },
        "ui": {
            "title": "Agent Workbench V6",
            "width": 1200,
            "height": 800,
        },
        "runtime": {
            "use_orchestrator": True,
            "decision_policy": "rule_based",
        },
        "engines": {
            "llm": {"type": "echo"},
            "tool": {"type": "echo"},
        },
        "logging": {"level": "INFO"},
    }
