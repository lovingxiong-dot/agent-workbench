"""agent_workbench/services/echo_provider.py — Echo Model Provider。

第一版占位 Provider，用于验证 ModelModule / Runtime 链路。
不引入任何真实 LLM 依赖。
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Any, Dict, List

from agent_workbench.services.model_provider import ModelProvider


class EchoProvider(ModelProvider):
    """回声 Provider：对已知关键词做固定回复，其余返回回声。"""

    @property
    def name(self) -> str:
        return "echo"

    def chat(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> str:
        """生成回声回复。"""
        text = ""
        if messages:
            text = messages[-1].get("content", "")

        lowered = text.lower().strip()
        if not lowered:
            return "你好，我是 V6 Agent Workbench，请输入内容。"
        if "time" in lowered or "时间" in lowered:
            return f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if "hello" in lowered or "你好" in lowered:
            return "你好！我是 V6 Agent Workbench，Framework Core 运行正常。"
        return f"收到：{text.replace(chr(10), ' ')}"

    def chat_stream(
        self, messages: List[Dict[str, str]], params: Dict[str, Any]
    ) -> Iterator[str]:
        """按固定长度块流式返回回声回复，方便验证 UI 流式渲染。"""
        response = self.chat(messages, params)
        chunk_size = 4
        for i in range(0, len(response), chunk_size):
            yield response[i : i + chunk_size]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Echo provider 无必填配置。"""
        return isinstance(config, dict)
