"""agent_workbench/runtime/interaction/layer.py — Workbench Interaction Boundary Layer。

WorkbenchInteractionLayer 是 UI / MCP / Local Agent 与 Runtime 之间的薄边界：
- 接收 RuntimeRequest。
- 调用 AgentWorkbenchRuntime.submit_request() 非阻塞提交。
- 订阅 EventBus，将 RuntimeEvent 映射为 InteractionEvent。
- 通过 UIEventRenderer 协议把 InteractionEvent 交给 UI。
- 提供 Session / Conversation 操作包装（load / create / delete），让 UI 不必
  直接访问 runtime.module_registry。

约束：
- 不持有 DecisionManager。
- 不做 Capability 路由决策。
- 不依赖任何 UI 框架。
- 不被任何 UI 直接绕过——所有外部输入必须经过本层。
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.enums import RuntimeState

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent, InteractionEventType
from agent_workbench.runtime.interaction.mapper import RuntimeEventMapper
from agent_workbench.presentation.protocols.interaction.renderer import UIEventRenderer
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
            request.to_user_request(), decision,
        )
        return self._runtime.submit_task(task)

    # ═══════════════════════════════════════════════════════════════
    # Session / Conversation 操作（薄包装，禁止 UI 直接访问 Runtime）
    # ═══════════════════════════════════════════════════════════════

    def list_conversation_groups(self) -> list:
        """列出 Conversation 分组。

        Phase 2-D.2.1: 替代 Application 直接调用
        `runtime.module_registry.get("session")` 与 `session_module.manager.list_groups()`。
        返回 v6 ConversationMetadata TypedDict 列表，Application 只做形状转换。
        """
        session_module = self._runtime.module_registry.get("session")
        chat_module = self._runtime.module_registry.get("chat")
        if session_module is None or chat_module is None:
            return []
        from agent_workbench.conversation import ConversationService
        from v6.services.chat_service import ChatService
        from v6.services.session_service import SessionService

        service = ConversationService(
            SessionService(session_module),
            ChatService(chat_module),
        )
        return service.list_groups()

    def create_conversation(
        self,
        title: str = "",
        *,
        summary: str = "",
        icon: str = "",
        workspace_id: str = "",
    ) -> str | None:
        """创建新会话，返回 session_id。

        Phase 2-D.2.1: 替代 Application 直接调用 conversation_service.create_conversation。
        """
        session_module = self._runtime.module_registry.get("session")
        chat_module = self._runtime.module_registry.get("chat")
        if session_module is None or chat_module is None:
            return None
        from agent_workbench.conversation import ConversationService
        from v6.services.chat_service import ChatService
        from v6.services.session_service import SessionService

        service = ConversationService(
            SessionService(session_module),
            ChatService(chat_module),
        )
        return service.create_conversation(
            title=title,
            summary=summary,
            icon=icon,
            workspace_id=workspace_id,
        )

    def delete_conversation(self, sid: str) -> bool:
        """删除会话。

        Phase 2-D.2.1: 替代 Application 直接调用 conversation_service.delete_conversation。
        """
        session_module = self._runtime.module_registry.get("session")
        chat_module = self._runtime.module_registry.get("chat")
        if session_module is None or chat_module is None:
            return False
        from agent_workbench.conversation import ConversationService
        from v6.services.chat_service import ChatService
        from v6.services.session_service import SessionService

        service = ConversationService(
            SessionService(session_module),
            ChatService(chat_module),
        )
        try:
            service.delete_conversation(sid)
            return True
        except Exception:
            return False

    def get_session_metadata(self, sid: str) -> dict | None:
        """获取会话摘要元数据。

        Phase 2-D.2.1: 替代 Application 直接调用 session_module.manager.get(sid)。

        **Boundary Contract**:
        - 仅返回 SessionSummary 字段（id / title / created_at / updated_at）
        - 禁止返回 SessionManager 内部对象
        - 禁止暴露 Runtime 内部数据结构（preview / icon / summary 等 SessionManager
          私有字段不外漏）

        返回 None 表示会话不存在。
        """
        session_module = self._runtime.module_registry.get("session")
        if session_module is None:
            return None
        session = session_module.manager.get(sid)
        if session is None or not isinstance(session, dict):
            return None
        # Boundary Adapter: 仅返白名单字段（Runtime 实际字段名为 sid/title）
        return {
            "id": session.get("sid", sid),
            "title": session.get("title", ""),
            "created_at": session.get("created_at", 0.0),
            "updated_at": session.get("updated_at", 0.0),
        }

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
