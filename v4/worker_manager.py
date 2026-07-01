"""
worker_manager.py — v4 Worker 管理器

设计原则：
- 环境感知：Worker 创建时绑定环境（project_root、tools）
- 并发槽位控制：系统最多同时运行 N 个 Worker（默认 5）
- 任务绑定：Worker 绑定到任务，不绑定到会话前台/后台状态
- 会话切换不操作 Worker：只切 UI，Worker 继续运行

删除：
- PAUSED / STOPPED 状态（Worker 只绑定任务生命周期）
- pause/resume 方法（不需要）
- Worker 注册表（Worker 直接绑定到 SessionRuntime）
"""
import logging
from typing import Optional, Dict, List
from PySide6.QtCore import QObject, Signal

from .event_bus import MessageBus
from .events import (
    WorkerCreateEvent, WorkerCreatedEvent, WorkerDestroyEvent, WorkerDestroyedEvent,
    WorkerChunkEvent, WorkerResultEvent, WorkerErrorEvent, WorkerToolEvent,
    PhaseChangedEvent, PhaseConfirmRequiredEvent, PhaseCompleteEvent, PhaseErrorEvent,
)

logger = logging.getLogger(__name__)


class WorkerManager(QObject):
    """Worker 管理器（环境感知 + 并发槽位控制）

    职责：
    - 管理 Worker 生命周期（创建、销毁）
    - 环境绑定：Worker 创建时绑定 project_root、tools
    - 并发槽位控制：最多 N 个 Worker 同时运行
    - 事件桥接：Worker 信号 → MessageBus 事件

    不维护：
    - 不维护 PAUSED/STOPPED 状态
    - 不维护会话前台/后台状态
    - 不直接操作 UI
    """

    MAX_WORKERS = 5  # 系统最大并发 Worker 数

    # 信号（主要用于调试/监控）
    worker_count_changed = Signal(int)  # 当前活跃 Worker 数

    def __init__(self, message_bus: MessageBus, max_workers: int = MAX_WORKERS, parent=None):
        super().__init__(parent)
        self._bus = message_bus
        self._max_workers = max(1, max_workers)
        self._workers: Dict[str, object] = {}  # session_id → Worker
        self._pending: List[WorkerCreateEvent] = []  # 超出并发槽位的排队创建请求

        # 订阅事件
        self._bus.subscribe_name("worker", "create", self._on_create)
        self._bus.subscribe_name("worker", "destroy", self._on_destroy)

    def get_worker(self, session_id: str) -> Optional[object]:
        """获取指定会话的 Worker 实例（供 Orchestrator attach 使用）。"""
        return self._workers.get(session_id)

    def confirm(self, session_id: str, confirmed: bool):
        """将用户确认结果转发给对应 Worker。"""
        worker = self._workers.get(session_id)
        if worker and hasattr(worker, "confirm"):
            worker.confirm(confirmed)

    # ── 属性 ──────────────────────────────────
    @property
    def active_count(self) -> int:
        return len(self._workers)

    @property
    def has_capacity(self) -> bool:
        return self.active_count < self._max_workers

    @property
    def is_full(self) -> bool:
        return self.active_count >= self._max_workers

    # ── 事件处理 ──────────────────────────────────
    def _on_create(self, event: WorkerCreateEvent):
        """处理 Worker 创建请求"""
        print(f"[DEBUG wm _on_create] sid={event.session_id[-8:]} cls={self.__class__.__name__}", flush=True)
        if event.session_id in self._workers:
            logger.warning("Worker exists for %s, skip", event.session_id)
            return

        if self.is_full:
            # 超出并发槽位，排队等待
            self._pending.append(event)
            return

        self._create_worker(event)

    def _on_destroy(self, event: WorkerDestroyEvent):
        """处理 Worker 销毁请求"""
        self._destroy_worker(event.session_id)

        # 检查排队请求
        if self._pending:
            next_event = self._pending.pop(0)
            self._create_worker(next_event)

    # ── 内部方法 ──────────────────────────────────
    def _create_worker(self, event: WorkerCreateEvent):
        """创建 V4Worker 并绑定环境，启动后提交用户文本。"""
        from .worker import V4Worker

        worker = V4Worker(
            mode_name=event.mode,
            model_id=event.model,
            session_id=event.session_id,
            project_root=getattr(event, "project_root", ""),
        )

        self._workers[event.session_id] = worker
        self.worker_count_changed.emit(self.active_count)

        # 桥接 Worker 信号 → MessageBus
        worker.chunk_ready.connect(
            lambda chunk: self._bus.emit(WorkerChunkEvent(
                session_id=event.session_id,
                worker_id=worker.session_id,
                chunk=chunk,
            ))
        )
        worker.result_ready.connect(
            lambda sid, text: self._bus.emit(WorkerResultEvent(
                session_id=event.session_id,
                worker_id=worker.session_id,
                full_text=text,
            ))
        )
        worker.error_occurred.connect(
            lambda code, err_detail: self._bus.emit(WorkerErrorEvent(
                session_id=event.session_id,
                worker_id=worker.session_id,
                code=code,
                detail=err_detail,
            ))
        )
        worker.phase_changed.connect(
            lambda phase, task_count: self._bus.emit(PhaseChangedEvent(
                session_id=event.session_id,
                phase=phase,
                task_count=task_count,
            ))
        )
        worker.confirm_required.connect(
            lambda task_list: self._bus.emit(PhaseConfirmRequiredEvent(
                session_id=event.session_id,
                task_list=task_list,
            ))
        )
        worker.phase_complete.connect(
            lambda success, message: self._bus.emit(PhaseCompleteEvent(
                session_id=event.session_id,
                success=success,
                message=message,
            ))
        )
        worker.phase_error.connect(
            lambda code, detail: self._bus.emit(PhaseErrorEvent(
                session_id=event.session_id,
                code=code,
                detail=detail,
            ))
        )
        worker.tool_called.connect(
            lambda name, args, result, elapsed_ms, success: self._bus.emit(WorkerToolEvent(
                session_id=event.session_id,
                worker_id=worker.session_id,
                tool_name=name,
                args=args,
                result=result,
                elapsed_ms=elapsed_ms,
                success=success,
            ))
        )

        # 启动 Worker
        worker.start()

        # 提交用户文本
        user_text = getattr(event, "user_text", "")
        if user_text:
            worker.submit(user_text)

        self._bus.emit(WorkerCreatedEvent(
            session_id=event.session_id,
            worker_id=worker.session_id,
        ))

        logger.info("V4Worker created for session %s: %s", event.session_id, worker.session_id)

    def _destroy_worker(self, session_id: str):
        """销毁 Worker"""
        worker = self._workers.pop(session_id, None)
        if worker:
            try:
                worker.stop()
                worker.wait(3000)
            except Exception as e:
                logger.error("Worker destroy error: %s", e)

            self.worker_count_changed.emit(self.active_count)
            self._bus.emit(WorkerDestroyedEvent(
                session_id=session_id,
                worker_id=session_id,
            ))

    # ── 公共查询 ──────────────────────────────────
    def get_worker(self, session_id: str) -> Optional[object]:
        return self._workers.get(session_id)

    def has_worker(self, session_id: str) -> bool:
        return session_id in self._workers
