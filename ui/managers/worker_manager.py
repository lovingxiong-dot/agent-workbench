"""
WorkerManager — AgentWorker 生命周期唯一权威（v3）

职责：
- 按 session_id 创建、停止、复用 Worker
- 每个 Worker 绑定 SignalAdapter，所有输出转换为 MessageBus 事件
- 支持 pause/resume，切会话时不停止后台 Worker
- 不直接操作 UI，不维护当前会话状态
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.event_bus import MessageBus
from workers.agent_worker import AgentWorker, TOOL_DEFINITIONS
from ui.managers.signal_adapter import SignalAdapter

logger = logging.getLogger(__name__)


class WorkerManager(QObject):
    """AgentWorker 生命周期管理器（v3 事件驱动版）"""

    worker_created = Signal(str)   # session_id
    worker_stopped = Signal(str)   # session_id

    def __init__(
        self,
        config_service,
        context_service,
        message_bus: MessageBus,
        llm_registry,
        tool_map: dict = None,
        parent=None,
    ):
        super().__init__(parent)
        self._config_service = config_service
        self._context_service = context_service
        self._bus = message_bus
        self._llm_registry = llm_registry
        self._tool_map = tool_map or {}

        self._workers: dict[str, AgentWorker] = {}
        self._adapters: dict[str, SignalAdapter] = {}

        # v3: 任务完成后自动停止 Worker
        self._subscribe_events()

    def _subscribe_events(self):
        try:
            from core.events import (
                TaskCompletedEvent,
                WorkerCreatedEvent,
                WorkerExecuteRequiredEvent,
                WorkerVerifyRequiredEvent,
            )

            self._bus.subscribe_name(
                "worker", "created",
                lambda event: self.create_worker(
                    session_id=event.session_id,
                    mode=event.mode,
                    model=event.model,
                    tools=event.tools,
                    context=event.context,
                )
                if isinstance(event, WorkerCreatedEvent) else None,
            )
            self._bus.subscribe_name(
                "worker", "execute_required",
                lambda event: self.execute_task(
                    session_id=event.session_id,
                    task_list=event.task_list,
                    original_text=event.original_text,
                    context=event.context,
                )
                if isinstance(event, WorkerExecuteRequiredEvent) else None,
            )
            self._bus.subscribe_name(
                "worker", "verify_required",
                lambda event: self.verify_task(
                    session_id=event.session_id,
                    execution_results=event.execution_results,
                    local_details=event.local_details,
                    context=event.context,
                )
                if isinstance(event, WorkerVerifyRequiredEvent) else None,
            )
            self._bus.subscribe_name(
                "task", "completed",
                lambda event: self.stop_worker(event.session_id)
                if isinstance(event, TaskCompletedEvent) else None,
            )
        except Exception as e:
            logger.warning("WorkerManager event subscription error: %s", e)

    def create_worker(
        self,
        session_id: str,
        mode: str,
        model: str,
        tools: list,
        context: str,
    ) -> Optional[AgentWorker]:
        """创建并启动指定会话的 AgentWorker"""
        # 如果已存在，先停止旧的
        if session_id in self._workers:
            self.stop_worker(session_id)

        llm = self._resolve_llm(model)
        if llm is None:
            logger.error("WorkerManager: cannot resolve LLM for model %s", model)
            return None

        mode_config = self._config_service.get_mode_config(mode)
        default_prompt = mode_config.get("system_prompt", "你是全能 AI 助手。")
        user_rules = self._config_service.get("user_rules", [])
        max_tool_rounds = self._config_service.get_max_tool_rounds(mode)
        task_timeout = self._config_service.get_task_timeout(mode)
        llm_timeout = self._config_service.get_llm_timeout(mode)
        tool_timeout = self._config_service.get_tool_timeout(mode)

        worker = AgentWorker(
            mode_name=mode,
            current_llm=llm,
            current_tools=tools,
            session_id=session_id,
            system_prompt=default_prompt,
            tool_map=self._tool_map,
            tool_definitions=TOOL_DEFINITIONS,
            enable_streaming=True,
            user_rules=user_rules,
            max_tool_rounds=max_tool_rounds,
            task_timeout=task_timeout,
            llm_timeout=llm_timeout,
            tool_timeout=tool_timeout,
            project_root=self._context_service.get_project_root(),
            workspace_context=context,
            app_version=self._config_service.get("app.version", "v3.x"),
        )

        adapter = SignalAdapter(worker, session_id, self._bus, parent=self)

        self._workers[session_id] = worker
        self._adapters[session_id] = adapter

        worker.start()
        self.worker_created.emit(session_id)
        logger.info("Worker created for session: %s", session_id)
        return worker

    def execute_task(
        self,
        session_id: str,
        task_list: list,
        original_text: str,
        context: str,
    ):
        """请求 Worker 执行指定任务清单"""
        worker = self._workers.get(session_id)
        if worker is None:
            logger.warning("execute_task: no worker for %s", session_id)
            return
        worker.request_execute(task_list, original_text, context)

    def verify_task(
        self,
        session_id: str,
        execution_results: list,
        local_details: str,
        context: str,
    ):
        """请求 Worker 验证执行结果"""
        worker = self._workers.get(session_id)
        if worker is None:
            logger.warning("verify_task: no worker for %s", session_id)
            return
        worker.request_verify(execution_results, local_details, context)

    def stop_worker(self, session_id: str):
        """停止指定会话的 Worker 并清理 Adapter"""
        adapter = self._adapters.pop(session_id, None)
        if adapter:
            adapter.disconnect_all()
            adapter.deleteLater()

        worker = self._workers.pop(session_id, None)
        if worker is None:
            return

        try:
            if worker.isRunning():
                worker.stop()
                if not worker.wait(3000):
                    worker.terminate()
                    worker.wait(1000)
        except Exception as e:
            logger.warning("Error stopping worker for %s: %s", session_id, e)

        self.worker_stopped.emit(session_id)
        logger.info("Worker stopped for session: %s", session_id)

    def stop_all_workers(self):
        """停止所有 Worker"""
        for session_id in list(self._workers.keys()):
            self.stop_worker(session_id)

    def pause(self, session_id: str):
        """暂停指定 Worker 的事件转发（切会话时使用）"""
        adapter = self._adapters.get(session_id)
        if adapter:
            adapter.pause()
            logger.debug("Worker paused for session: %s", session_id)

    def resume(self, session_id: str):
        """恢复指定 Worker 的事件转发"""
        adapter = self._adapters.get(session_id)
        if adapter:
            adapter.resume()
            logger.debug("Worker resumed for session: %s", session_id)

    def set_tool_map(self, tool_map: dict):
        """注入工具注册表"""
        self._tool_map = dict(tool_map)

    def has_worker(self, session_id: str) -> bool:
        return session_id in self._workers

    def get_worker(self, session_id: str) -> Optional[AgentWorker]:
        return self._workers.get(session_id)

    def _resolve_llm(self, model: str):
        """通过 LLMRegistry 解析模型实例"""
        try:
            if self._llm_registry.has_provider(model):
                return self._llm_registry.get(model)
            # 尝试第一个可用 provider
            providers = self._llm_registry.list_providers()
            if providers:
                first = next(iter(providers))
                logger.warning("Model %s not found, fallback to %s", model, first)
                return self._llm_registry.get(first)
        except Exception as e:
            logger.warning("Failed to resolve LLM for %s: %s", model, e)
        return None
