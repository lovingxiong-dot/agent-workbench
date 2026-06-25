"""
BaseWorker — Agent 任务 Worker 的抽象基类

提供生产级生命周期管理：
- 取消令牌（threading.Event）
- 任务总超时熔断
- 统一信号规范
- 异常捕获与错误上报

子类需实现：
    async def _process(self) -> None

信号约定：
- chunk_ready(str): 流式文本片段
- result_ready(str): 最终完整结果
- error_occurred(str, str): (error_code, detail)
- log_message(str): 日志文本
- task_created(str, str): (task_id, description)
- task_finished(str, str): (task_id, result_summary)
- token_used(str, str, int, int): (provider, model, input_tokens, output_tokens)
- confirm_required(str, str): (tool_name, command)
- round_advanced(int): 当前 ReAct 轮次
"""
import asyncio
import threading
import uuid
from abc import abstractmethod
from datetime import datetime
from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    # 文本/结果
    chunk_ready = Signal(str)
    result_ready = Signal(str)
    error_occurred = Signal(str, str)
    log_message = Signal(str)

    # 任务/进度
    task_created = Signal(str, str)
    task_finished = Signal(str, str)
    round_advanced = Signal(int)

    # 资源/确认
    token_used = Signal(str, str, int, int)
    confirm_required = Signal(str, str)

    def __init__(self, session_id: str, task_timeout: float = 120.0):
        super().__init__()
        self.worker_id = uuid.uuid4().hex[:8]
        self.session_id = session_id
        self.task_timeout = max(1.0, float(task_timeout))
        self._cancel_event = threading.Event()
        self._error_code = None
        self._error_detail = None

    # ═══════════════════════════════════════════════════════
    # 取消与超时控制
    # ═══════════════════════════════════════════════════════
    def stop(self):
        """请求取消当前任务（软取消）"""
        self._cancel_event.set()
        self.log_message.emit("[STOP] 用户请求取消任务")

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def _check_cancelled(self):
        """供 _process() 内部调用，主动检查取消状态"""
        if self._cancel_event.is_set():
            raise WorkerCancelledError("任务已被用户取消")

    def _report_error(self, code: str, detail: str):
        """记录错误并在结果中返回"""
        self._error_code = code
        self._error_detail = detail
        self.log_message.emit(f"[ERR:{code}] {detail}")
        self.error_occurred.emit(code, detail)

    # ═══════════════════════════════════════════════════════
    # QThread 入口
    # ═══════════════════════════════════════════════════════
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run_with_timeout())
        except Exception as ex:
            self._report_error("WORKER_RUNTIME", str(ex))
            self.result_ready.emit(f"Error: {str(ex)}")
        finally:
            loop.close()

    async def _run_with_timeout(self):
        """带总超时的任务执行包装"""
        start_at = datetime.now()
        try:
            await asyncio.wait_for(self._process(), timeout=self.task_timeout)
        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start_at).total_seconds()
            self._report_error("TASK_TIMEOUT", f"任务执行超过 {self.task_timeout} 秒（已运行 {elapsed:.1f} 秒）")
            self.result_ready.emit(f"Error: 任务超时（>{self.task_timeout}s），请简化请求或重试。")
        except WorkerCancelledError:
            self.result_ready.emit("[已取消]")
        except Exception as ex:
            self._report_error("PROCESS_ERROR", str(ex))
            self.result_ready.emit(f"Error: {str(ex)}")

    # ═══════════════════════════════════════════════════════
    # 子类必须实现
    # ═══════════════════════════════════════════════════════
    @abstractmethod
    async def _process(self) -> None:
        """子类实现具体的 Agent 执行逻辑"""
        raise NotImplementedError


class WorkerCancelledError(Exception):
    """用户主动取消任务时抛出"""
    pass
