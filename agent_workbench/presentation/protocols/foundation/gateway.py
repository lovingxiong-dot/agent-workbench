"""presentation/protocols/foundation/gateway.py — Gateway Contract。

Phase 1: Foundation Contract Freeze。

约束：
  ✓ 仅 dataclass + Protocol
  ✗ 零 Runtime Implementation import
  ✗ 零 UI import
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Protocol


class GatewayMode(str, Enum):
    """Gateway 运行模式。"""
    SINGLE_RUNTIME = "single_runtime"
    MULTI_RUNTIME = "multi_runtime"
    FEDERATION = "federation"


class ProviderProtocol(str, Enum):
    """LLM Provider 协议。"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    QWEN = "qwen"
    KIMI = "kimi"
    ECHO = "echo"
    CUSTOM = "custom"


@dataclass
class ProviderEndpoint:
    """Provider 接入点配置。"""
    provider_id: str
    protocol: ProviderProtocol
    base_url: str = ""
    api_key: str = ""
    models: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.models is None:
            self.models = []


@dataclass
class GatewayRequest:
    """Gateway 调用请求。"""
    request_id: str
    capability_id: str
    input: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayResponse:
    """Gateway 调用响应。"""
    request_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: int = 0


class Gateway(Protocol):
    """Gateway Contract — Provider / Model / Capability 路由。

    关键操作：
      - register_provider: 注册 Provider 接入点。
      - invoke: 调用某个 Capability（Gateway 自动路由到正确的 Provider/Model）。
      - list_providers: 列出已注册的 Provider。
      - health: 健康检查。

    Workbench v6：使用 Gateway 调用 LLM Provider。
    Agent Manager OS：使用 Gateway 跨 Runtime 路由 Capability。
    """

    @property
    def mode(self) -> GatewayMode:
        """Gateway 运行模式。"""
        ...

    def register_provider(self, provider: ProviderEndpoint) -> None:
        """注册一个 Provider 接入点。"""
        ...

    def unregister_provider(self, provider_id: str) -> None:
        """注销一个 Provider。"""
        ...

    def list_providers(self) -> List[ProviderEndpoint]:
        """列出所有已注册的 Provider。"""
        ...

    def invoke(self, request: GatewayRequest) -> GatewayResponse:
        """调用某个 Capability。"""
        ...

    def health(self) -> Dict[str, Any]:
        """健康检查。"""
        ...