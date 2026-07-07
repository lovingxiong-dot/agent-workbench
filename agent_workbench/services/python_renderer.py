"""agent_workbench/services/python_renderer.py — Python 风格 Prompt 渲染器。

第一版使用 str.format() 语法，支持 {variable} 占位符。
未来可替换为 JinjaRenderer，但接口保持一致。
"""
from __future__ import annotations

from typing import Any, Dict

from agent_workbench.services.prompt_renderer import PromptRenderer


class PythonRenderer(PromptRenderer):
    """使用 Python str.format() 渲染 Prompt 模板。"""

    @property
    def name(self) -> str:
        return "python"

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """渲染模板；缺失变量保留原占位符，不抛异常。"""
        if not template:
            return ""
        try:
            return template.format_map(_SafeMapping(variables))
        except (ValueError, KeyError):
            return template

    def validate(self, template: str) -> bool:
        """简单校验：尝试格式化空字典，不抛异常即有效。"""
        try:
            template.format_map(_SafeMapping({}))
            return True
        except (ValueError, KeyError):
            return False


class _SafeMapping(dict):
    """缺失 key 时返回原 {key} 占位符，避免渲染失败。"""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
