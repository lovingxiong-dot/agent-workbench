"""agent_workbench/controller.py — Agent Workbench V6 控制器。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 只持有 AgentWorkbenchRuntime，不直接持有 Module。
- 为 UI 提供统一 API。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.manager import Manager
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime
from agent_workbench.runtime.metadata import ModuleMetadata
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
        self._manager = manager or AgentManager()

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

        内部通过 Manager 将输入转换为 Task，再调用 submit_task()。
        """
        request = UserRequest(
            text=text,
            session_id=session_id,
            task_id=task_id,
        )
        task = self._manager.resolve(request)
        ctx = self.submit_task(task)

        # 将用户消息保存到 Memory（如启用）
        memory_module = self._runtime.module_registry.get("memory")
        if isinstance(memory_module, MemoryModule) and memory_module.service is not None:
            memory_module.save(text, namespace="chat_history", task_id=ctx.task_id)

        return ctx

    def chat_with_tool(
        self,
        tool: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> RuntimeContext:
        """提交一条工具执行任务（chat 兼容包装）。"""
        request = UserRequest(
            session_id=session_id,
            metadata={
                "task_type": "tool",
                "tool_request": {"tool": tool, "args": args},
            },
        )
        task = self._manager.resolve(request)
        return self.submit_task(task)

    def get_state(self) -> Dict[str, Any]:
        """返回当前 Runtime 状态。"""
        session_module = self._runtime.module_registry.get("session")
        if session_module is None:
            return {}
        return session_module.current_state()

    def get_overview(self) -> Dict[str, Any]:
        """返回 Overview 面板数据。"""
        return self._runtime.get_overview()

    def get_module_metadata(self, namespace: str) -> ModuleMetadata | None:
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
