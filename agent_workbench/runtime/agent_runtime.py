"""agent_workbench/runtime/agent_runtime.py — Agent Workbench V6 内部 Runtime。

职责：
- 组合 ConfigStore、ProfileManager、ModuleRegistry、EventBus。
- 持有底层 v6.runtime.runtime.AgentRuntime 负责任务编排。
- 注册 Workbench 专用 Engine（WorkbenchLLMEngine / WorkbenchToolEngine）。
- 通过 ConfigStore 变更通知驱动 Module 热更新。
- 为 WorkbenchController 提供单一入口。
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from v6.runtime.context import RuntimeContext
from v6.runtime.enums import RuntimeState
from v6.runtime.event_bus import EventBus
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.runtime import AgentRuntime as CoreAgentRuntime
from v6.runtime.task import ChatTask

from agent_workbench.engines.workbench_llm_engine import WorkbenchLLMEngine
from agent_workbench.engines.workbench_tool_engine import WorkbenchToolEngine
from agent_workbench.runtime.capability_router import CapabilityRouter
from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import ModuleMetadata
from agent_workbench.runtime.module_registry import ModuleRegistry
from agent_workbench.runtime.modules.config_module import ConfigModule
from agent_workbench.runtime.modules.memory_module import MemoryModule
from agent_workbench.runtime.modules.model_module import ModelModule
from agent_workbench.runtime.modules.profile_module import ProfileModule
from agent_workbench.runtime.modules.prompt_module import PromptModule
from agent_workbench.runtime.modules.runtime_module import RuntimeModule
from agent_workbench.runtime.modules.session_module import SessionModule
from agent_workbench.runtime.modules.strategy_module import StrategyModule
from agent_workbench.runtime.modules.tool_module import ToolModule
from agent_workbench.runtime.modules.trace_module import TraceModule
from agent_workbench.runtime.profile_manager import ProfileManager


class AgentWorkbenchRuntime:
    """Agent Workbench V6 内部 Runtime 封装。"""

    def __init__(self, config_path: str | None = None) -> None:
        self._config = ConfigStore(config_path)
        self._profile_manager = ProfileManager(self._config)
        self._event_bus = EventBus()
        self._capability_router = CapabilityRouter(default_capability="chat")
        # 使用带 CapabilityRouter 的 Orchestrator，使 CAPABILITY_RESOLVED 事件由 Router 发出。
        self._engine_manager = None
        self._orchestrator = Orchestrator(
            event_bus=self._event_bus,
            capability_router=self._capability_router,
        )
        self._core_runtime = CoreAgentRuntime(
            event_bus=self._event_bus,
            orchestrator=self._orchestrator,
        )
        self._registry = ModuleRegistry()
        self._current_context: RuntimeContext | None = None
        self._running = False

        self._register_modules()
        self._register_engines()
        self._subscribe_config_changes()

    @property
    def config(self) -> ConfigStore:
        return self._config

    @property
    def profile_manager(self) -> ProfileManager:
        return self._profile_manager

    @property
    def module_registry(self) -> ModuleRegistry:
        return self._registry

    @property
    def core_runtime(self) -> CoreAgentRuntime:
        return self._core_runtime

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """启动 Runtime 和所有 Module。"""
        if self._running:
            return
        self._core_runtime.start()
        self._registry.initialize_all(self)
        self._registry.apply_all(self._config)
        self._running = True

    def stop(self) -> None:
        """停止 Runtime 并释放 Module 资源。"""
        if not self._running:
            return
        self._running = False
        self._registry.dispose_all()
        self._core_runtime.stop()

    def chat(
        self,
        text: str,
        session_id: str | None = None,
        task_id: str | None = None,
    ) -> RuntimeContext:
        """提交一条用户消息，等待任务完成，返回最终 RuntimeContext。"""
        task_kwargs: dict[str, Any] = {}
        if task_id:
            task_kwargs["task_id"] = task_id
        task = ChatTask(text=text, session_id=session_id, **task_kwargs)
        task_id = self._core_runtime.orchestrate(task)

        # 轮询等待任务完成
        for _ in range(200):
            state = self._core_runtime.orchestrator.state(task_id)
            if state in {RuntimeState.COMPLETED, RuntimeState.FAILED}:
                break
            time.sleep(0.01)

        ctx = self._core_runtime.orchestrator.context(task_id)
        if ctx is None:
            ctx = RuntimeContext.new(task_id=task_id, session_id=session_id)
            ctx.set_status(RuntimeState.FAILED)
        self._current_context = ctx

        # 将用户消息保存到 Memory（如启用）
        memory_module = self._registry.get("memory")
        if isinstance(memory_module, MemoryModule) and memory_module.service is not None:
            memory_module.save(text, namespace="chat_history", task_id=ctx.task_id)

        return ctx

    def current_context(self) -> RuntimeContext | None:
        """返回当前/最近一次任务的 RuntimeContext。"""
        return self._current_context

    def set_decision_policy(self, policy: str) -> None:
        """动态切换决策策略。"""
        planner_loop = self._core_runtime.planner_loop
        if policy == "rule_based":
            from v6.runtime.decision_policy import RuleBasedDecisionPolicy

            planner_loop.set_policy(RuleBasedDecisionPolicy())

    def apply_config(self, namespace: str) -> None:
        """手动触发某个 namespace 的 Module 热更新。"""
        module = self._registry.get(namespace)
        if module is not None:
            module.apply_config(self._config)

    def get_module_metadata(self, namespace: str) -> ModuleMetadata | None:
        """获取某个模块的 Capability Metadata。"""
        module = self._registry.get(namespace)
        if module is None:
            return None
        return module.metadata()

    def get_overview(self) -> Dict[str, Any]:
        """返回 Overview 面板数据。"""
        model_module = self._registry.get("model")
        tool_module = self._registry.get("tool")
        memory_module = self._registry.get("memory")
        prompt_module = self._registry.get("prompt")

        providers = model_module.list_providers() if isinstance(model_module, ModelModule) else []
        tools = tool_module.list_tools() if isinstance(tool_module, ToolModule) else []
        memory_count = 0
        if isinstance(memory_module, MemoryModule) and memory_module.service is not None:
            memory_count = len(memory_module.query(limit=10000))
        templates = prompt_module.list_templates() if isinstance(prompt_module, PromptModule) else []

        return {
            "agent_name": self._config.get("agent.name", "Agent Workbench V6"),
            "current_profile": self._profile_manager.current,
            "default_provider": self._config.get("model.default_provider", "echo"),
            "providers": [p["name"] for p in providers],
            "tool_count": len(tools),
            "memory_count": memory_count,
            "prompt_count": len(templates),
            "current_prompt": self._config.get("prompt.templates", [{}])[0].get("name", ""),
        }

    def _register_modules(self) -> None:
        """注册 10 个 RuntimeModule。"""
        self._registry.register(RuntimeModule())
        self._registry.register(SessionModule())
        self._registry.register(ConfigModule())
        self._registry.register(ProfileModule())
        self._registry.register(PromptModule())
        self._registry.register(ModelModule())
        self._registry.register(ToolModule())
        self._registry.register(MemoryModule())
        self._registry.register(StrategyModule())
        self._registry.register(TraceModule())

    def _register_engines(self) -> None:
        """注册 Workbench 专用 Engine 到底层 EngineManager。"""
        manager = self._core_runtime.engine_manager
        # 清空默认空壳
        for name in list(manager.names()):
            manager.unregister(name)

        model_module = self._registry.get("model")
        tool_module = self._registry.get("tool")
        manager.register(WorkbenchLLMEngine(model_module))
        manager.register(WorkbenchToolEngine(tool_module))

    def _subscribe_config_changes(self) -> None:
        """订阅 ConfigStore 变更，驱动 Module 热更新。"""
        for namespace in self._registry.namespaces():
            self._config.subscribe(namespace, lambda _path, _value, ns=namespace: self._on_config_change(ns))

    def _on_config_change(self, namespace: str) -> None:
        module = self._registry.get(namespace)
        if module is not None:
            module.apply_config(self._config)
