"""v6/runtime/runtime.py — AgentRuntime：任务调度、生命周期、错误处理。

职责：
- 接收 UIController 发来的 Task
- 通过 Scheduler 调度执行
- 在 RuntimeContext 中维护任务上下文
- 通过 EventBus 输出运行时事件
- 支持注册任务类型处理器（阶段 5 供 Engines 使用）

设计来源：docs/v6/SPEC.md 第 4 节。
"""
from __future__ import annotations

from typing import Callable

from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import EventBus, RuntimeEvent
from v6.runtime.scheduler import Scheduler
from v6.runtime.task import Task


Handler = Callable[[Task, RuntimeContext, EventBus], None]


class AgentRuntime:
    """业务中枢：接收任务、调度执行、输出事件。"""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        scheduler: Scheduler | None = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._scheduler = scheduler or Scheduler(executor=self._execute)
        self._handlers: dict[str, Handler] = {}
        self._contexts: dict[str, RuntimeContext] = {}
        self._running = False

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def scheduler(self) -> Scheduler:
        return self._scheduler

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """启动 Runtime：先启动 EventBus，再启动 Scheduler。"""
        if self._running:
            return
        self._event_bus.start()
        self._scheduler.start()
        self._running = True

    def stop(self) -> None:
        """停止 Runtime：先停止 Scheduler，再停止 EventBus。"""
        if not self._running:
            return
        self._running = False
        self._scheduler.stop()
        self._event_bus.stop()
        self._contexts.clear()

    def submit(self, task: Task) -> str:
        """提交任务到调度器。"""
        return self._scheduler.submit(task)

    submit_task = submit  # SPEC 接口别名

    def cancel(self, task_id: str) -> bool:
        """取消指定任务。"""
        return self._scheduler.cancel(task_id)

    cancel_task = cancel  # SPEC 接口别名

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        """订阅 Runtime 事件。"""
        self._event_bus.subscribe(event_type, callback)

    def register_handler(self, task_type: str, handler: Handler) -> None:
        """注册任务类型处理器；覆盖内置 EchoHandler。"""
        self._handlers[task_type] = handler

    def _execute(self, task: Task) -> None:
        """Scheduler 工作线程调用的执行入口。"""
        ctx = task.payload.get("ctx")
        if not isinstance(ctx, RuntimeContext):
            ctx = RuntimeContext(
                task_id=task.task_id,
                session_id=task.session_id,
            )
        self._contexts[task.task_id] = ctx
        ctx.set_status("running")
        ctx.trace.add(
            node="runtime",
            action="task_start",
            phase=ctx.phase,
            payload={"task_type": task.type, "session_id": task.session_id},
        )
        try:
            handler = self._handlers.get(task.type)
            if handler is None:
                if task.type == "chat":
                    handler = self._echo_handler
                else:
                    ctx.trace.add(
                        node="runtime",
                        action="handler_missing",
                        phase=ctx.phase,
                        payload={"task_type": task.type},
                    )
                    ctx.set_status("failed")
                    self._event_bus.emit(
                        "error",
                        {"message": f"No handler registered for task type: {task.type}"},
                        task.task_id,
                    )
                    return
            ctx.trace.add(
                node="runtime",
                action="handler_dispatch",
                phase=ctx.phase,
                payload={"handler": task.type},
            )
            handler(task, ctx, self._event_bus)
            ctx.trace.add(
                node="runtime",
                action="task_finish",
                phase=ctx.phase,
                payload={"messages_count": len(ctx.messages)},
            )
            ctx.set_status("completed")
        except Exception as exc:  # pragma: no cover - defensive
            ctx.trace.add(
                node="runtime",
                action="task_error",
                phase=ctx.phase,
                payload={"error": str(exc)},
            )
            ctx.set_status("failed")
            self._event_bus.emit(
                "error",
                {"message": str(exc)},
                task.task_id,
            )
        finally:
            self._contexts.pop(task.task_id, None)

    @staticmethod
    def _echo_handler(task: Task, ctx: RuntimeContext, bus: EventBus) -> None:
        """最小回声处理器：替换上一阶段的 EchoRuntime。"""
        ctx.phase = "inference"
        ctx.trace.add(node="engine", action="echo_start", phase=ctx.phase)
        if ctx.messages:
            text = ctx.messages[-1].content
        else:
            text = getattr(task, "text", task.payload.get("text", ""))
        ctx.trace.add(
            node="engine",
            action="input_read",
            phase=ctx.phase,
            payload={"source": "ctx.messages" if ctx.messages else "task.text", "length": len(text)},
        )
        bus.emit("user_message", {"text": text}, task.task_id)
        ctx.trace.add(
            node="engine",
            action="emit_start",
            phase=ctx.phase,
            payload={"data": {"phase": ""}},
        )
        bus.emit("ai_start", {"phase": ""}, task.task_id)
        response = f"收到：{text.replace(chr(10), ' ')}"
        ctx.trace.add(
            node="engine",
            action="emit_chunk",
            phase=ctx.phase,
            payload={"data": {"text": response, "phase": ""}},
        )
        bus.emit("ai_chunk", {"text": response, "phase": ""}, task.task_id)
        ctx.trace.add(
            node="engine",
            action="emit_end",
            phase=ctx.phase,
            payload={"data": {}},
        )
        bus.emit("ai_end", {}, task.task_id)
        ctx.add_message("ai", response)
        ctx.trace.add(
            node="engine",
            action="echo_end",
            phase=ctx.phase,
            payload={"response_length": len(response)},
        )
