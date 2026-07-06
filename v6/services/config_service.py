"""v6/services/config_service.py — 配置业务服务。

对 ConfigManager 的薄封装，为 UIController / Runtime 提供符合 Runtime Interface Principle 的接口。

设计来源：docs/v6/SPEC.md 第 8.12 节。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from v6.config_manager import ConfigManager
from v6.runtime.context import RuntimeContext


class ConfigService:
    """配置业务服务。

    公共方法统一接收 RuntimeContext，方法名保留语义。
    """

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        self._cm = config_manager or ConfigManager(data_dir=data_dir)

    @property
    def manager(self) -> ConfigManager:
        return self._cm

    def apply(self, ctx: RuntimeContext) -> None:
        """将配置管理器中的配置应用到 RuntimeContext.metadata。"""
        ctx.metadata.setdefault("config", {})
        ctx.metadata["config"]["theme"] = self._cm.get("theme.name", "dark")
        ctx.metadata["config"]["last_mode"] = self._cm.get("app.last_mode", "Agent")
        ctx.metadata["config"]["last_model"] = self._cm.get("app.last_model", "gpt-4o")
        ctx.metadata["config"]["window_geometry"] = self._cm.get("window.geometry")

    def persist(self, ctx: RuntimeContext) -> None:
        """将 RuntimeContext.metadata 中的配置持久化。"""
        cfg = ctx.metadata.get("config", {})
        if "theme" in cfg:
            self._cm.set("theme.name", cfg["theme"])
        if "last_mode" in cfg:
            self._cm.set("app.last_mode", cfg["last_mode"])
        if "last_model" in cfg:
            self._cm.set("app.last_model", cfg["last_model"])
        if "window_geometry" in cfg:
            self._cm.set("window.geometry", cfg["window_geometry"])
