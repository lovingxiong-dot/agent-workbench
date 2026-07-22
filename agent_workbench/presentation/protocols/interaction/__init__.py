"""presentation/protocols/interaction/ — Interaction Protocol。

定义 Runtime ↔ Presentation 之间的通信契约：
- InteractionCommand: UI → Runtime（用户意图）
- InteractionEvent:  Runtime → UI（执行反馈）
- UIEventRenderer:   Renderer 消费协议

不属于 Runtime 包，不属于 UI 框架。是跨边界的协议层。
"""
from agent_workbench.presentation.protocols.interaction.command import (
    CommandType,
    InteractionCommand,
)
from agent_workbench.presentation.protocols.interaction.event import (
    InteractionEvent,
    InteractionEventType,
)
from agent_workbench.presentation.protocols.interaction.renderer import (
    UIEventRenderer,
)

__all__ = [
    "CommandType",
    "InteractionCommand",
    "InteractionEvent",
    "InteractionEventType",
    "UIEventRenderer",
]