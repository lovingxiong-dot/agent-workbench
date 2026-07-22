"""presentation/renderers/v6_ui/event_renderer.py — 事件流渲染器。

V6UIEventRenderer 实现 UIEventRenderer 协议（duck typing）：
将 InteractionEvent 映射到 v6/ui 纯 UI 组件的公共方法。

约束：
  ✓ 允许引用 Interaction Contract（runtime.interaction.event）
  ✓ 只引用 v6/ui 组件公共 API
  ✗ 不引用 Runtime Implementation（engine, executor, session, llm, tool）
  ✗ 不 import PySide6（v6/ui 组件内部处理）
  ✗ 不 import WorkbenchUIController
  ✗ 不穿透 v6/ui 私有成员
"""
from __future__ import annotations

from agent_workbench.runtime.interaction.event import InteractionEvent, InteractionEventType


class V6UIEventRenderer:
    """事件流渲染器：InteractionEvent → v6/ui 组件公共 API。

    实现 UIEventRenderer 协议（render 方法签名匹配），
    不继承任何类，通过 duck typing 满足 InteractionLayer 的期望。
    """

    def __init__(self, chat_area, left_panel=None, right_panel=None) -> None:
        self._chat = chat_area      # v6.ui.chat_area.ChatArea
        self._left = left_panel     # v6.ui.left_panel.LeftPanel (optional)
        self._right = right_panel   # v6.ui.right_panel.RightPanel (optional)

    def render(self, event: InteractionEvent) -> None:
        """UIEventRenderer 协议入口。

        根据 InteractionEventType 分发给对应 v6/ui 组件方法。
        无法识别的事件类型静默忽略。
        """
        handler = {
            InteractionEventType.MESSAGE_DELTA: self._on_message_delta,
            InteractionEventType.MESSAGE_COMPLETE: self._on_message_complete,
            InteractionEventType.MESSAGE_USER: self._on_message_user,
            InteractionEventType.TOOL_STARTED: self._on_tool_started,
            InteractionEventType.TOOL_COMPLETED: self._on_tool_completed,
            InteractionEventType.TASK_STARTED: self._on_task_started,
            InteractionEventType.TASK_FINISHED: self._on_task_finished,
            InteractionEventType.STATUS_UPDATE: self._on_status_update,
            InteractionEventType.CAPABILITY_STEP: self._on_capability_step,
            InteractionEventType.ERROR: self._on_error,
        }.get(event.type)
        if handler:
            handler(event)

    # ── Message Events ──

    def _on_message_user(self, event: InteractionEvent) -> None:
        text = event.payload.get("text", "")
        if text:
            self._chat.append_user(text)

    def _on_message_delta(self, event: InteractionEvent) -> None:
        text = event.payload.get("text", "")
        if text:
            self._chat.stream_chunk(text)

    def _on_message_complete(self, event: InteractionEvent) -> None:
        self._chat.stream_end()

    # ── Tool Events ──

    def _on_tool_started(self, event: InteractionEvent) -> None:
        name = event.payload.get("name", "")
        self._chat.tool_executed(name, {}, "running")

    def _on_tool_completed(self, event: InteractionEvent) -> None:
        name = event.payload.get("name", "")
        result = event.payload.get("result", {})
        status = event.payload.get("status", "ok")
        self._chat.tool_executed(name, result, status)

    # ── Task Events ──

    def _on_task_started(self, event: InteractionEvent) -> None:
        self._chat.set_streaming(True)

    def _on_task_finished(self, event: InteractionEvent) -> None:
        self._chat.set_streaming(False)

    # ── Status / Capability ──

    def _on_status_update(self, event: InteractionEvent) -> None:
        pass  # Phase 2-C：更新状态栏

    def _on_capability_step(self, event: InteractionEvent) -> None:
        index = event.payload.get("index", 1)
        step = event.payload.get("capability_id", event.payload.get("step", ""))
        if step:
            self._chat.add_capability_step(index, step)

    # ── Error ──

    def _on_error(self, event: InteractionEvent) -> None:
        msg = event.payload.get("message", "未知错误")
        self._chat.append_ai(f"[{msg}]", "error")
        self._chat.stream_end()