"""presentation/renderers/cli_renderer.py — CLI Renderer。

Phase 2-C.4：实现 RendererProtocol 的 CLI Renderer。
用于 Multi Renderer Proof——证明 PresentationRuntime 可以驱动
不同 UI 技术栈的 Renderer。

约束：
  ✓ 纯 stdout 输出，零 UI 框架依赖
  ✗ 禁止 PySide6、QWidget、v6/ui
  ✗ 禁止 Runtime Implementation import
"""
from __future__ import annotations

import sys
from typing import List

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent, InteractionEventType
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    WorkspaceState,
)


class CLIRenderer:
    """CLI Renderer — 终端输出 Renderer。

    实现 RendererProtocol（duck typing），
    将 InteractionEvent 和 Shell State 输出到终端。

    设计目的：
    - Phase 2-C.4 Multi Renderer Proof 的第二 Renderer
    - 证明 PresentationRuntime 不感知 Renderer 类型
    - 未来可作为 headless / CI / 调试模式使用
    """

    def __init__(self, prefix: str = "CLI") -> None:
        self._prefix = prefix
        self._started = False
        self._events: list[InteractionEvent] = []  # 用于验证

    # ── Lifecycle ──

    def start(self) -> None:
        self._started = True
        self._log("STARTED")

    def stop(self) -> None:
        self._started = False
        self._log("STOPPED")

    # ── Event Rendering ──

    def render(self, event: InteractionEvent) -> None:
        """渲染 InteractionEvent 到终端。

        Phase 2-C.4 证明用：事件类型 → 终端输出。
        """
        self._events.append(event)
        handler = {
            InteractionEventType.MESSAGE_DELTA: self._on_delta,
            InteractionEventType.MESSAGE_COMPLETE: self._on_complete,
            InteractionEventType.MESSAGE_USER: self._on_user,
            InteractionEventType.TOOL_STARTED: self._on_tool_started,
            InteractionEventType.TOOL_COMPLETED: self._on_tool_completed,
            InteractionEventType.TASK_STARTED: self._on_task_started,
            InteractionEventType.TASK_FINISHED: self._on_task_finished,
            InteractionEventType.STATUS_UPDATE: self._on_status,
            InteractionEventType.CAPABILITY_STEP: self._on_step,
            InteractionEventType.ERROR: self._on_error,
        }.get(event.type)
        if handler:
            handler(event)

    def _on_delta(self, event: InteractionEvent) -> None:
        text = event.payload.get("text", "")
        sys.stdout.write(text)
        sys.stdout.flush()

    def _on_complete(self, event: InteractionEvent) -> None:
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _on_user(self, event: InteractionEvent) -> None:
        text = event.payload.get("text", "")
        self._log(f"USER: {text}")

    def _on_tool_started(self, event: InteractionEvent) -> None:
        name = event.payload.get("name", "")
        self._log(f"TOOL START: {name}")

    def _on_tool_completed(self, event: InteractionEvent) -> None:
        name = event.payload.get("name", "")
        self._log(f"TOOL DONE: {name}")

    def _on_task_started(self, event: InteractionEvent) -> None:
        self._log("TASK STARTED")

    def _on_task_finished(self, event: InteractionEvent) -> None:
        self._log("TASK FINISHED")

    def _on_status(self, event: InteractionEvent) -> None:
        status = event.payload.get("status", "")
        self._log(f"STATUS: {status}")

    def _on_step(self, event: InteractionEvent) -> None:
        step = event.payload.get("capability_id", event.payload.get("step", ""))
        self._log(f"  STEP: {step}")

    def _on_error(self, event: InteractionEvent) -> None:
        msg = event.payload.get("message", "Unknown error")
        self._log(f"ERROR: {msg}")

    # ── Shell State Sync ──

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        self._log(f"NAV: {len(groups)} groups")
        for g in groups:
            self._log(f"  [{g.id}] {g.title} ({len(g.items)} items)")

    def update_workspace(self, state: WorkspaceState) -> None:
        self._log(f"WORKSPACE: {state.title} | {state.subtitle} | {len(state.messages)} msgs")

    def update_inspector(self, state: InspectorState) -> None:
        self._log(f"INSPECTOR: {state.object_id} ({len(state.properties)} props)")

    def update_command(self, state: CommandState) -> None:
        self._log(f"COMMAND: prompt='{state.prompt}' processing={state.is_processing}")

    # ── Helpers ──

    def _log(self, msg: str) -> None:
        sys.stderr.write(f"[{self._prefix}] {msg}\n")
        sys.stderr.flush()

    @property
    def event_count(self) -> int:
        return len(self._events)

    def clear_events(self) -> None:
        self._events.clear()