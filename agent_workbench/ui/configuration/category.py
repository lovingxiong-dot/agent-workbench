"""agent_workbench/ui/configuration/category.py — 配置分类元数据。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QDialog


@dataclass
class ConfigCategory:
    """左侧 Navigator Settings 区的一个配置分类。"""

    category_id: str
    title: str
    icon: str
    config_path: str
    dialog_factory: Callable[[], QDialog] | None
