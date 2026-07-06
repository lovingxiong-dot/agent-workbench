"""v6/services/config_service.py — 配置业务服务。

对 ConfigManager 的薄封装，为 UIController 提供类型明确的业务接口。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from v6.config_manager import ConfigManager


class ConfigService:
    """配置业务服务。"""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        self._cm = config_manager or ConfigManager(data_dir=data_dir)

    @property
    def manager(self) -> ConfigManager:
        return self._cm

    def theme(self) -> str:
        return self._cm.get("theme.name", "dark")

    def last_mode(self) -> str:
        return self._cm.get("app.last_mode", "Agent")

    def last_model(self) -> str:
        return self._cm.get("app.last_model", "gpt-4o")

    def window_geometry(self) -> Any:
        return self._cm.get("window.geometry")

    def set_theme(self, name: str) -> None:
        self._cm.set("theme.name", name)

    def set_last_mode(self, mode: str) -> None:
        self._cm.set("app.last_mode", mode)

    def set_last_model(self, model: str) -> None:
        self._cm.set("app.last_model", model)

    def set_window_geometry(self, geometry: Any) -> None:
        self._cm.set("window.geometry", geometry)
