"""
PhaseCoordinator — Phase 工作流协调器

职责：
- 接收 PhaseManager 所有信号，编排工作流
- _on_flow_finished() 为唯一完成路径
- 所有操作绑定 session_id
- UI 更新通过 phase_ui_update 信号通知 MainWindow
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class PhaseCoordinator(QObject):
    """Phase 工作流协调器"""

    # 信号
    phase_ui_update = Signal(str, int)   # phase_name, task_count
    flow_completed = Signal(str, bool, str)  # session_id, success, message
    worker_error = Signal(str, str)      # code, detail

    def __init__(
        self,
        phase_manager,
        queue_manager,
        worker_manager,
        task_service,
        chat_view,
        parent=None,
    ):
        super().__init__(parent)
        self._phase_manager = phase_manager
        self._qm = queue_manager
        self._wm = worker_manager
        self._task_service = task_service
        self._chat_view = chat_view

        self._flow_active = False
        self._current_session = ""
        self._phase_task_list = []
        self._phase_results = []
        self._connect_phase_signals()

    # ── 属性 ──────────────────────────────────────
    @property
    def current_session(self) -> str:
        return self._current_session

    @current_session.setter
    def current_session(self, value: str):
        self._current_session = value

    @property
    def is_flow_active(self) -> bool:
        return self._flow_active

    # ── 工作流入口 ────────────────────────────────
    def start_flow(self, session_id: str, user_text: str, mode: str, context: str):
        """启动 Phase 工作流"""
        if self._flow_active:
            logger.warning("Flow already active for %s, ignoring start", session_id)
            return

        self._current_session = session_id
        self._flow_active = True
        self._phase_results = []
        logger.info("Starting flow for session: %s", session_id)

        # 启动 PhaseManager
        self._phase_manager.start(user_text, mode, context)

    def on_user_confirm(self, session_id: str, confirmed: bool = True):
        """用户确认任务清单"""
        if session_id != self._current_session:
            logger.warning("Confirm from wrong session: %s != %s", session_id, self._current_session)
            return
        if self._flow_active:
            self._phase_manager.on_user_confirm(confirmed)

    def on_user_reanalyze(self, session_id: str):
        """用户要求重新分析"""
        if session_id != self._current_session:
            logger.warning("Reanalyze from wrong session: %s != %s", session_id, self._current_session)
            return
        if self._flow_active:
            ctx = self._phase_manager.current_context()
            self._phase_manager.reset()
            self._phase_manager.start(ctx.user_text, ctx.mode, ctx.context)

    def on_user_skip_verify(self, session_id: str):
        """用户跳过验证"""
        if session_id != self._current_session:
            logger.warning("Skip verify from wrong session: %s != %s", session_id, self._current_session)
            return
        if self._flow_active:
            self._phase_manager.on_verify_complete(True, "用户跳过验证")

    def reset(self):
        """重置协调器状态"""
        self._flow_active = False
        self._phase_task_list = []
        self._phase_results = []
        self._phase_manager.reset()

    # ── 内部 ──────────────────────────────────────
    def _connect_phase_signals(self):
        """连接 PhaseManager 信号到内部处理"""
        self._phase_manager.phase_changed.connect(self._on_phase_changed)
        self._phase_manager.analyze_required.connect(self._on_analyze_required)
        self._phase_manager.confirm_required.connect(self._on_confirm_required)
        self._phase_manager.execute_required.connect(self._on_execute_required)
        self._phase_manager.verify_required.connect(self._on_verify_required)
        self._phase_manager.archive_required.connect(self._on_archive_required)
        self._phase_manager.flow_finished.connect(self._on_flow_finished)
        self._phase_manager.error_occurred.connect(self._on_phase_error)

    @Slot(str, str)
    def _on_phase_changed(self, phase: str, mode: str):
        """Phase 变化 → 更新 UI"""
        self.phase_ui_update.emit(phase, len(self._phase_task_list))
        logger.debug("Phase changed: %s", phase)

    @Slot(str, str, str)
    def _on_analyze_required(self, user_text: str, mode: str, context: str):
        """Analyze 阶段 → 请求 Worker 分析"""
        self._chat_view.append_phase_message("analyze", "正在分析需求...")
        # Worker 创建和请求由 MainWindow 的 _ensure_phase_worker 处理
        # 这里只发射信号，由 MainWindow 响应
        self.worker_analysis_requested.emit(user_text, context)

    @Slot(list)
    def _on_confirm_required(self, task_list):
        """Confirm 阶段 → 显示任务清单"""
        self._phase_task_list = list(task_list)
        self._chat_view.set_phase_indicator("confirm", len(self._phase_task_list))
        self._chat_view.append_phase_message("confirm", "请确认以下任务清单")
        self._chat_view.show_confirmation(self._phase_task_list)
        self.phase_ui_update.emit("confirm", len(self._phase_task_list))

    @Slot(list)
    def _on_execute_required(self, task_list):
        """Execute 阶段 → 请求 Worker 执行"""
        self._phase_task_list = list(task_list)
        self._chat_view.hide_confirmation()
        self._chat_view.append_phase_message("execute", "开始执行任务")
        self.phase_ui_update.emit("execute", len(self._phase_task_list))
        # 由 MainWindow 的 Worker 执行
        self.worker_execution_requested.emit(task_list)

    @Slot(list, str)
    def _on_verify_required(self, execution_results, mode: str):
        """Verify 阶段 → 请求 Worker 验证"""
        self._chat_view.append_phase_message("verify", "正在验证执行结果...")
        self._chat_view.show_skip_verify()
        self.phase_ui_update.emit("verify", len(self._phase_task_list))
        self.worker_verification_requested.emit(execution_results)

    @Slot(str)
    def _on_archive_required(self, mode: str):
        """Archive 阶段 → 任务收尾"""
        self._chat_view.append_phase_message("archive", "任务收尾")
        self._chat_view.hide_skip_verify()
        self.phase_ui_update.emit("archive", 0)
        # 调用 PhaseManager 完成
        self._phase_manager.on_archive_complete(True, "工作流完成")

    @Slot(bool, str)
    def _on_flow_finished(self, success: bool, message: str):
        """唯一完成路径：更新状态 → mark_current_done → 停止 Worker"""
        session_id = self._current_session
        logger.info("Flow finished for %s: success=%s, message=%s", session_id, success, message)

        # 状态更新统一由 TaskService 权威处理；本协调器只负责流程收尾与 UI 通知。

        # 标记队列完成
        self._qm.mark_current_done()

        # 重置状态
        self._flow_active = False
        self._chat_view.clear_phase_ui()

        if not success:
            self._chat_view.append_system(f"⚠️ {message}")

        self.flow_completed.emit(session_id, success, message)

    @Slot(str, str)
    def _on_phase_error(self, code: str, detail: str):
        """Phase 错误 → 走同一完成路径"""
        logger.error("Phase error: %s - %s", code, detail)
        self._chat_view.append_system(f"❌ Phase 错误 [{code}]: {detail}")
        self._on_flow_finished(False, detail)
        self.worker_error.emit(code, detail)

    # 额外的信号用于 Worker 通信
    worker_analysis_requested = Signal(str, str)
    worker_execution_requested = Signal(list)
    worker_verification_requested = Signal(list)
