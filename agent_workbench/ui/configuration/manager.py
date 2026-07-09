"""agent_workbench/ui/configuration/manager.py — 配置分类注册管理器。"""
from __future__ import annotations

from agent_workbench.ui.configuration.category import ConfigCategory


class ConfigurationManager:
    """统一管理所有 Settings 配置分类。"""

    def __init__(self) -> None:
        self._categories: dict[str, ConfigCategory] = {}

    def register(self, category: ConfigCategory) -> None:
        """注册一个配置分类。"""
        self._categories[category.category_id] = category

    def get(self, category_id: str) -> ConfigCategory | None:
        """按 id 查找配置分类。"""
        return self._categories.get(category_id)

    def list_categories(self) -> list[ConfigCategory]:
        """返回所有已注册配置分类。"""
        return list(self._categories.values())
