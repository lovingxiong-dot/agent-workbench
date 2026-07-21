"""v5 配置服务包装层。"""
import os
import sys
from typing import Any, Optional

from services.config_service import ConfigService as _RootConfigService


class ConfigService:
    """包装根目录 ConfigService，提供 V5 所需配置接口。"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self._svc = _RootConfigService(config_path=config_path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._svc.get(key, default)

    def set(self, key: str, value: Any):
        self._svc.set(key, value)

    def save(self):
        self._svc.save()

    @property
    def raw_config(self) -> dict:
        """返回底层完整配置字典，供 engines 初始化使用。"""
        return self._svc.config or {}

    def get_app_root(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
