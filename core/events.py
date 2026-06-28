"""
events.py — v3 事件总线协议

所有跨组件通信的强类型事件定义。
事件按 namespace 分类，便于过滤和订阅。
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from datetime import datetime


class Event:
    """事件基类"""
    namespace: str = ""
    name: str = ""

    def event_type(self) -> str:
        return f"{self.namespace}.{self.name}"


# ═══════════════════════════════════════════════════
# 用户动作 user.*
# ═══════════════════════════════════════════════════
@dataclass
class UserSendEvent(Event):
    namespace = "user"
    name = "send"
    session_id: str
    user_text: str
    mode: str


@dataclass
class UserStopEvent(Event):
    namespace = "user"
    name = "stop"
    session_id: str


@dataclass
class UserConfirmEvent(Event):
    namespace = "user"
    name = "confirm"
    session_id: str
    confirmed: bool = True


@dataclass
class UserReanalyzeEvent(Event):
    namespace = "user"
    name = "reanalyze"
    session_id: str


@dataclass
class UserSkipVerifyEvent(Event):
    namespace = "user"
    name = "skip_verify"
    session_id: str


# ═══════════════════════════════════════════════════
# 会话生命周期 session.*
# ═══════════════════════════════════════════════════
@dataclass
class SessionCreateEvent(Event):
    namespace = "session"
    name = "create"
    project_path: str
    mode: str
    model: str
    title: str = "新对话"


@dataclass
class SessionSwitchEvent(Event):
    namespace = "session"
    name = "switch"
    old_session_id: str
    new_session_id: str


@dataclass
class SessionSwitchedEvent(Event):
    namespace = "session"
    name = "switched"
    old_session_id: str
    new_session_id: str


@dataclass
class SessionDeleteEvent(Event):
    namespace = "session"
    name = "delete"
    session_id: str


@dataclass
class SessionTitleUpdatedEvent(Event):
    namespace = "session"
    name = "title_updated"
    session_id: str
    title: str


# ═══════════════════════════════════════════════════
# 队列 queue.*
# ═══════════════════════════════════════════════════
@dataclass
class QueueEnqueueEvent(Event):
    namespace = "queue"
    name = "enqueue"
    session_id: str
    user_text: str
    mode: str
    context: str


@dataclass
class QueueStateChangedEvent(Event):
    namespace = "queue"
    name = "state_changed"
    session_id: str
    state_name: str          # IDLE / STREAMING / QUEUED_1
    is_full: bool
    send_enabled: bool
    bar_text: str


@dataclass
class QueueTaskReadyEvent(Event):
    namespace = "queue"
    name = "task_ready"
    session_id: str
    task_id: str


@dataclass
class QueueTaskStoppedEvent(Event):
    namespace = "queue"
    name = "task_stopped"
    session_id: str
    task_id: str


# ═══════════════════════════════════════════════════
# Phase 阶段 phase.*
# ═══════════════════════════════════════════════════
@dataclass
class PhaseChangedEvent(Event):
    namespace = "phase"
    name = "changed"
    session_id: str
    phase: str
    mode: str
    task_count: int = 0


@dataclass
class PhaseAnalyzeRequiredEvent(Event):
    namespace = "phase"
    name = "analyze_required"
    session_id: str
    user_text: str
    mode: str
    context: str


@dataclass
class PhaseConfirmRequiredEvent(Event):
    namespace = "phase"
    name = "confirm_required"
    session_id: str
    task_list: List[Any] = field(default_factory=list)


@dataclass
class PhaseExecuteRequiredEvent(Event):
    namespace = "phase"
    name = "execute_required"
    session_id: str
    task_list: List[Any] = field(default_factory=list)


@dataclass
class PhaseVerifyRequiredEvent(Event):
    namespace = "phase"
    name = "verify_required"
    session_id: str
    execution_results: List[dict] = field(default_factory=list)
    mode: str = "ask"


@dataclass
class PhaseArchiveRequiredEvent(Event):
    namespace = "phase"
    name = "archive_required"
    session_id: str
    mode: str = "ask"


@dataclass
class PhaseFlowCompletedEvent(Event):
    namespace = "phase"
    name = "flow_completed"
    session_id: str
    success: bool
    message: str = ""


@dataclass
class PhaseErrorEvent(Event):
    namespace = "phase"
    name = "error"
    session_id: str
    code: str
    detail: str


# ═══════════════════════════════════════════════════
# Worker 生命周期与输出 worker.*
# ═══════════════════════════════════════════════════
@dataclass
class WorkerCreatedEvent(Event):
    namespace = "worker"
    name = "created"
    session_id: str
    worker_id: str


@dataclass
class WorkerStoppedEvent(Event):
    namespace = "worker"
    name = "stopped"
    session_id: str
    worker_id: str


@dataclass
class WorkerResultEvent(Event):
    namespace = "worker"
    name = "result"
    session_id: str
    full_text: str


@dataclass
class WorkerChunkEvent(Event):
    namespace = "worker"
    name = "chunk"
    session_id: str
    chunk: str


@dataclass
class WorkerErrorEvent(Event):
    namespace = "worker"
    name = "error"
    session_id: str
    code: str
    detail: str


@dataclass
class WorkerToolExecutedEvent(Event):
    namespace = "worker"
    name = "tool_executed"
    session_id: str
    tool_name: str
    args: dict = field(default_factory=dict)
    result: str = ""
    elapsed_ms: int = 0


# ═══════════════════════════════════════════════════
# 任务状态 task.*（由 TaskService 权威发出）
# ═══════════════════════════════════════════════════
@dataclass
class TaskStatusChangedEvent(Event):
    namespace = "task"
    name = "status_changed"
    session_id: str
    status: str


@dataclass
class TaskCompletedEvent(Event):
    namespace = "task"
    name = "completed"
    session_id: str
    success: bool
    error: str = ""


@dataclass
class TaskProgressEvent(Event):
    namespace = "task"
    name = "progress"
    session_id: str
    phase: str
    detail: str = ""


# ═══════════════════════════════════════════════════
# UI 渲染指令 ui.*
# ═══════════════════════════════════════════════════
@dataclass
class UIAppendUserEvent(Event):
    namespace = "ui"
    name = "append_user"
    session_id: str
    text: str


@dataclass
class UIAppendAIEvent(Event):
    namespace = "ui"
    name = "append_ai"
    session_id: str
    text: str


@dataclass
class UIAppendSystemEvent(Event):
    namespace = "ui"
    name = "append_system"
    session_id: str
    text: str


@dataclass
class UIStreamChunkEvent(Event):
    namespace = "ui"
    name = "stream_chunk"
    session_id: str
    chunk: str


@dataclass
class UIFinalizeStreamEvent(Event):
    namespace = "ui"
    name = "finalize_stream"
    session_id: str


@dataclass
class UISetStreamingEvent(Event):
    namespace = "ui"
    name = "set_streaming"
    session_id: str
    active: bool


@dataclass
class UISetPhaseIndicatorEvent(Event):
    namespace = "ui"
    name = "set_phase_indicator"
    session_id: str
    phase: str
    task_count: int = 0


@dataclass
class UIClearPhaseUIEvent(Event):
    namespace = "ui"
    name = "clear_phase_ui"
    session_id: str


@dataclass
class UIShowConfirmationEvent(Event):
    namespace = "ui"
    name = "show_confirmation"
    session_id: str
    task_list: List[Any] = field(default_factory=list)


@dataclass
class UIHideConfirmationEvent(Event):
    namespace = "ui"
    name = "hide_confirmation"
    session_id: str


@dataclass
class UIShowSkipVerifyEvent(Event):
    namespace = "ui"
    name = "show_skip_verify"
    session_id: str


@dataclass
class UIHideSkipVerifyEvent(Event):
    namespace = "ui"
    name = "hide_skip_verify"
    session_id: str


@dataclass
class UIUpdateStatusBarEvent(Event):
    namespace = "ui"
    name = "update_status_bar"
    session_id: str
    capacity_text: str = ""


@dataclass
class UISetSendEnabledEvent(Event):
    namespace = "ui"
    name = "set_send_enabled"
    session_id: str
    enabled: bool


@dataclass
class UIUpdateSessionStatusEvent(Event):
    namespace = "ui"
    name = "update_session_status"
    session_id: str
    status: str      # pending / streaming / completed / failed
