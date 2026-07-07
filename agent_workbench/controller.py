"""agent_workbench/controller.py — Agent Workbench V6 控制器。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 只持有 AgentWorkbenchRuntime，不直接持有 Module。
- 为 UI 提供统一 API。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from v6.runtime.context import RuntimeContext

from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime


class WorkbenchController:
    """Agent Workbench V6 控制器。"""

    def __init__(self, runtime: AgentWorkbenchRuntime | None = None) -> None:
        self._runtime = runtime or AgentWorkbenchRuntime()

    def start(self) -> None:
        """启动 Runtime。"""
        self._runtime.start()

    def stop(self) -> None:
        """停止 Runtime。"""
        self._runtime.stop()

    def chat(self, text: str, session_id: Optional[str] = None) -> RuntimeContext:
        """提交一条用户消息，返回最终 RuntimeContext。"""
        return self._runtime.chat(text, session_id=session_id)

    def chat_with_tool(
        self,
        tool: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> RuntimeContext:
        """提交一条工具执行任务。"""
        # 构造一个带有 tool_request 的 ChatTask
        ctx = self._runtime.current_context()
        # 通过底层 Runtime 提交带 metadata 的任务
        from v6.runtime.context import RuntimeContext as CoreRuntimeContext
        from v6.runtime.enums import RuntimeState
        from v6.runtime.task import Task

        new_ctx = CoreRuntimeContext.new(session_id=session_id)
        new_ctx.metadata["task_type"] = "tool"
        new_ctx.metadata["tool_request"] = {"tool": tool, "args": args}

        task_id = self._runtime.core_runtime.orchestrate(
            Task(task_id=new_ctx.task_id, session_id=session_id, type="tool", payload={"ctx": new_ctx})
        )

        import time
        for _ in range(200):
            state = self._runtime.core_runtime.orchestrator.state(task_id)
            if state in {RuntimeState.COMPLETED, RuntimeState.FAILED}:
                break
            time.sleep(0.01)

        final_ctx = self._runtime.core_runtime.orchestrator.context(task_id)
        if final_ctx is None:
            final_ctx = new_ctx
        return final_ctx

    def get_state(self) -> Dict[str, Any]:
        """返回当前 Runtime 状态。"""
        session_module = self._runtime.module_registry.get("session")
        if session_module is None:
            return {}
        return session_module.current_state()

    def get_overview(self) -> Dict[str, Any]:
        """返回 Overview 面板数据。"""
        return self._runtime.get_overview()

    def get_module_form(self, namespace: str) -> Dict[str, Any]:
        """获取指定模块的 UI 表单。"""
        return self._runtime.get_module_form(namespace)

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
