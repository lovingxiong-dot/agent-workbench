"""
session_orchestrator.py — v3 会话协调器

单一协调权威：
- 持有所有 SessionRuntime
- 订阅 MessageBus 事件并路由到正确的运行时
- 所有 TaskService 写操作必须通过本类发起
- 保证任务完成路径唯一、会话切换状态不被覆盖
"""
from typing import Dict, Optional
from datetime import datetime

from PySide6.QtCore import QObject

from core.event_bus import MessageBus
from core.events import (
    UserSendEvent,
    UserStopEvent,
    UserConfirmEvent,
    UserReanalyzeEvent,
    UserSkipVerifyEvent,
    SessionCreateEvent,
    SessionSwitchEvent,
    SessionDeleteEvent,
    QueueEnqueueEvent,
    QueueTaskReadyEvent,
    QueueTaskStoppedEvent,
    PhaseAnalyzeRequiredEvent,
    PhaseConfirmRequiredEvent,
    PhaseExecuteRequiredEvent,
    PhaseVerifyRequiredEvent,
    PhaseArchiveRequiredEvent,
    PhaseFlowCompletedEvent,
    PhaseErrorEvent,
    WorkerResultEvent,
    WorkerChunkEvent,
    WorkerErrorEvent,
    WorkerToolExecutedEvent,
    UIAppendUserEvent,
    UIClearPhaseUIEvent,
    UISetStreamingEvent,
    UIUpdateSessionStatusEvent,
    UIShowConfirmationEvent,
    UIHideConfirmationEvent,
    UIShowSkipVerifyEvent,
    UIHideSkipVerifyEvent,
    UIUpdateStatusBarEvent,
)
from services.app_context import AppContext
from services.session_runtime import SessionRuntime
from services.task_service import TaskService
from workers.session_task import SessionTask, TaskStatus
from agent_engine.phase_manager import PhaseManager, TaskItem


class SessionOrchestrator(QObject):
    """
    v3 核心协调器。

    职责边界：
    - 不直接操作 UI（只发射 ui.* 事件）
    - 不直接调用 LLM / 工具（通过 WorkerManager）
    - 只维护会话运行时映射和任务状态机闭环
    """

    def __init__(
        self,
        app_context: AppContext,
        message_bus: MessageBus,
        task_service: TaskService,
        parent=None,
    ):
        super().__init__(parent)
        self._app_ctx = app_context
        self._bus = message_bus
        self._task_service = task_service
        self._runtimes: Dict[str, SessionRuntime] = {}
        self._current_session_id: Optional[str] = None

        self._subscribe_events()

    # ═══════════════════════════════════════════════════
    # 公共查询
    # ═══════════════════════════════════════════════════
    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id

    def get_runtime(self, session_id: str) -> Optional[SessionRuntime]:
        return self._runtimes.get(session_id)

    def has_runtime(self, session_id: str) -> bool:
        return session_id in self._runtimes

    # ═══════════════════════════════════════════════════
    # 事件订阅
    # ═══════════════════════════════════════════════════
    def _subscribe_events(self):
        self._bus.subscribe(self._on_user_send, namespace="user")
        self._bus.subscribe(self._on_user_stop, namespace="user")
        self._bus.subscribe(self._on_user_confirm, namespace="user")
        self._bus.subscribe(self._on_user_reanalyze, namespace="user")
        self._bus.subscribe(self._on_user_skip_verify, namespace="user")

        self._bus.subscribe(self._on_session_create, namespace="session")
        self._bus.subscribe(self._on_session_switch, namespace="session")
        self._bus.subscribe(self._on_session_delete, namespace="session")

        self._bus.subscribe(self._on_queue_task_ready, namespace="queue")
        self._bus.subscribe(self._on_queue_task_stopped, namespace="queue")

        self._bus.subscribe(self._on_phase_analyze, namespace="phase")
        self._bus.subscribe(self._on_phase_confirm, namespace="phase")
        self._bus.subscribe(self._on_phase_execute, namespace="phase")
        self._bus.subscribe(self._on_phase_verify, namespace="phase")
        self._bus.subscribe(self._on_phase_archive, namespace="phase")
        self._bus.subscribe(self._on_phase_flow_completed, namespace="phase")
        self._bus.subscribe(self._on_phase_error, namespace="phase")

        self._bus.subscribe(self._on_worker_result, namespace="worker")
        self._bus.subscribe(self._on_worker_chunk, namespace="worker")
        self._bus.subscribe(self._on_worker_error, namespace="worker")
        self._bus.subscribe(self._on_worker_tool, namespace="worker")

    # ═══════════════════════════════════════════════════
    # 用户动作处理
    # ═══════════════════════════════════════════════════
    def _on_user_send(self, event: UserSendEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return

        # 持久化用户消息
        self._bus.emit(UIAppendUserEvent(session_id=event.session_id, text=event.user_text))

        # 构建上下文并入队
        context = self._build_context(event.session_id)
        enqueued = rt.queue_manager.enqueue(event.user_text, event.mode, context)

        if not enqueued:
            self._bus.emit(UIAppendSystemEvent(
                session_id=event.session_id,
                text="⚠️ 队列已满，请等待当前任务完成",
            ))
            return

    def _on_user_stop(self, event: UserStopEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return

        # 只取消 active 任务
        task = self._task_service.get_task_status(event.session_id)
        if task and not task.is_terminal:
            self._task_service.cancel_task(event.session_id)

        rt.queue_manager.cancel_current()
        rt.phase_manager.reset()

        self._bus.emit(UISetStreamingEvent(session_id=event.session_id, active=False))
        self._bus.emit(UIClearPhaseUIEvent(session_id=event.session_id))

    def _on_user_confirm(self, event: UserConfirmEvent):
        rt = self._require_runtime(event.session_id)
        if rt:
            rt.phase_manager.on_user_confirm(event.confirmed)
            if event.confirmed:
                rt.save_phase_state({"phase": "confirm", "confirmed": True})
            else:
                rt.clear_phase_state()

    def _on_user_reanalyze(self, event: UserReanalyzeEvent):
        rt = self._require_runtime(event.session_id)
        if rt:
            # PhaseCoordinator 层处理 reanalyze 逻辑
            pass

    def _on_user_skip_verify(self, event: UserSkipVerifyEvent):
        rt = self._require_runtime(event.session_id)
        if rt:
            rt.phase_manager.on_verify_complete(True, "用户跳过验证")

    # ═══════════════════════════════════════════════════
    # 会话生命周期处理
    # ═══════════════════════════════════════════════════
    def _on_session_create(self, event: SessionCreateEvent):
        self.create_runtime(
            session_id=event.session_id if hasattr(event, "session_id") else self._gen_session_id(),
            project_path=event.project_path,
            title=event.title,
            mode=event.mode,
            model=event.model,
        )

    def _on_session_switch(self, event: SessionSwitchEvent):
        self.switch_session(event.new_session_id)

    def _on_session_delete(self, event: SessionDeleteEvent):
        self.delete_runtime(event.session_id)

    def create_runtime(
        self,
        session_id: str,
        project_path: str,
        title: str,
        mode: str,
        model: str,
    ) -> SessionRuntime:
        rt = SessionRuntime(
            session_id=session_id,
            project_path=project_path,
            title=title,
            mode=mode,
            model=model,
            parent=self,
        )
        self._runtimes[session_id] = rt
        if self._current_session_id is None:
            self._current_session_id = session_id
        return rt

    def switch_session(self, new_session_id: str):
        old_session_id = self._current_session_id
        if old_session_id == new_session_id:
            return

        # 暂停旧会话（只断 UI 信号，不停止 Worker）
        if old_session_id and old_session_id in self._runtimes:
            old_rt = self._runtimes[old_session_id]
            # 旧会话任务仍活跃时，只取消 active 任务（不应覆盖 completed）
            task = self._task_service.get_task_status(old_session_id)
            if task and task.is_active:
                # 后台继续运行，不切掉 Worker
                pass

        self._current_session_id = new_session_id

        # 恢复新会话
        new_rt = self._runtimes.get(new_session_id)
        if new_rt and new_rt.phase_state:
            self._restore_phase_ui(new_rt)

    def delete_runtime(self, session_id: str):
        rt = self._runtimes.pop(session_id, None)
        if rt and rt.worker is not None:
            # 由 WorkerManager 停止 Worker
            pass
        if self._current_session_id == session_id:
            self._current_session_id = None

    def _restore_phase_ui(self, rt: SessionRuntime):
        state = rt.phase_state
        phase = state.get("phase")
        if phase == "confirm":
            task_list = state.get("task_list", [])
            self._bus.emit(UIShowConfirmationEvent(session_id=rt.session_id, task_list=task_list))

    # ═══════════════════════════════════════════════════
    # 队列事件处理
    # ═══════════════════════════════════════════════════
    def _on_queue_task_ready(self, event: QueueTaskReadyEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return

        task = rt.queue_manager.get_streaming_task()
        if task is None:
            return

        # 启动 TaskService 任务
        self._task_service.submit_task(task.session_id, task.mode, task.user_text)
        rt.bind_task(self._task_service.get_task_status(task.session_id))

        # 启动 Phase 工作流
        rt.phase_manager.start(task.user_text, task.mode, task.context)

    def _on_queue_task_stopped(self, event: QueueTaskStoppedEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        # 触发下一个任务
        streaming = rt.queue_manager.get_streaming_task()
        if streaming:
            self._bus.emit(QueueTaskReadyEvent(
                session_id=event.session_id,
                task_id=streaming.task_id,
            ))

    # ═══════════════════════════════════════════════════
    # Phase 事件处理
    # ═══════════════════════════════════════════════════
    def _on_phase_analyze(self, event: PhaseAnalyzeRequiredEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        # 创建/复用 Worker，由 WorkerManager 处理
        # 这里发射 worker.create 事件
        self._bus.emit(WorkerCreatedEvent(
            session_id=event.session_id,
            worker_id=event.session_id,
        ))

    def _on_phase_confirm(self, event: PhaseConfirmRequiredEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        rt.save_phase_state({"phase": "confirm", "task_list": event.task_list})
        self._task_service._on_phase_change(event.session_id, "confirm", "等待用户确认")
        self._bus.emit(UIShowConfirmationEvent(session_id=event.session_id, task_list=event.task_list))

    def _on_phase_execute(self, event: PhaseExecuteRequiredEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        self._task_service._on_phase_change(event.session_id, "executing", "执行中")
        # 请求 Worker 执行

    def _on_phase_verify(self, event: PhaseVerifyRequiredEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        self._task_service._on_phase_change(event.session_id, "verifying", "验证中")
        self._bus.emit(UIShowSkipVerifyEvent(session_id=event.session_id))

    def _on_phase_archive(self, event: PhaseArchiveRequiredEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        rt.phase_manager.on_archive_complete(True, "工作流完成")

    def _on_phase_flow_completed(self, event: PhaseFlowCompletedEvent):
        """唯一任务完成路径"""
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return

        # 1. 更新 TaskService 状态（只更新未终止任务）
        task = self._task_service.get_task_status(event.session_id)
        if task and not task.is_terminal:
            if event.success:
                self._task_service.complete_task(event.session_id, True)
            else:
                self._task_service.complete_task(event.session_id, False, event.message)

        # 2. 清除运行时 Task 引用
        rt.clear_task()
        rt.clear_phase_state()

        # 3. 通知队列出队
        rt.queue_manager.mark_current_done(event.session_id)

        # 4. UI 归零
        self._bus.emit(UISetStreamingEvent(session_id=event.session_id, active=False))
        self._bus.emit(UIClearPhaseUIEvent(session_id=event.session_id))
        self._bus.emit(UIHideConfirmationEvent(session_id=event.session_id))
        self._bus.emit(UIHideSkipVerifyEvent(session_id=event.session_id))

    def _on_phase_error(self, event: PhaseErrorEvent):
        """Phase 错误统一走完成路径"""
        self._bus.emit(PhaseFlowCompletedEvent(
            session_id=event.session_id,
            success=False,
            message=f"[{event.code}] {event.detail}",
        ))

    # ═══════════════════════════════════════════════════
    # Worker 事件处理
    # ═══════════════════════════════════════════════════
    def _on_worker_result(self, event: WorkerResultEvent):
        rt = self._require_runtime(event.session_id)
        if rt is None:
            return
        # 解析 task list 并推进 Phase
        task_list = PhaseManager.parse_task_list(event.full_text)
        rt.phase_manager.on_analyze_complete(task_list)

    def _on_worker_chunk(self, event: WorkerChunkEvent):
        # 仅当前会话更新 UI
        if event.session_id == self._current_session_id:
            from core.events import UIStreamChunkEvent
            self._bus.emit(UIStreamChunkEvent(session_id=event.session_id, chunk=event.chunk))

    def _on_worker_error(self, event: WorkerErrorEvent):
        self._bus.emit(PhaseFlowCompletedEvent(
            session_id=event.session_id,
            success=False,
            message=f"[{event.code}] {event.detail}",
        ))

    def _on_worker_tool(self, event: WorkerToolExecutedEvent):
        # 工具执行事件，可用于日志/活动面板
        pass

    # ═══════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════
    def _require_runtime(self, session_id: str) -> Optional[SessionRuntime]:
        rt = self._runtimes.get(session_id)
        if rt is None:
            print(f"[ORCH] runtime not found: {session_id}", flush=True)
        return rt

    def _build_context(self, session_id: str) -> str:
        """构建 prompt 上下文。"""
        try:
            ctx = self._app_ctx.context_service
            return ctx.build_prompt_context()
        except Exception as e:
            print(f"[ORCH] build_context error: {e}", flush=True)
            return ""

    def _gen_session_id(self) -> str:
        from uuid import uuid4
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
