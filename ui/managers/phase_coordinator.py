"""
PhaseCoordinator — PhaseManager 信号 → MessageBus 事件转换器（v3）

每个 SessionRuntime 拥有一个 PhaseCoordinator，负责把 PhaseManager 的 Qt 信号
转换为带 session_id 的 Bus 事件。不再直接调用 UI。
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from core.event_bus import MessageBus
from core.events import (
    PhaseChangedEvent,
    PhaseAnalyzeRequiredEvent,
    PhaseConfirmRequiredEvent,
    PhaseExecuteRequiredEvent,
    PhaseVerifyRequiredEvent,
    PhaseArchiveRequiredEvent,
    PhaseFlowCompletedEvent,
    PhaseErrorEvent,
    UIAppendSystemEvent,
    UIClearPhaseUIEvent,
    UISetPhaseIndicatorEvent,
    UIShowConfirmationEvent,
    UIHideConfirmationEvent,
    UIShowSkipVerifyEvent,
    UIHideSkipVerifyEvent,
)

logger = logging.getLogger(__name__)


class PhaseCoordinator(QObject):
    """PhaseManager 信号 → MessageBus 事件桥接"""

    # 保留少量信号，便于同线程内直接消费（测试/兼容用）
    flow_completed = Signal(str, bool, str)  # session_id, success, message

    def __init__(
        self,
        session_id: str,
        phase_manager,
        message_bus: MessageBus,
        parent=None,
    ):
        super().__init__(parent)
        self._session_id = session_id
        self._phase_manager = phase_manager
        self._bus = message_bus

        self._flow_active = False
        self._phase_task_list = []
        self._connect_phase_signals()

    @property
    def is_flow_active(self) -> bool:
        return self._flow_active

    def start_flow(self, user_text: str, mode: str, context: str):
        """启动 Phase 工作流"""
        if self._flow_active:
            logger.warning("Flow already active for %s, ignoring start", self._session_id)
            return
        self._flow_active = True
        self._phase_manager.start(user_text, mode, context)

    def on_user_confirm(self, confirmed: bool = True):
        if self._flow_active:
            self._phase_manager.on_user_confirm(confirmed)

    def on_user_reanalyze(self):
        if self._flow_active:
            ctx = self._phase_manager.current_context()
            self._phase_manager.reset()
            self._phase_manager.start(ctx.user_text, ctx.mode, ctx.context)

    def on_user_skip_verify(self):
        if self._flow_active:
            self._phase_manager.on_verify_complete(True, "用户跳过验证")

    def reset(self):
        self._flow_active = False
        self._phase_task_list = []
        self._phase_manager.reset()

    # ── 内部 ──────────────────────────────────────
    def _connect_phase_signals(self):
        self._phase_manager.phase_changed.connect(self._on_phase_changed)
        self._phase_manager.analyze_required.connect(self._on_analyze_required)
        self._phase_manager.confirm_required.connect(self._on_confirm_required)
        self._phase_manager.execute_required.connect(self._on_execute_required)
        self._phase_manager.verify_required.connect(self._on_verify_required)
        self._phase_manager.archive_required.connect(self._on_archive_required)
        self._phase_manager.flow_finished.connect(self._on_flow_finished)
        self._phase_manager.error_occurred.connect(self._on_phase_error)

    def _emit(self, event):
        if self._bus is None:
            return
        try:
            self._bus.emit(event)
        except Exception as e:
            logger.warning("PhaseCoordinator emit error: %s", e)

    @Slot(str, str)
    def _on_phase_changed(self, phase: str, mode: str):
        self._emit(PhaseChangedEvent(
            session_id=self._session_id,
            phase=phase,
            mode=mode,
            task_count=len(self._phase_task_list),
        ))
        self._emit(UISetPhaseIndicatorEvent(
            session_id=self._session_id,
            phase=phase,
            task_count=len(self._phase_task_list),
        ))

    @Slot(str, str, str)
    def _on_analyze_required(self, user_text: str, mode: str, context: str):
        self._emit(PhaseAnalyzeRequiredEvent(
            session_id=self._session_id,
            user_text=user_text,
            mode=mode,
            context=context,
        ))

    @Slot(list)
    def _on_confirm_required(self, task_list):
        self._phase_task_list = list(task_list)
        self._emit(PhaseConfirmRequiredEvent(
            session_id=self._session_id,
            task_list=self._phase_task_list,
        ))
        self._emit(UIShowConfirmationEvent(
            session_id=self._session_id,
            task_list=self._phase_task_list,
        ))

    @Slot(list)
    def _on_execute_required(self, task_list):
        self._phase_task_list = list(task_list)
        self._emit(PhaseExecuteRequiredEvent(
            session_id=self._session_id,
            task_list=self._phase_task_list,
        ))
        self._emit(UIHideConfirmationEvent(session_id=self._session_id))

    @Slot(list, str)
    def _on_verify_required(self, execution_results, mode: str):
        self._emit(PhaseVerifyRequiredEvent(
            session_id=self._session_id,
            execution_results=execution_results,
            mode=mode,
        ))
        self._emit(UIShowSkipVerifyEvent(session_id=self._session_id))

    @Slot(str)
    def _on_archive_required(self, mode: str):
        self._emit(PhaseArchiveRequiredEvent(
            session_id=self._session_id,
            mode=mode,
        ))
        self._emit(UIHideSkipVerifyEvent(session_id=self._session_id))
        # 调用 PhaseManager 完成
        self._phase_manager.on_archive_complete(True, "工作流完成")

    @Slot(bool, str)
    def _on_flow_finished(self, success: bool, message: str):
        session_id = self._session_id
        logger.info("Flow finished for %s: success=%s, message=%s", session_id, success, message)

        self._flow_active = False

        if not success:
            self._emit(UIAppendSystemEvent(
                session_id=session_id,
                text=f"⚠️ {message}",
            ))

        self._emit(PhaseFlowCompletedEvent(
            session_id=session_id,
            success=success,
            message=message,
        ))
        self._emit(UIClearPhaseUIEvent(session_id=session_id))
        self.flow_completed.emit(session_id, success, message)

    @Slot(str, str)
    def _on_phase_error(self, code: str, detail: str):
        logger.error("Phase error: %s - %s", code, detail)
        self._emit(UIAppendSystemEvent(
            session_id=self._session_id,
            text=f"❌ Phase 错误 [{code}]: {detail}",
        ))
        self._phase_manager.reset()
        self._finish_flow(False, detail)

    def _finish_flow(self, success: bool, message: str):
        """完成工作流，但不重复发送系统消息（错误路径已发送）"""
        session_id = self._session_id
        logger.info("Flow finished for %s: success=%s, message=%s", session_id, success, message)

        self._flow_active = False

        self._emit(PhaseFlowCompletedEvent(
            session_id=session_id,
            success=success,
            message=message,
        ))
        self._emit(UIClearPhaseUIEvent(session_id=session_id))
        self.flow_completed.emit(session_id, success, message)
