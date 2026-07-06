"""v6/config_manager.py — 配置持久化管理器。

职责：
- 统一管理数据目录 storage/
- 读写 storage/config.yaml
- 支持点分路径 get/set
- 配置变更时持久化并发射 changed 信号

数据层除 changed 信号外不依赖 Qt。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from PySide6.QtCore import QObject, Signal

from v6._paths import data_dir as _default_data_dir


class ConfigManager(QObject):
    """基于 YAML 的应用配置管理器。"""

    changed = Signal(str, object)  # path, new_value

    def __init__(self, data_dir: str | os.PathLike | None = None) -> None:
        super().__init__()
        self._dir = Path(data_dir) if data_dir else _default_data_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "config.yaml"
        self._config: dict[str, Any] = {}
        self._load_defaults()
        self._load()

    def _load_defaults(self) -> None:
        """初始化默认配置；后续加载会合并覆盖。"""
        self._config = {
            "app": {
                "version": "v6.3.0-alpha",
                "last_mode": "Agent",
                "last_model": "gpt-4o",
            },
            "theme": {"name": "dark"},
            "window": {"geometry": None},
        }

    def get(self, path: str, default: Any = None) -> Any:
        """通过点分路径读取配置，不存在则返回 default。"""
        parts = path.split(".")
        node = self._config
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, path: str, value: Any) -> None:
        """通过点分路径设置配置，自动持久化并发射 changed 信号。"""
        parts = path.split(".")
        node = self._config
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        self.save()
        self.changed.emit(path, value)

    def save(self) -> None:
        """立即持久化到 config.yaml。"""
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, allow_unicode=True, sort_keys=False)

    def _load(self) -> None:
        """从 config.yaml 加载，与默认配置深度合并。"""
        if not self._path.exists():
            self.save()
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
        except Exception:
            return
        if isinstance(loaded, dict):
            self._merge(loaded, self._config)

    def _merge(self, src: dict, dst: dict) -> None:
        """将 src 深度合并到 dst。"""
        for key, value in src.items():
            if isinstance(value, dict) and key in dst and isinstance(dst[key], dict):
                self._merge(value, dst[key])
            else:
                dst[key] = value
