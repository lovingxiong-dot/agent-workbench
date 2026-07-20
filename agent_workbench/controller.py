"""agent_workbench/controller.py — Agent Workbench V6 控制器。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 只持有 AgentWorkbenchRuntime，不直接持有 Module。
- 为 UI 提供统一 API。
- 所有请求通过 Interaction Layer 进入 Runtime，DecisionManager 只调用一次。
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.manager import Manager
from v6.runtime.task import Task

from agent_workbench.package import PackageExecutor, PackageRegistry
from agent_workbench.runtime.agent_runtime import AgentWorkbenchRuntime
from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource, WorkbenchInteractionLayer
from agent_workbench.runtime.manager.decision_manager import DecisionManager
from agent_workbench.runtime.modules.session_module import SessionModule
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
        package_registry: PackageRegistry | None = None,
    ) -> None:
        self._runtime = runtime or AgentWorkbenchRuntime(config_path=config_path)
        # 兼容外部注入的 Manager；缺省使用 Runtime 内部的 DecisionManager。
        self._manager = manager or self._runtime.decision_manager
        self._interaction = WorkbenchInteractionLayer(runtime=self._runtime)
        self._package_registry = package_registry
        self._package_executor = PackageExecutor()
        self._session_id: str | None = None

    def start(self) -> None:
        """启动 Runtime，恢复上次会话。"""
        self._runtime.start()
        # 恢复上次活跃 Session
        session_module = self._runtime.module_registry.get("session")
        if isinstance(session_module, SessionModule):
            restored = session_module.load_last_active()
            if restored:
                self._session_id = restored

    def stop(self) -> None:
        """停止 Runtime，持久化当前 Session。"""
        session_module = self._runtime.module_registry.get("session")
        if isinstance(session_module, SessionModule):
            session_module.persist()
            session_module.save_last_active()
        self._runtime.stop()

    @property
    def session_id(self) -> str | None:
        """当前活跃 Session ID。"""
        return self._session_id

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
        """提交一条用户消息，返回最终 RuntimeContext。

        统一入口：所有请求（CLI / GUI / MCP / API）都通过 Interaction Layer
        进入 Runtime，DecisionManager 只调用一次。
        """
        # 自动创建或使用已有 Session
        sid = session_id or self._session_id
        if sid is None:
            sid = uuid.uuid4().hex[:12]
            self._session_id = sid
            session_module = self._runtime.module_registry.get("session")
            if isinstance(session_module, SessionModule):
                session_module.start_session(sid)

        request = RuntimeRequest(
            source=RuntimeRequestSource.GLOBAL_CHAT,
            text=text,
            session_id=sid,
            task_id=task_id,
        )
        return self._interaction.execute_request(request)

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

    def switch_provider(self, provider_name: str) -> bool:
        """运行时切换 Model Provider，无需重启 Runtime。

        Args:
            provider_name: 目标 Provider 名称（如 "agnes"、"deepseek"）。

        Returns:
            True 如果切换成功。
        """
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return False
        return model_module.switch_provider(provider_name)

    def switch_model(self, model_name: str) -> bool:
        """运行时切换模型（在当前 Provider 内）。

        Args:
            model_name: 目标模型名称（如 "agnes-2.0-flash"）。

        Returns:
            True 如果切换成功。
        """
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return False
        return model_module.switch_model(model_name)

    def get_current_provider(self) -> str:
        """返回当前 Provider 名称。"""
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return ""
        return model_module.get_current_provider_name()

    def get_current_model(self) -> str:
        """返回当前模型名称。"""
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return ""
        return model_module.current_model

    def list_models(self) -> list[str]:
        """返回当前 Provider 的可用模型列表。"""
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return []
        return model_module.list_models()

    def list_providers(self) -> list[str]:
        """返回可用 Provider 名称列表。"""
        model_module = self._runtime.module_registry.get("model")
        if model_module is None:
            return []
        return [p["name"] for p in model_module.list_providers()]

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

    def execute_agent_action(self, package_id: str, action_id: str) -> Dict[str, Any]:
        """执行指定 Package Agent 的 action。

        这是 Commit 12.4 的入口：UI / CommandBar / MCP 触发 Package Action 后，
        统一交给 Controller，由 PackageExecutor 更新运行时统计并返回结果。
        当前实现为 Application Layer 直接执行；后续可在此方法内扩展为
        RuntimeRequest → Orchestrator → Tool Engine 的完整链路。
        """
        if self._package_registry is None:
            return {"status": "failed", "error": "package registry not configured"}

        package = self._package_registry.get(package_id)
        if package is None:
            return {"status": "failed", "error": f"package not found: {package_id}"}

        result = self._package_executor.execute(package, action_id)

        # 发布 TASK_STARTED / TASK_COMPLETED 事件，使 Trace Workspace 可观测。
        event_bus = self._runtime.core_runtime.event_bus
        if event_bus is not None:
            from v6.runtime.event_bus import RuntimeEventType

            event_bus.publish(
                RuntimeEventType.TASK_STARTED,
                {"package_id": package_id, "action_id": action_id},
                source="package_executor",
            )
            event_bus.publish(
                RuntimeEventType.TASK_COMPLETED,
                {"result": result},
                source="package_executor",
            )

        return result
