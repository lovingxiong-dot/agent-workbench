"""v6/runtime/adapter.py — RuntimeAdapter：Application Layer 的 Runtime 适配器。

设计来源：docs/v6/SPEC.md 第 8.12、8.13 节。

重要边界：
- Adapter 属于 Application Layer，不属于 Runtime。
- Adapter 不保存状态，所有状态在 RuntimeContext 中。
- Adapter 不做业务，只做：Input → Context → Runtime → Output。
- Runtime 永远不知道是谁在调用它（GUI / Gateway / CLI / MCP）。
- 公共方法统一以 RuntimeContext 作为输入协议，方法名保留语义。

长期演进：
- 当前为本地适配器（LocalRuntimeAdapter），直接转发给 AgentRuntime。
- 未来可扩展：RemoteRuntimeAdapter、WebSocketRuntimeAdapter、MCPRuntimeAdapter 等。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.runtime import AgentRuntime
from v6.runtime.task import Task


class IRuntimeAdapter(ABC):
    """Runtime 适配器协议。

    所有外部调用方（UI、CLI、Web、Gateway、MCP）均通过此协议与 Runtime 交互。
    """

    @abstractmethod
    def submit(self, ctx: RuntimeContext) -> str:
        """提交一个 RuntimeContext 给 Runtime 执行，返回 task_id。"""
        pass

    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        """取消指定任务。"""
        pass

    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        """订阅 Runtime 事件。"""
        pass


class LocalRuntimeAdapter(IRuntimeAdapter):
    """本地 Runtime 适配器：直接把 RuntimeContext 包装为 Task 提交给 AgentRuntime。"""

    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self._runtime = runtime or AgentRuntime()

    @property
    def runtime(self) -> AgentRuntime:
        return self._runtime

    def start(self) -> None:
        """启动底层 Runtime。"""
        self._runtime.start()

    def stop(self) -> None:
        """停止底层 Runtime。"""
        self._runtime.stop()

    def submit(self, ctx: RuntimeContext) -> str:
        """提交 RuntimeContext 到本地 Runtime 执行。"""
        task = Task(
            task_id=ctx.task_id,
            session_id=ctx.session_id,
            type="chat",
            payload={"ctx": ctx},
        )
        return self._runtime.submit(task)

    def cancel(self, task_id: str) -> bool:
        return self._runtime.cancel(task_id)

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        self._runtime.subscribe(event_type, callback)
