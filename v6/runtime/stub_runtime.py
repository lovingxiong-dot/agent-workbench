"""v6/runtime/stub_runtime.py — 最小 Echo Runtime 占位。

在真正的 AgentRuntime 实现前，仅用于支撑 UI 层独立演示：
收到用户消息后通过 callback 返回固定回声。
下一阶段将被 runtime.py + engines/ 替换。
"""
from __future__ import annotations

from typing import Callable


class EchoRuntime:
    """最小 Runtime 占位：收到消息后通过 callback 返回回声事件。"""

    def __init__(self) -> None:
        self._counter = 0

    def send_chat(self, text: str, on_event: Callable[[str, dict], None]) -> None:
        """模拟一次聊天任务：user_echo → ai_start → ai_chunk → ai_end。"""
        self._counter += 1
        on_event("user_echo", {"text": text})
        on_event("ai_start", {"phase": ""})
        on_event("ai_chunk", {"text": f"收到：{text.replace(chr(10), ' ')}"})
        on_event("ai_end", {})
