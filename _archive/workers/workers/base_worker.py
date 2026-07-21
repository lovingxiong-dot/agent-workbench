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
- turn_metrics_ready(object): TurnMetrics 指标对象（含 token/时间）
- confirm_required(str, str): (tool_name, command)
- round_advanced(int): 当前 ReAct 轮次
"""
import asyncio
import threading
import uuid
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
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
    turn_metrics_ready = Signal(object)
    confirm_required = Signal(str, str)

    # 工具执行回传（共享输出面板）
    tool_executed = Signal(str, dict, str, int)  # name, args, result, elapsed_ms

    def __init__(self, session_id: str, task_timeout: float = 120.0):
        super().__init__()
        self.worker_id = uuid.uuid4().hex[:8]
        self.session_id = session_id
        self.task_timeout = max(1.0, float(task_timeout))
        self._cancel_event = threading.Event()
        self._error_code = None
        self._error_detail = None
        self._cpu_executor = None

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

    def get_cpu_executor(self):
        """返回 CPU/同步任务线程池，供子类/Orchestrator 使用"""
        return self._cpu_executor

    # ═══════════════════════════════════════════════════════
    # QThread 入口
    # ═══════════════════════════════════════════════════════
    def run(self):
        # CPU/同步兜底线程池：仅用于 run_backtest、MT5、akshare 等无法 async 的任务
        self._cpu_executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix=f"cpu_{self.worker_id}_",
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # 注意：不调用 loop.set_default_executor，让原生协程在事件循环中执行
        try:
            loop.run_until_complete(self._run_with_timeout())
        except Exception as ex:
            self._report_error("WORKER_RUNTIME", str(ex))
            self.result_ready.emit(f"Error: {str(ex)}")
        finally:
            loop.close()
            if self._cpu_executor is not None:
                # 用户取消/异常时快速释放；正常结束时等待已提交任务完成
                if self._cancel_event.is_set():
                    self._cpu_executor.shutdown(wait=False, cancel_futures=True)
                else:
                    self._cpu_executor.shutdown(wait=True)
                self._cpu_executor = None

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
