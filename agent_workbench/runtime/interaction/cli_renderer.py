"""agent_workbench/runtime/interaction/cli_renderer.py — CLI 流式渲染器。

实现 UIEventRenderer 协议，在终端逐字输出 AI 回复。
不依赖任何 UI 框架（Qt / Web），纯 stdout 输出。

约束：
- 在 EventBus 后台线程运行，直接 print 到 stdout。
- 不修改 Frozen Zone 文件。
- 通过 Extension Point（Interaction Layer）接入。
"""
from __future__ import annotations

import sys
import threading

from agent_workbench.runtime.interaction.event import InteractionEvent, InteractionEventType
from agent_workbench.runtime.interaction.renderer import UIEventRenderer


class CLIStreamRenderer:
    """CLI 流式渲染器 — 逐字输出 AI 回复到终端。

    使用示例:
        renderer = CLIStreamRenderer()
        controller.interaction_layer.set_renderer(renderer)
        controller.chat("你好")  # 阻塞，但渲染器会逐字输出
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streaming = False
        self._error_occurred = False

    def render(self, event: InteractionEvent) -> None:
        """渲染 InteractionEvent 到终端输出。

        CLI 单线程模式不需要 task_id 过滤，直接输出所有流式事件。
        """
        if event.type == InteractionEventType.MESSAGE_DELTA:
            self._on_delta(event)
        elif event.type == InteractionEventType.MESSAGE_COMPLETE:
            self._on_complete(event)
        elif event.type == InteractionEventType.ERROR:
            self._on_error(event)
        elif event.type == InteractionEventType.TASK_FINISHED:
            self._on_task_finished(event)
        # STATUS_UPDATE, TOOL_STARTED, TOOL_COMPLETED 等事件在 CLI 中静默

    def _on_delta(self, event: InteractionEvent) -> None:
        """流式文本块 → 逐字输出。"""
        with self._lock:
            self._streaming = True
        text = event.payload.get("text", "")
        if text:
            sys.stdout.write(text)
            sys.stdout.flush()

    def _on_complete(self, event: InteractionEvent) -> None:
        """流式结束 → 换行。"""
        with self._lock:
            self._streaming = False
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _on_error(self, event: InteractionEvent) -> None:
        """错误事件 → 输出错误信息。"""
        with self._lock:
            self._error_occurred = True
            self._streaming = False
        msg = event.payload.get("message", "Unknown error")
        sys.stdout.write(f"\n[错误] {msg}\n")
        sys.stdout.flush()

    def _on_task_finished(self, event: InteractionEvent) -> None:
        """任务结束 → 重置状态。"""
        with self._lock:
            self._streaming = False

    def reset(self, task_id: str | None = None) -> None:
        """重置渲染器状态，准备新一轮流式输出。"""
        with self._lock:
            self._streaming = False
            self._error_occurred = False