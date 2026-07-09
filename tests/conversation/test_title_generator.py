"""Tests for conversation title generation."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from v6.runtime.types import ChatMessage

from agent_workbench.conversation.title_generator import RuleTitleGenerator


class TestRuleTitleGenerator:
    def test_empty_messages_returns_default(self):
        gen = RuleTitleGenerator()
        assert gen.generate([]) == RuleTitleGenerator.DEFAULT_TITLE

    def test_only_assistant_messages_returns_default(self):
        gen = RuleTitleGenerator()
        messages = [ChatMessage(role="assistant", content="Hello")]
        assert gen.generate(messages) == RuleTitleGenerator.DEFAULT_TITLE

    def test_short_user_message_preserved(self):
        gen = RuleTitleGenerator()
        messages = [ChatMessage(role="user", content="帮我分析代码")]
        assert gen.generate(messages) == "帮我分析代码"

    def test_long_user_message_truncated_by_chars(self):
        gen = RuleTitleGenerator()
        long_text = "帮我分析这个 Python 文件的架构和潜在问题并给出优化建议"
        messages = [ChatMessage(role="user", content=long_text)]
        title = gen.generate(messages)
        assert len(title) <= RuleTitleGenerator.MAX_CHARS + 1  # +1 for ellipsis
        assert title.endswith("…")

    def test_long_user_message_truncated_by_words(self):
        gen = RuleTitleGenerator()
        long_text = "one two three four five six seven eight nine ten"
        messages = [ChatMessage(role="user", content=long_text)]
        title = gen.generate(messages)
        assert len(title.split()) <= RuleTitleGenerator.MAX_WORDS

    def test_newlines_replaced(self):
        gen = RuleTitleGenerator()
        messages = [ChatMessage(role="user", content="帮我分析\n这个代码")]
        title = gen.generate(messages)
        assert "\n" not in title
        assert title == "帮我分析 这个代码"

    def test_first_user_message_wins(self):
        gen = RuleTitleGenerator()
        messages = [
            ChatMessage(role="user", content="first"),
            ChatMessage(role="user", content="second"),
        ]
        assert gen.generate(messages) == "first"
