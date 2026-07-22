"""presentation/protocols/foundation/event.py — EventBus Contract。

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
import time


class EventChannel(str, Enum):
    """事件通道分类。"""
    RUNTIME = "runtime"            # Runtime 内部事件
    INTERACTION = "interaction"    # Runtime ↔ UI 交互事件
    AGENT = "agent"                # Agent 执行事件
    WORKFLOW = "workflow"          # Workflow 任务事件
    SYSTEM = "system"              # 系统级事件（启动、停止、错误）


@dataclass
class EventEnvelope:
    """跨边界事件容器。

    字段：
    - event_id: 事件唯一标识。
    - event_type: 事件类型（如 "task.started", "agent.message.delta"）。
    - channel: 事件通道。
    - source: 事件来源（runtime_id / agent_id / session_id / system）。
    - timestamp: 事件产生时间戳。
    - payload: 事件载荷。
    - correlation_id: 关联 ID（用于追踪因果链）。
    """
    event_id: str
    event_type: str
    channel: EventChannel
    source: str
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}


EventHandler = "EventHandlerCallable"  # 避免运行时循环引用
# 实际类型签名：Callable[[EventEnvelope], None]


class EventBus(Protocol):
    """EventBus Contract — Foundation 共享事件总线。

    关键操作：
      - publish: 发布事件到指定通道。
      - subscribe: 订阅通道事件。
      - unsubscribe: 取消订阅。
      - history: 查询最近事件历史。

    约束：
      - 通道隔离：跨通道不互串。
      - 异步安全：允许后台线程发布事件。
    """

    def publish(
        self,
        channel: EventChannel,
        event_type: str,
        payload: Dict[str, Any],
        source: str,
        correlation_id: str | None = None,
    ) -> str:
        """发布一个事件到指定通道，返回 event_id。"""
        ...

    def subscribe(
        self,
        channel: EventChannel,
        handler: Any,  # Callable[[EventEnvelope], None]
    ) -> str:
        """订阅一个通道事件，返回 subscription_id。"""
        ...

    def unsubscribe(self, subscription_id: str) -> None:
        """取消订阅。"""
        ...

    def history(
        self,
        channel: EventChannel | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> List[EventEnvelope]:
        """查询最近事件历史（可选通道/类型过滤）。"""
        ...