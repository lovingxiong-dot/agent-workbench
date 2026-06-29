"""
SignalAdapter — AgentWorker Qt 信号 → MessageBus 事件转换器

每个 Worker 实例配一个 Adapter，按 session_id 路由事件。
支持 pause/resume：pause 时停止转发，resume 后恢复。
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject

from core.event_bus import MessageBus
from core.events import (
    WorkerChunkEvent,
    WorkerResultEvent,
    WorkerErrorEvent,
    WorkerLogMessageEvent,
    WorkerTaskCreatedEvent,
    WorkerTaskFinishedEvent,
    WorkerTokenUsedEvent,
    WorkerTurnMetricsEvent,
    WorkerConfirmRequiredEvent,
    WorkerToolExecutedEvent,
    WorkerAnalyzeResultEvent,
    WorkerExecuteResultEvent,
    WorkerVerifyResultEvent,
)
from workers.agent_worker import AgentWorker

logger = logging.getLogger(__name__)


class SignalAdapter(QObject):
    """将 AgentWorker 信号转换为带 session_id 的 MessageBus 事件"""

    def __init__(
        self,
        worker: AgentWorker,
        session_id: str,
        message_bus: MessageBus,
        parent=None,
    ):
        super().__init__(parent)
        self._worker = worker
        self._session_id = session_id
        self._bus = message_bus
        self._enabled = True
        self._connections = []

        self._bind()

    @property
    def session_id(self) -> str:
        return self._session_id

    def set_enabled(self, enabled: bool):
        """暂停/恢复事件转发"""
        self._enabled = enabled

    def pause(self):
        self.set_enabled(False)

    def resume(self):
        self.set_enabled(True)

    def disconnect_all(self):
        """断开所有信号连接"""
        for signal, slot in self._connections:
            try:
                signal.disconnect(slot)
            except Exception:
                pass
        self._connections.clear()

    def _emit(self, event):
        """内部转发包装"""
        if not self._enabled:
            return
        try:
            self._bus.emit(event)
        except Exception as e:
            logger.warning("SignalAdapter emit error for %s: %s", self._session_id, e)

    def _bind(self):
        """绑定 Worker 所有信号"""
        worker = self._worker
        sid = self._session_id

        mappings = [
            (worker.chunk_ready, self._on_chunk),
            (worker.result_ready, self._on_result),
            (worker.error_occurred, self._on_error),
            (worker.log_message, self._on_log),
            (worker.task_created, self._on_task_created),
            (worker.task_finished, self._on_task_finished),
            (worker.token_used, self._on_token_used),
            (worker.turn_metrics_ready, self._on_turn_metrics),
            (worker.confirm_required, self._on_confirm_required),
            (worker.tool_executed, self._on_tool_executed),
            (worker.analyze_result_ready, self._on_analyze_result),
            (worker.execute_result_ready, self._on_execute_result),
            (worker.verify_result_ready, self._on_verify_result),
        ]

        for signal, slot in mappings:
            signal.connect(slot)
            self._connections.append((signal, slot))

    def _on_chunk(self, chunk: str):
        self._emit(WorkerChunkEvent(session_id=self._session_id, chunk=chunk))

    def _on_result(self, session_id: str, full_text: str):
        # Worker 的 result_ready 已经携带 session_id，校验一致性
        if session_id != self._session_id:
            logger.warning(
                "Worker result session mismatch: adapter=%s, signal=%s",
                self._session_id,
                session_id,
            )
            return
        self._emit(WorkerResultEvent(session_id=self._session_id, full_text=full_text))

    def _on_error(self, code: str, detail: str):
        self._emit(WorkerErrorEvent(
            session_id=self._session_id,
            code=code,
            detail=detail,
        ))

    def _on_log(self, message: str):
        self._emit(WorkerLogMessageEvent(
            session_id=self._session_id,
            message=message,
        ))

    def _on_task_created(self, task_id: str, description: str):
        self._emit(WorkerTaskCreatedEvent(
            session_id=self._session_id,
            task_id=task_id,
            description=description,
        ))

    def _on_task_finished(self, task_id: str, result: str):
        self._emit(WorkerTaskFinishedEvent(
            session_id=self._session_id,
            task_id=task_id,
            result=result,
        ))

    def _on_token_used(self, model: str, token_type: str, count: int, cost: int):
        self._emit(WorkerTokenUsedEvent(
            session_id=self._session_id,
            model=model,
            token_type=token_type,
            count=count,
            cost=cost,
        ))

    def _on_turn_metrics(self, metrics: object):
        self._emit(WorkerTurnMetricsEvent(
            session_id=self._session_id,
            metrics=metrics,
        ))

    def _on_confirm_required(self, task_id: str, description: str):
        self._emit(WorkerConfirmRequiredEvent(
            session_id=self._session_id,
            task_id=task_id,
            description=description,
        ))

    def _on_tool_executed(self, name: str, args: dict, result: str, elapsed_ms: int):
        self._emit(WorkerToolExecutedEvent(
            session_id=self._session_id,
            tool_name=name,
            args=args,
            result=result,
            elapsed_ms=elapsed_ms,
        ))

    def _on_analyze_result(self, task_list: list):
        self._emit(WorkerAnalyzeResultEvent(
            session_id=self._session_id,
            task_list=task_list,
        ))

    def _on_execute_result(self, result: str):
        self._emit(WorkerExecuteResultEvent(
            session_id=self._session_id,
            result=result,
        ))

    def _on_verify_result(self, result: str):
        self._emit(WorkerVerifyResultEvent(
            session_id=self._session_id,
            result=result,
        ))
