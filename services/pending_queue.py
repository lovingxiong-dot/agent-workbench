"""
PendingQueue — 双槽位等待队列

管理用户发送消息的并发控制：
- 2 个槽位：slot[0] = 当前 streaming，slot[1] = 排队中
- 槽满时拒绝新消息，通过信号通知 UI 灰化发送键
- 每个槽位独立可取消
- 当前任务完成时自动 dequeue 下一个
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal
import threading
import time


@dataclass
class PendingTask:
    """可取消的待处理任务"""
    task_id: str
    user_text: str
    mode: str
    context: str
    cancel_event: threading.Event = field(default_factory=threading.Event)
    status: str = "pending"  # pending | streaming | cancelled | completed
    timestamp: float = field(default_factory=time.time)


class PendingQueue(QObject):
    """双槽位等待队列，容量上限 2"""
    
    MAX_SLOTS = 2
    
    # 信号：队列状态变化 → UI 更新发送键/队列条
    queue_changed = Signal()  # 长度、满状态变化
    task_started = Signal(str)  # task_id — 开始 streaming
    task_cancelled = Signal(str)  # task_id — 被取消
    task_completed = Signal(str)  # task_id — 正常完成
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._slots: list[Optional[PendingTask]] = [None, None]
        self._lock = threading.Lock()
    
    def enqueue(self, task: PendingTask) -> bool:
        """入队：找到第一个空槽位，返回是否成功"""
        with self._lock:
            for i in range(self.MAX_SLOTS):
                if self._slots[i] is None:
                    self._slots[i] = task
                    if i == 0:
                        task.status = "streaming"
                        print(f"[DIAG-QUEUE] enqueue slot[0] task_id={task.task_id}, text='{task.user_text[:20]}'", flush=True)
                        self.task_started.emit(task.task_id)
                    else:
                        print(f"[DIAG-QUEUE] enqueue slot[{i}] task_id={task.task_id}, text='{task.user_text[:20]}'", flush=True)
                    self.queue_changed.emit()
                    return True
            print(f"[DIAG-QUEUE] enqueue FAILED: queue full, slots={[s.task_id if s else None for s in self._slots]}", flush=True)
            return False  # 槽满
    
    def cancel(self, slot_index: int):
        """取消指定槽位的任务（0=当前streaming, 1=排队中）"""
        with self._lock:
            if 0 <= slot_index < self.MAX_SLOTS:
                task = self._slots[slot_index]
                if task and task.status not in ("cancelled", "completed"):
                    task.cancel_event.set()
                    task.status = "cancelled"
                    self.task_cancelled.emit(task.task_id)
                    self._slots[slot_index] = None
                    self._compact()
                    self.queue_changed.emit()
            else:
                import logging
                logging.warning(f"PendingQueue.cancel: slot_index={slot_index} out of range [0, {self.MAX_SLOTS})")
    
    def cancel_all(self):
        """取消所有任务"""
        for i in range(self.MAX_SLOTS - 1, -1, -1):
            self.cancel(i)
    
    def mark_task_completed(self, task_id: str):
        """
        标记当前 streaming 任务完成，自动 dequeue 下一个。
        
        _compact() 内部已将 slot[1] 移到 slot[0] 并设置 status="streaming" 和 emit task_started，
        此处只负责移除当前任务和发射 task_completed，不重复处理下一个任务的启动。
        """
        with self._lock:
            if self._slots[0] and self._slots[0].task_id == task_id:
                self._slots[0].status = "completed"
                self._slots[0] = None
                self.task_completed.emit(task_id)
                self._compact()
                self.queue_changed.emit()
    
    def dequeue(self) -> Optional[PendingTask]:
        """取出下一个待处理任务（FIFO），返回 None 表示队列空"""
        with self._lock:
            for i in range(self.MAX_SLOTS):
                task = self._slots[i]
                if task and task.status == "pending":
                    self._slots[i] = None
                    self._compact()
                    self.queue_changed.emit()
                    return task
            return None
    
    def get_streaming_task(self) -> Optional[PendingTask]:
        """获取当前正在 streaming 的任务（slot 0）"""
        with self._lock:
            return self._slots[0]
    
    def get_pending_tasks(self) -> list[PendingTask]:
        """获取所有排队中的任务（不含 streaming）"""
        with self._lock:
            return [t for t in self._slots if t and t.status == "pending"]
    
    @property
    def is_full(self) -> bool:
        with self._lock:
            return all(s is not None for s in self._slots)
    
    @property
    def length(self) -> int:
        with self._lock:
            return sum(1 for s in self._slots if s is not None)
    
    @property
    def has_streaming(self) -> bool:
        with self._lock:
            return self._slots[0] is not None
    
    def clear(self):
        """清空队列（切换会话时使用）"""
        with self._lock:
            for i in range(self.MAX_SLOTS):
                if self._slots[i]:
                    self._slots[i].cancel_event.set()
                    self._slots[i].status = "cancelled"
                    self._slots[i] = None
        self.queue_changed.emit()
    
    def _compact(self):
        """压缩槽位：将 slot[1] 移到 slot[0]（如果 slot[0] 为空）"""
        if self._slots[0] is None and self._slots[1] is not None:
            self._slots[0] = self._slots[1]
            self._slots[0].status = "streaming"
            self._slots[1] = None
            self.task_started.emit(self._slots[0].task_id)
