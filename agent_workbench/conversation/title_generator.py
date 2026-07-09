"""agent_workbench/conversation/title_generator.py — 会话标题生成策略。

所有策略只接收消息列表，返回标题字符串。
UI / Runtime / Provider 对标题生成逻辑无感知。
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from v6.runtime.types import ChatMessage


@runtime_checkable
class TitleGenerator(Protocol):
    """标题生成器协议。"""

    def generate(self, messages: list[ChatMessage]) -> str:
        """根据消息列表生成标题。"""
        ...


class AbstractTitleGenerator(ABC):
    """同步标题生成器的抽象基类。"""

    @abstractmethod
    def generate(self, messages: list[ChatMessage]) -> str:
        """根据消息列表生成标题。"""
        ...


class RuleTitleGenerator(AbstractTitleGenerator):
    """基于规则的标题生成器。

    - 取第一条用户消息。
    - 清理首尾空白与换行。
    - 超过 8 个词或 30 个字符时截断并加 "…"。
    - 无用户消息时返回默认标题。
    """

    DEFAULT_TITLE: str = "New Conversation"
    MAX_CHARS: int = 30
    MAX_WORDS: int = 8

    def generate(self, messages: list[ChatMessage]) -> str:
        first_user_text = ""
        for msg in messages:
            if getattr(msg, "role", None) == "user":
                first_user_text = (getattr(msg, "content", None) or "").strip()
                break

        if not first_user_text:
            return self.DEFAULT_TITLE

        # 把换行替换为空格，压缩连续空白。
        text = re.sub(r"\s+", " ", first_user_text.replace("\n", " ")).strip()

        words = text.split()
        if len(words) <= self.MAX_WORDS and len(text) <= self.MAX_CHARS:
            return text

        if len(words) > self.MAX_WORDS:
            text = " ".join(words[: self.MAX_WORDS])
        if len(text) > self.MAX_CHARS:
            text = text[: self.MAX_CHARS].rstrip() + "…"
        return text
