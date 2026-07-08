"""agent_workbench/runtime/interaction/layer.py — Workbench Interaction Boundary Layer。

WorkbenchInteractionLayer 是 UI / MCP / Local Agent 与 Runtime 之间的薄边界：
- 接收 RuntimeRequest。
- 调用 AgentWorkbenchRuntime.submit_request() 非阻塞提交。
- 订阅 EventBus，将 RuntimeEvent 映射为 InteractionEvent。
- 通过 UIEventRenderer 协议把 InteractionEvent 交给 UI。

约束：
- 不持有 DecisionManager。
- 不做 Capability 路由决策。
- 不依赖任何 UI 框架。
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.enums import RuntimeState

from agent_workbench.runtime.interaction.event import InteractionEvent, InteractionEventType
from agent_workbench.runtime.interaction.mapper import RuntimeEventMapper
from agent_workbench.runtime.interaction.renderer import UIEventRenderer
from agent_workbench.runtime.interaction.request import RuntimeRequest

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime


class WorkbenchInteractionLayer:
    """Workbench 交互边界层。"""

    def __init__(
        self,
        runtime: "AgentWorkbenchRuntime",
        renderer: UIEventRenderer | None = None,
    ) -> None:
        self._runtime = runtime
        self._mapper = RuntimeEventMapper()
        self._renderer: UIEventRenderer | None = renderer
        self._task_to_request: dict[str, str] = {}
        self._lock = threading.Lock()
        self._subscribed = False
        self._callback: Callable[[RuntimeEvent], None] | None = None
        self._subscribe()

    def set_renderer(self, renderer: UIEventRenderer | None) -> None:
        """设置或移除 UI 渲染器。"""
        self._renderer = renderer

    def submit_request(self, request: RuntimeRequest) -> str:
        """非阻塞提交 RuntimeRequest，返回 request_id。

        CHAT 与 ACTION 都返回 request_id，后续通过 Event Stream 区分。
        Runtime 异常会被捕获并转换为 ERROR InteractionEvent，不会传播给 UI。
        """
        try:
            task_id = self._runtime.submit_request(request)
        except Exception as exc:  # pragma: no cover - 防御性边界保护
            self._render_error(request.request_id, f"Runtime request failed: {exc}")
            return request.request_id

        if task_id is not None:
            with self._lock:
                self._task_to_request[task_id] = request.request_id

        return request.request_id

    def execute_request(self, request: RuntimeRequest) -> RuntimeContext:
        """阻塞执行并返回最终 RuntimeContext（兼容旧 chat()）。"""
        from agent_workbench.runtime.decision import RuntimeMode

        decision = self._runtime.decision_manager.decide(request.to_user_request())

        if decision.mode == RuntimeMode.CHAT:
            return self._runtime.build_chat_context(request.to_user_request(), decision)

        task = self._runtime.decision_manager.resolve_from_decision(
            request.to_user_request(), decision
        )
        return self._runtime.submit_task(task)

    def close(self) -> None:
        """关闭 Interaction Layer：取消 EventBus 订阅并释放资源。"""
        event_bus = self._runtime.core_runtime.event_bus
        if event_bus is not None and self._callback is not None:
            event_bus.unsubscribe("*", self._callback)
        self._callback = None
        self._subscribed = False
        self._renderer = None
        with self._lock:
            self._task_to_request.clear()

    def _subscribe(self) -> None:
        """订阅 Runtime EventBus。"""
        event_bus = self._runtime.core_runtime.event_bus
        if event_bus is None or self._subscribed:
            return
        self._callback = self._on_event
        event_bus.subscribe("*", self._callback)
        self._subscribed = True

    def _on_event(self, event: RuntimeEvent) -> None:
        """RuntimeEvent 回调：映射为 InteractionEvent 并交给 Renderer。"""
        interaction_event = self._map_event(event)
        if interaction_event is None:
            return

        renderer = self._renderer
        if renderer is None:
            return

        try:
            renderer.render(interaction_event)
        except Exception:  # pragma: no cover - renderer 错误不应影响 Runtime
            # UI 渲染异常不得破坏 Runtime 执行。
            pass

    def _render_error(self, request_id: str, message: str) -> None:
        """向 Renderer 输出 ERROR InteractionEvent。"""
        renderer = self._renderer
        if renderer is None:
            return
        try:
            renderer.render(
                InteractionEvent(
                    type=InteractionEventType.ERROR,
                    request_id=request_id,
                    source="interaction_layer",
                    payload={"message": message},
                )
            )
        except Exception:  # pragma: no cover - renderer 错误不得破坏 Runtime
            pass

    def _map_event(self, event: RuntimeEvent) -> InteractionEvent | None:
        """补充 request_id 后调用 Mapper。"""
        request_id = self._resolve_request_id(event)
        interaction_event = self._mapper.map(event)
        if interaction_event is None:
            return None
        if request_id:
            interaction_event.request_id = request_id
        return interaction_event

    def _resolve_request_id(self, event: RuntimeEvent) -> str | None:
        """根据 task_id 查找 request_id。"""
        if not event.task_id:
            return None
        with self._lock:
            return self._task_to_request.get(event.task_id)
