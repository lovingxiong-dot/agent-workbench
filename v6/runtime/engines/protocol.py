"""v6/runtime/engines/protocol.py — Engine Protocol、Descriptor 与异常。

设计来源：V6.5 Runtime Foundation Layer Step 3。

核心原则：
- Engine Protocol 只定义生命周期与执行接口，不绑定具体业务。
- Engine 公共接口统一接收 RuntimeContext，request 通过 ctx.request 注入。
- Engine.execute(ctx) -> Any，结果可写入 ctx.result。
- EngineDescriptor 承载 Engine 元数据与依赖关系，为 Plugin Registry / Marketplace 预留扩展点。
- EngineNotReadyError 用于 execute 阶段状态校验。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Protocol

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState


class Engine(Protocol):
    """Engine 协议。

    所有具体 Engine（LLM / Tool / Memory / Planner 等）必须实现此协议。
    接口统一以 RuntimeContext 为唯一输入，不接收独立 request 参数。
    """

    name: str

    def load(self) -> None:
        """加载 Engine 资源（如模型、插件、配置文件）。"""
        ...

    def initialize(self, ctx: RuntimeContext) -> None:
        """初始化 Engine，完成后应进入 READY 状态。"""
        ...

    def health_check(self) -> EngineState:
        """返回 Engine 当前健康状态。"""
        ...

    def execute(self, ctx: RuntimeContext) -> Any:
        """执行 Engine 任务。

        EngineManager 会在调用前将请求写入 ctx.request。
        Engine 可读取 ctx.request / ctx.metrics / ctx.trace / ctx.result 等字段，
        并将结果写入 ctx.result。
        """
        ...

    def shutdown(self) -> None:
        """释放 Engine 资源，完成后进入 STOPPED 状态。"""
        ...


@dataclass
class EngineDescriptor:
    """Engine 元数据描述符。

    用于 Engine Registry、Plugin Loader、Marketplace、UI 状态栏展示。
    """

    name: str
    version: str = "0.0.0"
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    state: EngineState = EngineState.CREATED
    instance: Optional[Engine] = None
    metadata: dict = field(default_factory=dict)


class EngineNotReadyError(RuntimeError):
    """Engine 未就绪时执行抛出。"""

    def __init__(self, name: str, state: Optional[EngineState], expected: List[EngineState]) -> None:
        self.name = name
        self.state = state
        self.expected = expected
        state_value = state.value if state else "missing"
        super().__init__(
            f"Engine '{name}' is {state_value!r}, expected one of "
            f"{[s.value for s in expected]}"
        )
