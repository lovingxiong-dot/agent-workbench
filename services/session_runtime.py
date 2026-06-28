"""
session_runtime.py — 会话运行时聚合根

每个会话拥有独立的 Queue、Phase、Task、Worker 引用。
不直接操作 UI，只维护本会话内的业务对象。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject

from agent_engine.phase_manager import PhaseManager
from services.pending_queue import PendingQueue
from ui.managers.queue_manager import QueueManager
from workers.session_task import SessionTask, TaskStatus


@dataclass
class SessionRuntime(QObject):
    """
    单个会话的完整运行时聚合根。

    职责：
    - 持有本会话独立的 PendingQueue / QueueManager / PhaseManager
    - 持有当前 Worker 与 Task 引用
    - 保存 phase_state 快照，用于切回时恢复 UI
    """

    session_id: str
    project_path: str
    title: str
    mode: str
    model: str

    # 业务对象（__post_init__ 中创建）
    pending_queue: PendingQueue = field(init=False)
    queue_manager: QueueManager = field(init=False)
    phase_manager: PhaseManager = field(init=False)

    # 运行时引用
    worker: Optional[object] = None
    task: Optional[SessionTask] = None

    # 状态快照
    phase_state: dict = field(default_factory=dict)

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        QObject.__init__(self)
        self.pending_queue = PendingQueue(parent=self)
        self.queue_manager = QueueManager(
            pending_queue=self.pending_queue,
            session_id=self.session_id,
            parent=self,
        )
        self.phase_manager = PhaseManager(parent=self)

    @property
    def is_active(self) -> bool:
        """当前是否有未终止的任务在运行。"""
        if self.task is None:
            return False
        return not self.task.is_terminal

    @property
    def current_phase(self) -> str:
        """当前 PhaseManager 阶段。"""
        return self.phase_manager.current_phase()

    def attach_worker(self, worker: object) -> None:
        """绑定当前 Worker。"""
        self.worker = worker
        self.updated_at = datetime.now()

    def detach_worker(self) -> None:
        """解绑 Worker。"""
        self.worker = None
        self.updated_at = datetime.now()

    def bind_task(self, task: SessionTask) -> None:
        """绑定当前 Task。"""
        self.task = task
        self.updated_at = datetime.now()

    def clear_task(self) -> None:
        """清除当前 Task 引用（任务已终止）。"""
        self.task = None
        self.updated_at = datetime.now()

    def save_phase_state(self, state: dict) -> None:
        """保存 phase 状态快照。"""
        self.phase_state = dict(state)
        self.updated_at = datetime.now()

    def clear_phase_state(self) -> None:
        """清除 phase 状态快照。"""
        self.phase_state.clear()
        self.updated_at = datetime.now()

    def to_snapshot(self) -> dict:
        """生成可序列化的快照。"""
        return {
            "session_id": self.session_id,
            "project_path": self.project_path,
            "title": self.title,
            "mode": self.mode,
            "model": self.model,
            "phase_state": self.phase_state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
