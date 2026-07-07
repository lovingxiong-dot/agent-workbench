"""agent_workbench/services/prompt_renderer.py — Prompt 渲染器统一接口。

未来可扩展：
- PythonRenderer（第一版）
- JinjaRenderer
- MustacheRenderer

Runtime 通过此接口调用，不依赖具体实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PromptRenderer(ABC):
    """Prompt 渲染器抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """渲染器标识名。"""
        ...

    @abstractmethod
    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """渲染模板并返回最终 Prompt 文本。"""
        ...

    @abstractmethod
    def validate(self, template: str) -> bool:
        """校验模板语法是否有效。"""
        ...
