"""agent_workbench/ui/workbench_ui_controller.py — V6 UI 与 Agent Workbench Runtime 的桥梁。

设计边界：
- 完全复用 v6.ui_controller.UIController 的信号契约与 Session/Chat/Config 服务，
  保证 v6 三栏 UI 无需改动即可工作。
- 聊天请求不再提交给 v6 LocalRuntimeAdapter，而是转发给
  agent_workbench.controller.WorkbenchController，使配置面板中调整的模型、
  Prompt、工具、Memory 等参数真正影响当前对话。
- 设置按钮事件触发右侧「配置」标签页切换。
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable

from v6.runtime.adapter import IRuntimeAdapter
from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent
from v6.ui_controller import UIController

from agent_workbench.controller import WorkbenchController

if TYPE_CHECKING:
    from v6.services.chat_service import ChatService
    from v6.services.config_service import ConfigService
    from v6.services.session_service import SessionService


class NoopRuntimeAdapter(IRuntimeAdapter):
    """占位 Runtime Adapter，避免 v6 UIController 自行启动额外的 AgentRuntime。"""

    def __init__(self) -> None:
        self._callbacks: dict[str, list[Callable[[RuntimeEvent], None]]] = {}

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def submit(self, ctx: RuntimeContext) -> str:
        return ctx.task_id

    def cancel(self, task_id: str) -> bool:
        return True

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        self._callbacks.setdefault(event_type, []).append(callback)


class WorkbenchUIController(UIController):
    """Agent Workbench 专用 UI 控制器。"""

    def __init__(
        self,
        parent=None,
        config_service: "ConfigService | None" = None,
        session_service: "SessionService | None" = None,
        chat_service: "ChatService | None" = None,
        workbench: WorkbenchController | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        self._workbench = workbench or WorkbenchController()
        super().__init__(
            parent=parent,
            config_service=config_service,
            session_service=session_service,
            chat_service=chat_service,
            adapter=NoopRuntimeAdapter(),
            data_dir=data_dir,
        )

    @property
    def workbench_controller(self) -> WorkbenchController:
        """暴露给 UI（如 AgentConfigPanel）使用的 Workbench 控制器。"""
        return self._workbench

    def startup(self) -> None:
        """启动 Workbench Runtime，然后复用 v6 的 UI 初始化流程。"""
        self._workbench.start()
        super().startup()

    def shutdown(self) -> None:
        """停止 Workbench Runtime，然后停止 v6 Adapter 占位。"""
        super().shutdown()
        self._workbench.stop()

    def on_settings_requested(self) -> None:
        """左下角设置按钮：切换到右侧配置标签页。"""
        self.sign_switch_tab.emit("config")

    def on_send_msg(self, text: str) -> None:
        """用户发送消息：保存用户消息并提交给 WorkbenchController。"""
        if not self._active_sid:
            self.on_new_session()
        sid = self._active_sid
        if sid is None:
            return

        ctx = self._new_ctx(sid)
        ctx.add_message("user", text)
        self._chat.store(ctx)
        self.sign_chat_user.emit(text)
        self.sign_set_streaming.emit(True)
        with self._lock:
            self._streaming = True
            self._current_session_id = sid
            self._ai_parts = []

        try:
            final_ctx = self._workbench.chat(text, session_id=sid)
            assistant = [m for m in final_ctx.messages if m.role == "assistant"]
            if assistant:
                content = assistant[-1].content
                store_ctx = self._new_ctx(sid)
                store_ctx.add_message("ai", content)
                self._chat.store(store_ctx)
                self.sign_chat_ai.emit(content, "")
                self._ai_parts.append(content)
        except Exception as exc:
            self.sign_chat_ai.emit(f"运行时错误：{exc}", "error")
        finally:
            with self._lock:
                self._streaming = False
                self._current_task_id = None
                self._current_session_id = None
                self._ai_parts = []
            self.sign_stream_end.emit()
            self.sign_set_streaming.emit(False)
