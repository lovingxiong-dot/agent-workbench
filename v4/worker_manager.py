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
        """创建 Worker 并绑定环境"""
        from workers.agent_worker import AgentWorker
        from agent_engine.llm_registry import LLMRegistry

        llm = LLMRegistry("config.yaml", "config.yaml").get_llm(event.model)
        if not llm:
            self._bus.emit(WorkerErrorEvent(
                session_id=event.session_id,
                code="LLM_NOT_FOUND",
                detail=f"Model {event.model} not found",
            ))
            return

        worker = AgentWorker(
            mode_name=event.mode,
            current_llm=llm,
            session_id=event.session_id,
            project_root=event.project_root,
        )

        self._workers[event.session_id] = worker
        self.worker_count_changed.emit(self.active_count)

        # 桥接 Worker 信号 → MessageBus
        worker.chunk_ready.connect(
            lambda chunk: self._bus.emit(WorkerChunkEvent(
                session_id=event.session_id,
                worker_id=worker.worker_id,
                chunk=chunk,
            ))
        )
        worker.result_ready.connect(
            lambda sid, text: self._bus.emit(WorkerResultEvent(
                session_id=event.session_id,
                worker_id=worker.worker_id,
                full_text=text,
            ))
        )
        worker.error_occurred.connect(
            lambda code, err_detail: self._bus.emit(WorkerErrorEvent(
                session_id=event.session_id,
                worker_id=worker.worker_id,
                code=code,
                detail=err_detail,
            ))
        )

        # 启动 Worker
        worker.start()

        self._bus.emit(WorkerCreatedEvent(
            session_id=event.session_id,
            worker_id=worker.worker_id,
        ))

        logger.info("Worker created for session %s: %s", event.session_id, worker.worker_id)

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
                worker_id=getattr(worker, "worker_id", ""),
            ))

    # ── 公共查询 ──────────────────────────────────
    def get_worker(self, session_id: str) -> Optional[object]:
        return self._workers.get(session_id)

    def has_worker(self, session_id: str) -> bool:
        return session_id in self._workers
