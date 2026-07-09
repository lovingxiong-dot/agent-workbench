"""agent_workbench/ui/configuration/ — 配置分类注册表。

No-Code Registration Principle：
Settings 分类与新增对话框通过 ConfigurationManager 注册，
Navigator 与 WorkbenchUIController 只依赖分类元数据，无需硬编码每个领域。
"""
from __future__ import annotations

from agent_workbench.ui.configuration.category import ConfigCategory
from agent_workbench.ui.configuration.manager import ConfigurationManager

__all__ = ["ConfigCategory", "ConfigurationManager"]
