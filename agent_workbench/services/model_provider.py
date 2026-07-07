"""agent_workbench/services/model_provider.py — Model Provider 统一接口。

Provider 列表：
- EchoProvider（第一版占位）
- 未来：OpenAIProvider、GeminiProvider、ClaudeProvider、LocalProvider

ModelModule 通过此接口管理 provider，不依赖具体实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Dict, List


class ModelProvider(ABC):
    """模型 Provider 抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 标识名。"""
        ...

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> str:
        """根据消息列表和采样参数生成回复。"""
        ...

    def chat_stream(
        self, messages: List[Dict[str, str]], params: Dict[str, Any]
    ) -> Iterator[str]:
        """流式生成回复。默认实现一次性返回完整回复；子类可覆盖实现真正流式。"""
        yield self.chat(messages, params)

    def configure(self, config: Dict[str, Any]) -> None:
        """传入 provider 专属配置；默认无操作，子类可覆盖。"""

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """校验 provider 配置是否有效。"""
        ...
