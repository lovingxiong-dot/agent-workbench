"""
SessionRegistry — 工作线程注册表（前后台分离核心）

职责：
- 每个会话拥有独立的 PendingQueue 和 AgentWorker
- 切换会话时 Worker 不销毁（PAUSED），切回时 RESUME
- Worker 上限 5 个，超限自动 STOP 最旧

Worker 状态转换：
    RUNNING ─[pause]──→ PAUSED ─[resume]──→ RUNNING
        │                   │
        └──[stop]──→ STOPPED ←──[stop]──┘
"""
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

from services.pending_queue import PendingQueue

logger = logging.getLogger(__name__)

MAX_WORKERS = 5  # 最大活跃 Worker 数


class WorkerState(Enum):
    RUNNING = auto()   # 前台：UI 信号连接，处理任务
    PAUSED = auto()    # 后台：UI 信号断开，Worker 继续运行
    STOPPED = auto()   # 已销毁


@dataclass
class SessionSlot:
    """会话槽：每个会话的完整运行时状态"""
    session_id: str
    worker: Optional[object] = None          # AgentWorker 实例
    queue: Optional[PendingQueue] = None    # 会话级 PendingQueue
    phase_state: dict = field(default_factory=dict)  # PhaseState 序列化
    worker_state: WorkerState = WorkerState.STOPPED


class SessionRegistry(QObject):
    """工作线程注册表"""

    session_state_changed = Signal(str, str)  # session_id, WorkerState name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slots: dict[str, SessionSlot] = {}
        self._current_session = ""

    # ── 属性 ──────────────────────────────────────
    @property
    def current_session(self) -> str:
        return self._current_session

    @current_session.setter
    def current_session(self, value: str):
        self._current_session = value

    # ── 槽位管理 ─────────────────────────────────
    def get_or_create_slot(self, session_id: str) -> SessionSlot:
        """获取或创建会话槽"""
        if session_id not in self._slots:
            self._slots[session_id] = SessionSlot(
                session_id=session_id,
                queue=PendingQueue(parent=self),
            )
            logger.info("SessionSlot created: %s", session_id)
        return self._slots[session_id]

    def get_slot(self, session_id: str) -> Optional[SessionSlot]:
        return self._slots.get(session_id)

    def get_queue(self, session_id: str) -> Optional[PendingQueue]:
        slot = self._slots.get(session_id)
        return slot.queue if slot else None

    def get_worker(self, session_id: str) -> Optional[object]:
        slot = self._slots.get(session_id)
        return slot.worker if slot else None

    # ── 状态转换 ─────────────────────────────────
    def switch_to(self, session_id: str):
        """仅切换 _current_session 指针，不操作 Worker"""
        old = self._current_session
        self._current_session = session_id
        self.get_or_create_slot(session_id)
        logger.info("Registry switch: %s → %s", old, session_id)

    def pause(self, session_id: str):
        """断开 UI 信号，Worker 继续运行"""
        slot = self._slots.get(session_id)
        if slot and slot.worker_state == WorkerState.RUNNING:
            slot.worker_state = WorkerState.PAUSED
            self.session_state_changed.emit(session_id, "PAUSED")
            logger.info("Worker paused: %s", session_id)

    def resume(self, session_id: str):
        """重新连接 UI 信号，恢复处理"""
        slot = self._slots.get(session_id)
        if slot and slot.worker_state == WorkerState.PAUSED:
            slot.worker_state = WorkerState.RUNNING
            self.session_state_changed.emit(session_id, "RUNNING")
            logger.info("Worker resumed: %s", session_id)

    def stop(self, session_id: str):
        """停止 Worker 并释放槽位"""
        slot = self._slots.get(session_id)
        if slot and slot.worker_state != WorkerState.STOPPED:
            if slot.worker:
                try:
                    slot.worker.stop()
                except Exception:
                    pass
            slot.worker = None
            slot.worker_state = WorkerState.STOPPED
            slot.queue = None
            self.session_state_changed.emit(session_id, "STOPPED")
            logger.info("Worker stopped: %s", session_id)

    def remove_slot(self, session_id: str):
        """删除会话槽（删除会话时调用）"""
        if session_id in self._slots:
            self.stop(session_id)
            del self._slots[session_id]
            if self._current_session == session_id:
                self._current_session = ""

    def _enforce_worker_limit(self):
        """Worker 上限：超过 MAX_WORKERS 时自动 STOP 最旧的 PAUSED Worker"""
        running = [sid for sid, s in self._slots.items()
                   if s.worker_state in (WorkerState.RUNNING, WorkerState.PAUSED)]
        while len(running) > MAX_WORKERS:
            # 优先 STOP PAUSED，其次最旧的 RUNNING
            paused = [sid for sid in running if self._slots[sid].worker_state == WorkerState.PAUSED]
            victim = paused[0] if paused else running[0]
            self.stop(victim)
            running.remove(victim)
            logger.warning("Worker limit reached, stopped: %s", victim)