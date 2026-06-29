"""
QueueManager — 双槽位队列状态管理器（会话级）

职责：
- 封装 PendingQueue，对外暴露高级 API
- 队列状态机：IDLE → STREAMING → QUEUED_1(FULL)
- UI 状态信号（发送键、队列条）
- mark_current_done() 为唯一完成路径
- 所有操作绑定 session_id，支持多会话独立队列
"""
import logging
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

from services.pending_queue import PendingQueue, PendingTask

logger = logging.getLogger(__name__)


class QueueState(Enum):
    IDLE = auto()
    STREAMING = auto()
    QUEUED_1 = auto()  # 等同于 FULL


class QueueManager(QObject):
    """双槽位队列状态管理器（会话级）"""

    # 信号
    state_changed = Signal(str)           # QueueState 名称
    send_enabled_changed = Signal(bool)   # 发送键是否可用
    queue_bar_text_changed = Signal(str)  # 队列条文本
    task_ready_to_start = Signal(object)  # PendingTask — 需要启动 Phase 工作流
    task_stopped = Signal(str)            # session_id — 用户停止/任务完成

    def __init__(self, pending_queue: PendingQueue, session_id: str, parent=None):
        super().__init__(parent)
        self._pq = pending_queue
        self._session_id = session_id
        self._state = QueueState.IDLE
        self._connect_internal_signals()

    # ── 属性 ──────────────────────────────────────
    @property
    def state(self) -> QueueState:
        return self._state

    @property
    def is_full(self) -> bool:
        return self._pq.is_full

    @property
    def session_id(self) -> str:
        return self._session_id

    # ── 核心操作 ──────────────────────────────────
    def enqueue(self, user_text: str, mode: str, context: str) -> bool:
        """入队：返回 False 表示槽满，调用方保留输入"""
        import uuid
        task = PendingTask(
            task_id=uuid.uuid4().hex[:8],
            user_text=user_text,
            mode=mode,
            context=context,
        )
        if not self._pq.enqueue(task):
            return False
        # 如果入队到 slot[0]，立即通知启动
        streaming = self._pq.get_streaming_task()
        if streaming and streaming.task_id == task.task_id:
            self.task_ready_to_start.emit(streaming)
        self._update_state()
        return True

    def cancel_current(self):
        """取消当前 streaming 任务"""
        self._pq.cancel(0)
        self._update_state()
        self.task_stopped.emit(self._session_id)

    def cancel_pending(self):
        """取消所有排队任务（保留当前 streaming）"""
        if self._pq.get_pending_tasks():
            self._pq.cancel(1)
            self._update_state()

    def mark_current_done(self):
        """唯一完成路径：标记当前任务完成，自动出队下一个"""
        streaming = self._pq.get_streaming_task()
        if streaming:
            self._pq.mark_task_completed(streaming.task_id)
            self._update_state()
            self.task_stopped.emit(self._session_id)

    def clear(self):
        """清空队列（切换会话时调用）"""
        self._pq.clear()
        self._update_state()

    def get_streaming_task(self) -> Optional[PendingTask]:
        return self._pq.get_streaming_task()

    def get_pending_tasks(self) -> list:
        return self._pq.get_pending_tasks()

    # ── 内部 ──────────────────────────────────────
    def _connect_internal_signals(self):
        """监听 PendingQueue 信号并转发为高级信号"""
        self._pq.queue_changed.connect(self._on_queue_changed)
        self._pq.task_started.connect(self._on_task_started)
        self._pq.task_completed.connect(self._on_task_completed)

    def _on_queue_changed(self):
        """队列变化 → 更新状态机 → 发射信号"""
        self._update_state()

    def _on_task_started(self, task_id: str):
        """任务开始 → 更新状态"""
        self._update_state()

    def _on_task_completed(self, task_id: str):
        """任务完成 → 更新状态"""
        self._update_state()

    def _update_state(self):
        """根据 PendingQueue 状态更新内部状态机"""
        if self._pq.has_streaming:
            if self._pq.is_full:
                self._state = QueueState.QUEUED_1
            else:
                self._state = QueueState.STREAMING
        else:
            self._state = QueueState.IDLE

        # 发射状态信号
        self.state_changed.emit(self._state.name)
        self.send_enabled_changed.emit(not self._pq.is_full)

        # 构建队列条文本
        self.queue_bar_text_changed.emit(self._build_queue_bar_text())

    def _build_queue_bar_text(self) -> str:
        """构建队列条显示文本"""
        streaming = self._pq.get_streaming_task()
        pending = self._pq.get_pending_tasks()

        if not streaming and not pending:
            return ""

        parts = []
        if streaming:
            preview = streaming.user_text[:40] + "..." if len(streaming.user_text) > 40 else streaming.user_text
            parts.append(f"🔄 处理中: {preview}")
        for task in pending:
            preview = task.user_text[:40] + "..." if len(task.user_text) > 40 else task.user_text
            parts.append(f"📋 排队中: {preview}")
        if self._pq.is_full:
            parts.append("[队列已满，请等待]")

        return "  |  ".join(parts)
