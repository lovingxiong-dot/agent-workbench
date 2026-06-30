"""
events.py — v4 事件总线协议

所有事件携带 session_id，便于路由和过滤。
事件命名约定：namespace.name（小写）
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class Event:
    """事件基类"""
    namespace: str = ""
    name: str = ""
    session_id: str = ""

    def event_type(self) -> str:
        return f"{self.namespace}.{self.name}"


# ═══════════════════════════════════════════════════
# 用户动作 user.*
# ═══════════════════════════════════════════════════
@dataclass
class UserSendEvent(Event):
    namespace: str = "user"
    name: str = "send"
    user_text: str = ""
    mode: str = "ask"
    session_type: str = "chat"
    project_path: str = ""


@dataclass
class UserStopEvent(Event):
    namespace: str = "user"
    name: str = "stop"


@dataclass
class UserConfirmEvent(Event):
    namespace: str = "user"
    name: str = "confirm"
    confirmed: bool = True


@dataclass
class UserReanalyzeEvent(Event):
    namespace: str = "user"
    name: str = "reanalyze"


@dataclass
class UserSkipVerifyEvent(Event):
    namespace: str = "user"
    name: str = "skip_verify"


# ═══════════════════════════════════════════════════
# 会话生命周期 session.*
# ═══════════════════════════════════════════════════
@dataclass
class SessionCreateEvent(Event):
    namespace: str = "session"
    name: str = "create"
    title: str = "新对话"
    session_type: str = "chat"  # chat / work
    project_path: str = ""
    mode: str = "ask"
    model: str = ""


@dataclass
class SessionSwitchEvent(Event):
    namespace: str = "session"
    name: str = "switch"
    new_session_id: str = ""


@dataclass
class SessionDeleteEvent(Event):
    namespace: str = "session"
    name: str = "delete"


@dataclass
class SessionPinEvent(Event):
    namespace: str = "session"
    name: str = "pin"
    pinned: bool = True


@dataclass
class SessionRenameEvent(Event):
    namespace: str = "session"
    name: str = "rename"
    new_title: str = ""


# ═══════════════════════════════════════════════════
# 队列 queue.*
# ═══════════════════════════════════════════════════
@dataclass
class QueueEnqueueEvent(Event):
    namespace: str = "queue"
    name: str = "enqueue"
    user_text: str = ""
    mode: str = ""
    context: str = ""


@dataclass
class QueueTaskReadyEvent(Event):
    namespace: str = "queue"
    name: str = "task_ready"
    task_id: str = ""


@dataclass
class QueueTaskCompleteEvent(Event):
    namespace: str = "queue"
    name: str = "task_complete"
    task_id: str = ""
    success: bool = True


@dataclass
class QueueSlotFullEvent(Event):
    namespace: str = "queue"
    name: str = "slot_full"


@dataclass
class QueueSlotAvailableEvent(Event):
    namespace: str = "queue"
    name: str = "slot_available"


# ═══════════════════════════════════════════════════
# Phase 阶段 phase.*
# ═══════════════════════════════════════════════════
@dataclass
class PhaseChangedEvent(Event):
    namespace: str = "phase"
    name: str = "changed"
    phase: str = ""
    task_count: int = 0


@dataclass
class PhaseAnalyzeRequiredEvent(Event):
    namespace: str = "phase"
    name: str = "analyze_required"
    user_text: str = ""
    context: str = ""


@dataclass
class PhaseConfirmRequiredEvent(Event):
    namespace: str = "phase"
    name: str = "confirm_required"
    task_list: List[Any] = field(default_factory=list)


@dataclass
class PhaseExecuteRequiredEvent(Event):
    namespace: str = "phase"
    name: str = "execute_required"
    task_list: List[Any] = field(default_factory=list)
    original_text: str = ""


@dataclass
class PhaseVerifyRequiredEvent(Event):
    namespace: str = "phase"
    name: str = "verify_required"
    execution_results: List[dict] = field(default_factory=list)


@dataclass
class PhaseArchiveRequiredEvent(Event):
    namespace: str = "phase"
    name: str = "archive_required"


@dataclass
class PhaseCompleteEvent(Event):
    namespace: str = "phase"
    name: str = "complete"
    success: bool = True
    message: str = ""


@dataclass
class PhaseErrorEvent(Event):
    namespace: str = "phase"
    name: str = "error"
    code: str = ""
    detail: str = ""


# 旧名称兼容别名（orchestrator.py 等仍可能引用）
PhaseAnalyzeEvent = PhaseAnalyzeRequiredEvent
PhaseConfirmEvent = PhaseConfirmRequiredEvent
PhaseExecuteEvent = PhaseExecuteRequiredEvent
PhaseVerifyEvent = PhaseVerifyRequiredEvent
PhaseArchiveEvent = PhaseArchiveRequiredEvent


# ═══════════════════════════════════════════════════
# Worker 生命周期 worker.*
# ═══════════════════════════════════════════════════
@dataclass
class WorkerCreateEvent(Event):
    namespace: str = "worker"
    name: str = "create"
    worker_id: str = ""
    mode: str = ""
    model: str = ""
    project_root: str = ""


@dataclass
class WorkerCreatedEvent(Event):
    namespace: str = "worker"
    name: str = "created"
    worker_id: str = ""


@dataclass
class WorkerDestroyEvent(Event):
    namespace: str = "worker"
    name: str = "destroy"
    worker_id: str = ""


@dataclass
class WorkerDestroyedEvent(Event):
    namespace: str = "worker"
    name: str = "destroyed"
    worker_id: str = ""


@dataclass
class WorkerChunkEvent(Event):
    namespace: str = "worker"
    name: str = "chunk"
    worker_id: str = ""
    chunk: str = ""


@dataclass
class WorkerResultEvent(Event):
    namespace: str = "worker"
    name: str = "result"
    worker_id: str = ""
    full_text: str = ""


@dataclass
class WorkerErrorEvent(Event):
    namespace: str = "worker"
    name: str = "error"
    worker_id: str = ""
    code: str = ""
    detail: str = ""


@dataclass
class WorkerToolEvent(Event):
    namespace: str = "worker"
    name: str = "tool"
    worker_id: str = ""
    tool_name: str = ""
    args: dict = field(default_factory=dict)
    result: str = ""


# ═══════════════════════════════════════════════════
# UI 渲染指令 ui.*
# ═══════════════════════════════════════════════════
@dataclass
class UIAppendUserEvent(Event):
    namespace: str = "ui"
    name: str = "append_user"
    text: str = ""


@dataclass
class UIAppendAIEvent(Event):
    namespace: str = "ui"
    name: str = "append_ai"
    text: str = ""


@dataclass
class UIAppendSystemEvent(Event):
    namespace: str = "ui"
    name: str = "append_system"
    text: str = ""


@dataclass
class UIStreamChunkEvent(Event):
    namespace: str = "ui"
    name: str = "stream_chunk"
    chunk: str = ""


@dataclass
class UIFinalizeStreamEvent(Event):
    namespace: str = "ui"
    name: str = "finalize_stream"


@dataclass
class UISetStreamingEvent(Event):
    namespace: str = "ui"
    name: str = "set_streaming"
    active: bool = False


@dataclass
class UISetPhaseEvent(Event):
    namespace: str = "ui"
    name: str = "set_phase"
    phase: str = ""
    task_count: int = 0


@dataclass
class UIClearPhaseEvent(Event):
    namespace: str = "ui"
    name: str = "clear_phase"


@dataclass
class UIClearChatEvent(Event):
    namespace: str = "ui"
    name: str = "clear_chat"


@dataclass
class UIShowConfirmationEvent(Event):
    namespace: str = "ui"
    name: str = "show_confirmation"
    task_list: List[Any] = field(default_factory=list)


@dataclass
class UIHideConfirmationEvent(Event):
    namespace: str = "ui"
    name: str = "hide_confirmation"


@dataclass
class UIShowConfirmEvent(Event):
    namespace: str = "ui"
    name: str = "show_confirm"
    task_list: List[Any] = field(default_factory=list)


@dataclass
class UIHideConfirmEvent(Event):
    namespace: str = "ui"
    name: str = "hide_confirm"


@dataclass
class UISetSendEnabledEvent(Event):
    namespace: str = "ui"
    name: str = "set_send_enabled"
    enabled: bool = True


@dataclass
class UIUpdateQueueBarEvent(Event):
    namespace: str = "ui"
    name: str = "update_queue_bar"
    bar_text: str = ""
    visible: bool = False


@dataclass
class UIUpdateSessionListEvent(Event):
    namespace: str = "ui"
    name: str = "update_session_list"
    sessions: List[Any] = field(default_factory=list)


@dataclass
class UIUpdateSessionBadgeEvent(Event):
    namespace: str = "ui"
    name: str = "update_session_badge"
    session_id: str = ""
    phase: str = ""


@dataclass
class UIFocusInputEvent(Event):
    namespace: str = "ui"
    name: str = "focus_input"


@dataclass
class UISetActiveSessionEvent(Event):
    namespace: str = "ui"
    name: str = "set_active_session"
    active_session_id: str = ""
