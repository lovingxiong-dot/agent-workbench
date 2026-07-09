"""agent_workbench/controller.py — Agent Workbench V6 控制器。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 只持有 AgentWorkbenchRuntime，不直接持有 Module。
- 为 UI 提供统一 API。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.enums import RuntimeState
from v6.runtime.manager import Manager
from v6.runtime.task import Task
from v6.runtime.types import ChatMessage
from v6.runtime.user_request import UserRequest

from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime
from agent_workbench.runtime.decision import RuntimeMode
from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource, WorkbenchInteractionLayer
from agent_workbench.runtime.manager.decision_manager import DecisionManager
from agent_workbench.metadata import MetadataDefinition
from agent_workbench.runtime.modules.memory_module import MemoryModule
from agent_workbench.services.manager import AgentManager


class WorkbenchController:
    """Agent Workbench V6 控制器。"""

    def __init__(
        self,
        runtime: AgentWorkbenchRuntime | None = None,
        config_path: str | None = None,
        manager: Manager | None = None,
    ) -> None:
        self._runtime = runtime or AgentWorkbenchRuntime(config_path=config_path)
        # 兼容外部注入的 Manager；缺省使用 Runtime 内部的 DecisionManager。
        self._manager = manager or self._runtime.decision_manager
        self._interaction = WorkbenchInteractionLayer(runtime=self._runtime)

    def start(self) -> None:
        """启动 Runtime。"""
        self._runtime.start()

    def stop(self) -> None:
        """停止 Runtime。"""
        self._runtime.stop()

    @property
    def core_runtime(self):
        """暴露底层 v6 AgentRuntime，供 UI 订阅 EventBus。"""
        return self._runtime.core_runtime

    @property
    def runtime(self) -> AgentWorkbenchRuntime:
        """暴露 AgentWorkbenchRuntime，供 UI 访问模块注册表等内部能力。"""
        return self._runtime

    @property
    def interaction_layer(self) -> WorkbenchInteractionLayer:
        """暴露 Interaction Boundary Layer，供 UI 非阻塞提交请求。"""
        return self._interaction

    def submit_request(self, request: RuntimeRequest) -> str:
        """非阻塞提交 RuntimeRequest，返回 request_id。"""
        return self._interaction.submit_request(request)

    def submit_task(self, task: Task) -> RuntimeContext:
        """提交任意 Task，返回最终 RuntimeContext。"""
        return self._runtime.submit_task(task)

    def chat(
        self,
        text: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> RuntimeContext:
        """提交一条用户消息（chat 兼容包装），返回最终 RuntimeContext。

        Commit 6：通过 RuntimeRequest 进入 Interaction Layer。
        - CHAT 模式不进入 Runtime 执行层，直接返回完成上下文。
        - ACTION / WORKFLOW 模式生成 Task 并调用 submit_task()。
        """
        request = RuntimeRequest(
            source=RuntimeRequestSource.GLOBAL_CHAT,
            text=text,
            session_id=session_id,
            task_id=task_id,
        )

        if hasattr(self._manager, "decide"):
            decision = self._manager.decide(request.to_user_request())
            if decision.mode == RuntimeMode.CHAT:
                # _build_chat_context 仍保留在 Controller，不提前迁移。
                return self._build_chat_context(request.to_user_request(), decision)

        return self._interaction.execute_request(request)

    def _build_chat_context(
        self,
        request: UserRequest,
        decision,
    ) -> RuntimeContext:
        """为 CHAT 模式构造不进入 Runtime 的完成上下文。"""
        ctx = RuntimeContext.new(
            task_id=request.task_id,
            session_id=request.session_id,
        )
        ctx.status = RuntimeState.COMPLETED
        ctx.metadata["decision"] = decision.to_dict()
        ctx.metadata["skipped_runtime"] = True
        if request.text:
            ctx.messages.append(ChatMessage(role="user", content=request.text))
        return ctx

    def chat_with_tool(
        self,
        tool: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> RuntimeContext:
        """提交一条工具执行任务（chat 兼容包装）。"""
        request = RuntimeRequest(
            source=RuntimeRequestSource.COMMAND_BAR,
            session_id=session_id,
            metadata={
                "task_type": "tool",
                "tool_request": {"tool": tool, "args": args},
            },
        )
        return self._interaction.execute_request(request)

    def get_state(self) -> Dict[str, Any]:
        """返回当前 Runtime 状态。"""
        session_module = self._runtime.module_registry.get("session")
        if session_module is None:
            return {}
        return session_module.current_state()

    def get_overview(self) -> Dict[str, Any]:
        """返回 Overview 面板数据。"""
        return self._runtime.get_overview()

    def get_module_metadata(self, namespace: str) -> MetadataDefinition | None:
        """获取指定模块的 Capability Metadata。"""
        return self._runtime.get_module_metadata(namespace)

    def apply_config_change(self, namespace: str) -> None:
        """手动触发某个 namespace 的 Module 热更新。"""
        self._runtime.apply_config(namespace)

    def get_config_value(self, path: str, default: Any = None) -> Any:
        """读取配置。"""
        return self._runtime.config.get(path, default)

    def set_config_value(self, path: str, value: Any) -> None:
        """写入配置并触发 Module 热更新。"""
        self._runtime.config.set(path, value)

    def trace_timeline(self, task_id: str) -> list[Dict[str, Any]]:
        """返回指定任务的 Trace Timeline。"""
        ctx = self._runtime.core_runtime.orchestrator.context(task_id)
        if ctx is None:
            return []
        return ctx.trace.snapshot().get("steps", [])
