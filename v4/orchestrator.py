"""
orchestrator.py — v4 会话协调器（SessionOrchestrator）

职责：
- 作为 v4 单轨架构的核心协调器，持有所有 SessionRuntime。
- 订阅 MessageBus 上的 user、session、queue、phase、worker 命名空间事件。
- 所有消息必须先写入 DB，再转发 ui.* 事件。
- 会话切换时只切换 UI 指针，从 DB 加载消息，不操作 Worker。
- 不直接创建/停止 Worker，仅通过 worker.create / worker.destroy 事件委托 WorkerManager。
"""
from typing import Dict, Optional, List

from PySide6.QtCore import QObject

from .models import SessionMetadata, Message, TaskPhase, TaskState
from .repository import SessionRepository
from .runtime import SessionRuntime
from .event_bus import MessageBus
from .events import (
    UserSendEvent, UserStopEvent, UserConfirmEvent,
    SessionCreateEvent, SessionSwitchEvent, SessionDeleteEvent,
    SessionPinEvent, SessionRenameEvent,
    QueueTaskReadyEvent, QueueTaskCompleteEvent,
    PhaseChangedEvent, PhaseConfirmRequiredEvent, PhaseCompleteEvent, PhaseErrorEvent,
    WorkerCreateEvent, WorkerCreatedEvent, WorkerDestroyEvent,
    WorkerChunkEvent, WorkerResultEvent, WorkerErrorEvent,
    UIAppendUserEvent, UIAppendAIEvent, UIAppendSystemEvent,
    UIStreamChunkEvent, UIFinalizeStreamEvent,
    UISetPhaseEvent, UIClearPhaseEvent, UIShowConfirmEvent, UIHideConfirmEvent,
    UIClearChatEvent,
    UISetSendEnabledEvent, UIUpdateQueueBarEvent,
    UIUpdateSessionListEvent, UIUpdateSessionBadgeEvent,
    UIFocusInputEvent, UISetActiveSessionEvent,
)


class SessionOrchestrator(QObject):
    """v4 会话协调器"""

    def __init__(self, repository: SessionRepository, message_bus: MessageBus, worker_manager=None, parent=None):
        super().__init__(parent)
        self._repo = repository
        self._bus = message_bus
        self._worker_mgr = worker_manager
        self._runtimes: Dict[str, SessionRuntime] = {}
        self._current_session_id: Optional[str] = None

        self._subscribe_events()

    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id

    def has_runtime(self, session_id: str) -> bool:
        return session_id in self._runtimes

    def get_runtime(self, session_id: str) -> Optional[SessionRuntime]:
        return self._runtimes.get(session_id)

    def list_runtimes(self) -> List[SessionRuntime]:
        return list(self._runtimes.values())

    # ═══════════════════════════════════════════════════
    # 事件订阅
    # ═══════════════════════════════════════════════════
    def _subscribe_events(self):
        # user
        self._bus.subscribe_name("user", "send", self._on_user_send)
        self._bus.subscribe_name("user", "stop", self._on_user_stop)
        self._bus.subscribe_name("user", "confirm", self._on_user_confirm)

        # session
        self._bus.subscribe_name("session", "create", self._on_session_create)
        self._bus.subscribe_name("session", "switch", self._on_session_switch)
        self._bus.subscribe_name("session", "delete", self._on_session_delete)
        self._bus.subscribe_name("session", "pin", self._on_session_pin)
        self._bus.subscribe_name("session", "rename", self._on_session_rename)

        # queue
        self._bus.subscribe_name("queue", "task_ready", self._on_queue_task_ready)
        self._bus.subscribe_name("queue", "task_complete", self._on_queue_task_complete)

        # phase
        self._bus.subscribe_name("phase", "changed", self._on_phase_changed)
        self._bus.subscribe_name("phase", "confirm_required", self._on_phase_confirm_required)
        self._bus.subscribe_name("phase", "complete", self._on_phase_complete)
        self._bus.subscribe_name("phase", "error", self._on_phase_error)

        # worker
        self._bus.subscribe_name("worker", "created", self._on_worker_created)
        self._bus.subscribe_name("worker", "chunk", self._on_worker_chunk)
        self._bus.subscribe_name("worker", "result", self._on_worker_result)
        self._bus.subscribe_name("worker", "error", self._on_worker_error)

    # ═══════════════════════════════════════════════════
    # user.* 处理
    # ═══════════════════════════════════════════════════
    def _on_user_send(self, event: UserSendEvent):
        """用户发送消息：若当前无会话（草稿窗口），先创建会话；再写 DB，再发 UI；随后入队。"""
        # 草稿窗口首条消息：创建会话并切换
        if not self._current_session_id:
            model = event.model or "tool-agent"
            self._create_session_from_draft(
                session_type=event.session_type,
                project_path=event.project_path,
                mode=event.mode,
                model=model,
            )

        rt = self._require_runtime(self._current_session_id)
        if not rt:
            return

        # 1. 持久化用户消息（唯一权威来源）
        msg = Message.new(self._current_session_id, "user", event.user_text)
        self._repo.add_message(msg)

        # 2. 通知 UI（仅当前会话）
        self._bus.emit(UIAppendUserEvent(session_id=self._current_session_id, text=event.user_text))

        # 3. 入队
        context = self._build_context(self._current_session_id)
        task = rt.queue.enqueue(event.user_text, event.mode, context)

        if not task:
            self._bus.emit(UIAppendSystemEvent(
                session_id=self._current_session_id,
                text="⚠️ 队列已满",
            ))
            return

        # 4. 刷新会话列表（消息时间已更新）
        self._refresh_session_list()

    def _on_user_stop(self, event: UserStopEvent):
        """用户停止：取消本会话队列任务，并通知 WorkerManager 销毁 Worker。"""
        rt = self._require_runtime(event.session_id)
        if not rt:
            return

        rt.queue.cancel_current()
        self._repo.update_task_state(TaskState(
            session_id=event.session_id,
            phase=TaskPhase.CANCELLED,
        ))

        # 同步终止 Worker，避免其继续产生 phase 事件覆盖已取消状态
        self._bus.emit(WorkerDestroyEvent(
            session_id=event.session_id,
            worker_id="",
        ))

        if event.session_id == self._current_session_id:
            self._bus.emit(UIClearPhaseEvent(session_id=event.session_id))

        self._refresh_session_badge(event.session_id)

    def _on_user_confirm(self, event: UserConfirmEvent):
        """用户确认/取消 Phase 任务清单：转发给 WorkerManager。"""
        if self._worker_mgr:
            self._worker_mgr.confirm(event.session_id, event.confirmed)

    # ═══════════════════════════════════════════════════
    # session.* 处理
    # ═══════════════════════════════════════════════════
    def _on_session_create(self, event: SessionCreateEvent):
        """创建新会话并自动切换。"""
        metadata = SessionMetadata.new(
            title=event.title,
            session_type=event.session_type,
            mode=event.mode,
            model=event.model,
            project_path=event.project_path,
        )
        self._repo.create_session(metadata)

        rt = SessionRuntime(metadata, parent=self)
        self._runtimes[metadata.session_id] = rt
        self._connect_queue_signals(rt)

        self._switch_session(metadata.session_id)
        self._refresh_session_list()
        self._bus.emit(UIFocusInputEvent(session_id=metadata.session_id))

    def _on_session_switch(self, event: SessionSwitchEvent):
        """切换会话：只切 UI，不中断 Worker。"""
        self._require_runtime(event.new_session_id)
        self._switch_session(event.new_session_id)

    def _on_session_delete(self, event: SessionDeleteEvent):
        """删除会话：清理运行时与 DB。"""
        rt = self._runtimes.pop(event.session_id, None)
        if rt:
            rt.queue.cancel_current()

        self._repo.delete_session(event.session_id)

        if self._current_session_id == event.session_id:
            sessions = self._repo.list_sessions()
            if sessions:
                sid = sessions[0].session_id
                self._require_runtime(sid)
                self._switch_session(sid)
            else:
                self._current_session_id = None
                self._bus.emit(UIClearChatEvent(session_id=""))
                self._bus.emit(UIFocusInputEvent(session_id=""))

        self._refresh_session_list()

    def _on_session_pin(self, event: SessionPinEvent):
        """置顶/取消置顶会话。"""
        self._repo.update_session(event.session_id, pinned=event.pinned, update_timestamp=False)
        self._refresh_session_list()

    def _on_session_rename(self, event: SessionRenameEvent):
        """重命名会话。"""
        self._repo.update_session(event.session_id, title=event.new_title)
        self._refresh_session_list()

    def _switch_session(self, new_session_id: str):
        """核心切换逻辑：从 DB 加载消息并恢复 UI。

        调用方必须保证 new_session_id 对应的 runtime 已存在；
        若不存在，说明目标会话已被删除或尚未创建，直接返回避免 UI 指向无效 runtime。
        """
        rt = self._runtimes.get(new_session_id)
        if not rt:
            return

        if self._current_session_id == new_session_id:
            return

        self._current_session_id = new_session_id

        # 先刷新会话列表，确保列表项存在后再设置当前选中项
        self._refresh_session_list()

        # 通知 UI 切换当前会话选中项
        self._bus.emit(UISetActiveSessionEvent(session_id=new_session_id, active_session_id=new_session_id))

        # 清空当前会话聊天视图，随后从 DB 重新加载
        self._bus.emit(UIClearChatEvent(session_id=new_session_id))

        msgs = self._repo.get_messages(new_session_id)
        task_state = self._repo.get_task_state(new_session_id)
        rt = self._runtimes.get(new_session_id)

        # 加载消息（权威来源：DB）
        for msg in msgs:
            if msg.role == "user":
                self._bus.emit(UIAppendUserEvent(session_id=new_session_id, text=msg.content))
            elif msg.role == "ai":
                self._bus.emit(UIAppendAIEvent(session_id=new_session_id, text=msg.content))
            else:
                self._bus.emit(UIAppendSystemEvent(session_id=new_session_id, text=msg.content))

        # 恢复 Phase UI
        if task_state.phase in (TaskPhase.CONFIRMING, TaskPhase.EXECUTING):
            self._bus.emit(UISetPhaseEvent(
                session_id=new_session_id,
                phase=task_state.phase.value,
                task_count=task_state.task_count,
            ))

        # 同步队列状态
        if rt:
            self._bus.emit(UISetSendEnabledEvent(
                session_id=new_session_id,
                enabled=not rt.queue.is_full,
            ))

        self._bus.emit(UIFocusInputEvent(session_id=new_session_id))

    # ═══════════════════════════════════════════════════
    # queue.* 处理
    # ═══════════════════════════════════════════════════
    def _on_queue_task_ready(self, event: QueueTaskReadyEvent):
        """队列任务就绪：请求 WorkerManager 创建 Worker。"""
        rt = self._require_runtime(event.session_id)
        if not rt:
            return

        task = rt.queue.get_streaming_task()
        user_text = task.user_text if task else ""
        env = rt.environment
        self._bus.emit(WorkerCreateEvent(
            session_id=event.session_id,
            worker_id="",
            mode=rt.metadata.mode,
            model=rt.metadata.model,
            project_root=env.project_root,
            user_text=user_text,
        ))

        self._repo.update_task_state(TaskState(
            session_id=event.session_id,
            phase=TaskPhase.ANALYZING,
        ))
        self._refresh_session_badge(event.session_id)

    def _on_queue_task_complete(self, event: QueueTaskCompleteEvent):
        """队列任务完成：更新任务状态，释放 Worker。"""
        phase = TaskPhase.COMPLETED if event.success else TaskPhase.FAILED
        self._repo.update_task_state(TaskState(
            session_id=event.session_id,
            phase=phase,
        ))

        self._bus.emit(WorkerDestroyEvent(
            session_id=event.session_id,
            worker_id="",
        ))

        if event.session_id == self._current_session_id:
            self._bus.emit(UIClearPhaseEvent(session_id=event.session_id))

        self._refresh_session_badge(event.session_id)
        self._refresh_session_list()

    # ═══════════════════════════════════════════════════
    # phase.* 处理
    # ═══════════════════════════════════════════════════
    def _on_phase_complete(self, event: PhaseCompleteEvent):
        """Phase 完成：标记队列任务完成、清理状态。"""
        rt = self._runtimes.get(event.session_id)
        if rt:
            streaming = rt.queue.get_streaming_task()
            if streaming:
                rt.queue.mark_done(streaming.task_id)
            rt.clear_phase_state()

        if event.session_id == self._current_session_id:
            if not event.success:
                self._bus.emit(UIAppendSystemEvent(
                    session_id=event.session_id,
                    text=f"⚠️ {event.message}",
                ))
            self._bus.emit(UIClearPhaseEvent(session_id=event.session_id))

        phase = TaskPhase.COMPLETED if event.success else TaskPhase.FAILED
        self._repo.update_task_state(TaskState(
            session_id=event.session_id,
            phase=phase,
        ))
        self._refresh_session_badge(event.session_id)

    def _on_phase_error(self, event: PhaseErrorEvent):
        """Phase 错误：统一走完成失败路径。"""
        self._on_phase_complete(PhaseCompleteEvent(
            session_id=event.session_id,
            success=False,
            message=f"[{event.code}] {event.detail}",
        ))

    def _on_phase_changed(self, event: PhaseChangedEvent):
        """Phase 切换：更新任务状态并通知 UI。"""
        rt = self._runtimes.get(event.session_id)
        if rt:
            rt.save_phase_state({"phase": event.phase, "task_count": event.task_count})

        phase_map = {
            "analyze": TaskPhase.ANALYZING,
            "confirm": TaskPhase.CONFIRMING,
            "execute": TaskPhase.EXECUTING,
            "verify": TaskPhase.VERIFYING,
            "archive": TaskPhase.COMPLETED,
        }
        db_phase = phase_map.get(event.phase, TaskPhase.ANALYZING)
        self._repo.update_task_state(TaskState(
            session_id=event.session_id,
            phase=db_phase,
        ))

        if event.session_id == self._current_session_id:
            self._bus.emit(UISetPhaseEvent(
                session_id=event.session_id,
                phase=event.phase,
                task_count=event.task_count,
            ))
        self._refresh_session_badge(event.session_id)

    def _on_phase_confirm_required(self, event: PhaseConfirmRequiredEvent):
        """需要用户确认任务清单：通知 UI 显示确认面板。"""
        if event.session_id == self._current_session_id:
            self._bus.emit(UIShowConfirmEvent(
                session_id=event.session_id,
                task_list=event.task_list,
            ))

    # ═══════════════════════════════════════════════════
    # worker.* 处理
    # ═══════════════════════════════════════════════════
    def _on_worker_created(self, event: WorkerCreatedEvent):
        """Worker 创建成功：绑定到对应 SessionRuntime。"""
        if not self._worker_mgr:
            return
        worker = self._worker_mgr.get_worker(event.session_id)
        rt = self._runtimes.get(event.session_id)
        if rt and worker:
            rt.attach_worker(worker)

    def _on_worker_chunk(self, event: WorkerChunkEvent):
        """Worker 流式 chunk：只转发当前会话。"""
        rt = self._runtimes.get(event.session_id)
        if rt:
            rt._chunks_received = True

        if event.session_id == self._current_session_id:
            self._bus.emit(UIStreamChunkEvent(
                session_id=event.session_id,
                chunk=event.chunk,
            ))

    def _on_worker_result(self, event: WorkerResultEvent):
        """Worker 结果：持久化 AI 消息，更新 UI。"""
        rt = self._runtimes.get(event.session_id)
        if not rt:
            return

        text = event.full_text or ""
        if text.strip():
            msg = Message.new(event.session_id, "ai", text)
            self._repo.add_message(msg)

        if event.session_id == self._current_session_id:
            self._bus.emit(UIFinalizeStreamEvent(session_id=event.session_id))
            if not rt._chunks_received and text.strip():
                self._bus.emit(UIAppendAIEvent(session_id=event.session_id, text=text))

        rt._chunks_received = False
        self._refresh_session_list()

    def _on_worker_error(self, event: WorkerErrorEvent):
        """Worker 错误：统一走 Phase 完成失败路径。"""
        self._on_phase_complete(PhaseCompleteEvent(
            session_id=event.session_id,
            success=False,
            message=f"[{event.code}] {event.detail}",
        ))

    # ═══════════════════════════════════════════════════
    # 内部工具方法
    # ═══════════════════════════════════════════════════
    def _create_session_from_draft(self, session_type: str, project_path: str, mode: str, model: str):
        """从草稿窗口创建会话：写入 DB、创建 runtime、切换当前会话、刷新列表并设置选中项。"""
        metadata = SessionMetadata.new(
            title="新对话",
            session_type=session_type,
            mode=mode,
            model=model,
            project_path=project_path,
        )
        self._repo.create_session(metadata)

        rt = SessionRuntime(metadata, parent=self)
        self._runtimes[metadata.session_id] = rt
        self._connect_queue_signals(rt)

        self._current_session_id = metadata.session_id
        self._refresh_session_list()
        self._bus.emit(UISetActiveSessionEvent(
            session_id=metadata.session_id,
            active_session_id=metadata.session_id,
        ))

    def clear_current(self):
        """清空当前会话指针，进入草稿窗口状态。"""
        self._current_session_id = None
        self._bus.emit(UIClearChatEvent(session_id=""))
        self._bus.emit(UIFocusInputEvent(session_id=""))

    def _require_runtime(self, session_id: str) -> Optional[SessionRuntime]:
        """获取运行时；若不存在则从 DB 恢复。"""
        rt = self._runtimes.get(session_id)
        if rt is None:
            metadata = self._repo.get_session(session_id)
            if metadata:
                rt = SessionRuntime(metadata, parent=self)
                self._runtimes[session_id] = rt
                self._connect_queue_signals(rt)
        return rt

    def _build_context(self, session_id: str) -> str:
        """构建 prompt 上下文。"""
        rt = self._runtimes.get(session_id)
        if not rt:
            return ""

        env = rt.environment
        parts = []
        if env.project_root:
            parts.append(f"当前项目目录: {env.project_root}")
        if env.tools:
            parts.append(f"可用工具: {', '.join(env.tools)}")

        return "\n".join(parts)

    def _connect_queue_signals(self, rt: SessionRuntime):
        """将会话队列信号桥接到 MessageBus 事件。"""
        qm = rt.queue
        qm.task_ready.connect(
            lambda task: self._bus.emit(QueueTaskReadyEvent(
                session_id=rt.session_id,
                task_id=task.task_id,
            ))
        )
        qm.task_complete.connect(
            lambda task_id: self._bus.emit(QueueTaskCompleteEvent(
                session_id=rt.session_id,
                task_id=task_id,
                success=True,
            ))
        )
        qm.send_enabled_changed.connect(
            lambda enabled: self._bus.emit(UISetSendEnabledEvent(
                session_id=rt.session_id,
                enabled=enabled,
            ))
        )
        qm.queue_bar_text_changed.connect(
            lambda text: self._bus.emit(UIUpdateQueueBarEvent(
                session_id=rt.session_id,
                bar_text=text,
                visible=bool(text),
            ))
        )

    def _refresh_session_list(self):
        """刷新会话列表。"""
        sessions = self._repo.list_sessions()
        self._bus.emit(UIUpdateSessionListEvent(
            session_id=self._current_session_id or "",
            sessions=sessions,
        ))

    def _refresh_session_badge(self, session_id: str):
        """刷新会话状态徽章。"""
        state = self._repo.get_task_state(session_id)
        self._bus.emit(UIUpdateSessionBadgeEvent(
            session_id=session_id,
            phase=state.phase.value,
        ))
