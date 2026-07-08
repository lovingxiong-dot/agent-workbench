"""agent_workbench/runtime/interaction/renderer.py — UI 渲染器协议。

UIEventRenderer 是 UI 层必须实现的协议。
它消费 InteractionEvent，而不是 RuntimeEvent。

实现说明：
- 回调通常运行在 EventBus 后台线程，Qt 实现需自行切到主线程（Signal / QMetaObject.invokeMethod）。
- 本文件只定义协议，不包含任何 Qt / Web / CLI 实现。
"""
from __future__ import annotations

from typing import Protocol

from agent_workbench.runtime.interaction.event import InteractionEvent


class UIEventRenderer(Protocol):
    """UI 渲染器协议。

    实现者只需实现一个 render 方法，根据 event.type 分发到对应的 UI 更新。
    """

    def render(self, event: InteractionEvent) -> None:
        """渲染一个 InteractionEvent。"""
        ...
