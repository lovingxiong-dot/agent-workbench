"""
TaskService — 任务调度中心

职责：
- 接收 MainWindow 的任务提交请求
- 准入控制（容量检查）
- 管理 WorkerPool 和任务队列
- 发射状态变化信号供 UI 订阅
- Phase 变化回调（供 Worker 调用）
"""
from typing import Dict, Optional, Tuple
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from workers.session_task import SessionTask, TaskStatus
from workers.task_capacity import TaskCapacity
from workers.task_queue import TaskQueue


class ResourceError(RuntimeError):
    """资源不足，无法提交新任务"""
    pass


class TaskService(QObject):
    # === 信号定义 ===
    task_status_changed = Signal(str, str)       # session_id, status
    capacity_changed = Signal(int, int, int)      # active_count, queued_count, max_total
    task_progress = Signal(str, str, str)         # session_id, phase, detail
    tool_usage_changed = Signal(int, int)         # tools_in_use, max_tools
    task_completed = Signal(str, bool)            # session_id, success

    def __init__(self, capacity: TaskCapacity = None):
        super().__init__()
        self.capacity = capacity or TaskCapacity()
        self._queue = TaskQueue(self.capacity.max_queued_tasks)
        self._tasks: Dict[str, SessionTask] = {}
        self._active_tools: int = 0

        # WorkerPool 延迟创建（需要传入 worker 创建工厂函数）
        self._pool = None  # type: Optional[WorkerPool]

    def set_pool(self, pool):
        """注入 WorkerPool 实例（由 MainWindow 在初始化完成后调用）"""
        self._pool = pool

    # ═══════════════════════════════════════════════════════
    # 准入控制
    # ═══════════════════════════════════════════════════════
    def can_submit(self) -> Tuple[bool, str]:
        """检查是否可以提交新任务"""
        active = sum(1 for t in self._tasks.values()
                     if t.status in (TaskStatus.ANALYZING, TaskStatus.EXECUTING, TaskStatus.VERIFYING))
        queued = self._queue.size

        if active >= self.capacity.max_concurrent_tasks:
            if queued >= self.capacity.max_queued_tasks:
                return False, "任务队列已满，请等待"
            return True, "queued"

        # 检查系统资源
        try:
            import psutil
            mem_available = psutil.virtual_memory().available / (1024 * 1024)
            if mem_available < self.capacity.memory_threshold_mb:
                return False, f"内存不足 (可用 {mem_available:.0f}MB < {self.capacity.memory_threshold_mb}MB)"
        except ImportError:
            pass  # psutil 未安装时跳过内存检查

        return True, "ok"

    # ═══════════════════════════════════════════════════════
    # 任务调度
    # ═══════════════════════════════════════════════════════
    def submit_task(self, session_id: str, mode: str, user_input: str) -> SessionTask:
        """提交新任务。可能立即执行或排入队列。"""
        ok, reason = self.can_submit()
        if not ok:
            raise ResourceError(reason)

        status = TaskStatus.QUEUED if reason == "queued" else TaskStatus.ANALYZING
        task = SessionTask(
            session_id=session_id,
            mode=mode,
            user_input=user_input,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        task._set_status(status)

        # 如果已有同会话的旧任务且未终止，则取消
        old_task = self._tasks.get(session_id)
        if old_task is not None and not old_task.is_terminal:
            print(f"[DIAG-TASK] submit_task canceling old task: session={session_id}, old_status={old_task.status.value}", flush=True)
            self.cancel_task(session_id)

        self._tasks[session_id] = task

        if reason == "ok" and self._pool:
            # 有空闲 Worker，立即执行
            self._pool.submit(task, self._on_phase_change, self._on_task_done)
        elif reason == "queued":
            self._queue.enqueue(session_id, mode, user_input)
        elif not self._pool:
            # WorkerPool 尚未就绪，排入队列等待
            self._queue.enqueue(session_id, mode, user_input)

        self.task_status_changed.emit(session_id, task.status.value)
        self._emit_capacity()
        return task

    def _drain_queue(self):
        """从队列中取出任务提交到 WorkerPool。终端状态任务不会被重新激活。"""
        while self._queue.size > 0:
            ok, reason = self.can_submit()
            if not ok or reason == "queued":
                break
            queued = self._queue.dequeue()
            if queued is None:
                break
            task = self._tasks.get(queued.session_id)
            if task is None:
                task = SessionTask(
                    session_id=queued.session_id,
                    mode=queued.mode,
                    user_input=queued.user_input,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                )
                self._tasks[queued.session_id] = task
            # 该会话任务已到达终态，跳过 stale 队列项，避免覆盖 completed/failed
            if task.is_terminal:
                continue
            task._set_status(TaskStatus.ANALYZING)
            if self._pool:
                self._pool.submit(task, self._on_phase_change, self._on_task_done)
            self.task_status_changed.emit(task.session_id, task.status.value)

    def cancel_task(self, session_id: str):
        """取消指定会话的任务。terminal 状态不会被覆盖。"""
        task = self._tasks.get(session_id)
        if task and task.is_terminal:
            return
        if task and task.is_waiting:
            self._queue.remove(session_id)
        if task:
            task._set_status(TaskStatus.FAILED)
            task.last_error = "用户取消"
            task.updated_at = datetime.now().isoformat()
            self.task_status_changed.emit(session_id, TaskStatus.FAILED.value)
            self.task_completed.emit(session_id, False)
        if self._pool:
            self._pool.cancel(session_id)
        self._emit_capacity()
        # 取消后释放容量，尝试启动队列中的下一个任务
        self._drain_queue()

    def fail_task(self, session_id: str, error: str = ""):
        """将指定会话任务标记为失败。terminal 状态不会被覆盖。"""
        task = self._tasks.get(session_id)
        if task and task.is_terminal:
            return
        if task:
            task._set_status(TaskStatus.FAILED)
            if error:
                task.last_error = error
            task.updated_at = datetime.now().isoformat()
            self.task_status_changed.emit(session_id, TaskStatus.FAILED.value)
            self.task_completed.emit(session_id, False)
        self._emit_capacity()
        # 失败后释放容量，尝试启动队列中的下一个任务
        self._drain_queue()

    def get_task_status(self, session_id: str) -> Optional[SessionTask]:
        return self._tasks.get(session_id)

    def get_tasks_for_session(self, session_id: str) -> Optional[SessionTask]:
        return self._tasks.get(session_id)

    def has_active_task(self, session_id: str) -> bool:
        task = self._tasks.get(session_id)
        return task is not None and task.is_active

    # ═══════════════════════════════════════════════════════
    # Phase 变化回调（供 Worker / WorkerPool 调用）
    # ═══════════════════════════════════════════════════════
    def _on_phase_change(self, session_id: str, phase: str, detail: str = ""):
        task = self._tasks.get(session_id)
        if task and not task.is_terminal:
            task._set_status(TaskStatus(phase) if phase in {s.value for s in TaskStatus} else TaskStatus.ANALYZING)
            task.updated_at = datetime.now().isoformat()
            self.task_progress.emit(session_id, phase, detail)
            self.task_status_changed.emit(session_id, phase)

    # ═══════════════════════════════════════════════════════
    # 工具使用追踪
    # ═══════════════════════════════════════════════════════
    def on_tool_start(self, session_id: str):
        self._active_tools += 1
        self.tool_usage_changed.emit(self._active_tools, self.capacity.max_total_tools)

    def on_tool_end(self, session_id: str):
        self._active_tools = max(0, self._active_tools - 1)
        self.tool_usage_changed.emit(self._active_tools, self.capacity.max_total_tools)

    # ═══════════════════════════════════════════════════════
    # 任务完成
    # ═══════════════════════════════════════════════════════
    def complete_task(self, session_id: str, success: bool, error: str = ""):
        """由 MainWindow 显式调用，标记一次用户请求的工作流完成/失败。terminal 状态不会被覆盖。"""
        task = self._tasks.get(session_id)
        if task and task.is_terminal:
            return
        if task:
            task._set_status(TaskStatus.COMPLETED if success else TaskStatus.FAILED)
            if error:
                task.last_error = error
            task.updated_at = datetime.now().isoformat()
        self.task_completed.emit(session_id, success)
        status_str = (task.status.value if task else TaskStatus.COMPLETED.value)
        self.task_status_changed.emit(session_id, status_str)
        self._emit_capacity()
        # 尝试从队列中取出下一个任务
        self._drain_queue()

    def _on_task_done(self, session_id: str, success: bool):
        """WorkerPool 回调用入口，统一委托到 complete_task"""
        if self._pool:
            self._pool.on_task_complete(session_id)
        self.complete_task(session_id, success)

    # ═══════════════════════════════════════════════════════
    # 容量查询
    # ═══════════════════════════════════════════════════════
    def _emit_capacity(self):
        active = sum(1 for t in self._tasks.values()
                     if t.status in (TaskStatus.ANALYZING, TaskStatus.EXECUTING,
                                     TaskStatus.VERIFYING, TaskStatus.AWAITING_CONFIRM))
        queued = self._queue.size
        self.capacity_changed.emit(active, queued, self.capacity.total_capacity)

    def get_capacity_info(self) -> dict:
        """供 UI 查询当前容量状态"""
        active = sum(1 for t in self._tasks.values()
                     if t.status in (TaskStatus.ANALYZING, TaskStatus.EXECUTING, TaskStatus.VERIFYING))
        return {
            "active_tasks": active,
            "max_concurrent": self.capacity.max_concurrent_tasks,
            "queued_tasks": self._queue.size,
            "max_queued": self.capacity.max_queued_tasks,
            "tools_in_use": self._active_tools,
            "max_tools": self.capacity.max_total_tools,
            "total_capacity": self.capacity.total_capacity,
        }

    @property
    def tasks(self) -> Dict[str, SessionTask]:
        return self._tasks
