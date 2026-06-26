"""
AgentWorker — AgentSession 的 QThread 载体

v3.8 改造后，AgentWorker 不再每阶段新建 Orchestrator，
而是在整个 Phase 流程（Analyze → Confirm → Execute → Verify → Archive）中复用同一个 AgentSession。

MainWindow 通过 Signal 向 Worker 发送 Phase 请求：
  - request_analyze(user_text, context)
  - request_execute(task_list, original_text, context)
  - request_verify(execution_results, local_details, context)

Worker 内部在同一个 asyncio 事件循环中顺序执行，消除确认阶段重建开销。
"""
import asyncio
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal
from langchain_core.messages import HumanMessage

from agent_engine.agent_session import AgentSession, TaskItem
from agent_engine.orchestrator import OrchestratorCancelledError
from services.metrics_collector import MetricsCollector
from tools import system as system_tools, ARUN_MAP
from tools.external_apis import set_cpu_executor as set_external_cpu_executor
from tools.quant import set_cpu_executor as set_quant_cpu_executor

# Tiered tool definitions with explicit priority hints
TOOL_DEFINITIONS = [
    {"type":"function","function":{"name":"web_fetch","description":"[PRIORITY-1] Fetch webpage content as text summary. USE FIRST for: prices, weather, news, facts, general queries. NOT for stocks or economic data.","parameters":{"type":"object","properties":{"url":{"type":"string","description":"URL to fetch"}},"required":["url"]}}},
    {"type":"function","function":{"name":"fetch_financial_news","description":"[PRIORITY-1] Get financial news headlines. Use for market news, hot topics.","parameters":{"type":"object","properties":{"query":{"type":"string","description":"Search keyword"},"limit":{"type":"number","description":"Default 5"}},"required":[]}}},
    {"type":"function","function":{"name":"fetch_macro_data","description":"[PRIORITY-1] Get CPI/GDP/PMI economic data. Use ONLY when user asks for these specific indicators.","parameters":{"type":"object","properties":{"indicator":{"type":"string","description":"cpi, gdp, or pmi"}},"required":["indicator"]}}},
    {"type":"function","function":{"name":"fetch_stock_data","description":"[PRIORITY-1] Get stock OHLCV history (A-share/HK/US). Use for stock price, trend, charts.","parameters":{"type":"object","properties":{"ticker":{"type":"string","description":"e.g. 000001, AAPL"},"start_date":{"type":"string"},"end_date":{"type":"string"}},"required":["ticker"]}}},
    {"type":"function","function":{"name":"read_file","description":"[PRIORITY-2] Read text file (first 5000 chars). Use to view file contents.","parameters":{"type":"object","properties":{"path":{"type":"string","description":"File path"},"encoding":{"type":"string","description":"Default utf-8"}},"required":["path"]}}},
    {"type":"function","function":{"name":"list_dir","description":"[PRIORITY-2] List directory contents. Use to browse folders.","parameters":{"type":"object","properties":{"path":{"type":"string","description":"Directory path"}},"required":[]}}},
    {"type":"function","function":{"name":"run_command","description":"[PRIORITY-2] Execute shell command or launch program. Use for: opening apps, running scripts.","parameters":{"type":"object","properties":{"command":{"type":"string","description":"Command"}},"required":["command"]}}},
    {"type":"function","function":{"name":"clipboard_read","description":"[PRIORITY-2] Read Windows clipboard text.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"clipboard_write","description":"[PRIORITY-2] Write text to Windows clipboard.","parameters":{"type":"object","properties":{"text":{"type":"string","description":"Text"}},"required":["text"]}}},
    {"type":"function","function":{"name":"send_notification","description":"[PRIORITY-2] Windows desktop toast notification.","parameters":{"type":"object","properties":{"title":{"type":"string"},"message":{"type":"string"}},"required":["title"]}}},
    {"type":"function","function":{"name":"mt5_get_price","description":"[PRIORITY-3-MT5] Get MetaTrader5 forex/commodity bid-ask spread. ONLY use when user says 'MT5', 'forex', or specifies currency pair like EURUSD/XAUUSD. For gold/oil GENERAL prices use web_fetch instead.","parameters":{"type":"object","properties":{"symbol":{"type":"string","description":"Symbol e.g. EURUSD, XAUUSD"}},"required":["symbol"]}}},
    {"type":"function","function":{"name":"mt5_place_order","description":"[PRIORITY-3-MT5] Place trade order via MetaTrader5 (needs confirmation). ONLY use for explicit trading: 'order', 'buy', 'sell', 'open position'.","parameters":{"type":"object","properties":{"symbol":{"type":"string"},"volume":{"type":"number"},"order_type":{"type":"string","description":"buy or sell"}},"required":["symbol","volume","order_type"]}}},
    {"type":"function","function":{"name":"run_backtest","description":"[PRIORITY-3-QUANT] Run strategy backtest. ONLY use when user says 'backtest', 'strategy', or 'historical simulation'.","parameters":{"type":"object","properties":{"strategy_code":{"type":"string"}},"required":["strategy_code"]}}},
    {"type":"function","function":{"name":"write_file","description":"[PRIORITY-3-DESTRUCTIVE] Overwrite file. ONLY use when user says 'save', 'write', 'create file', 'export'.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"},"encoding":{"type":"string","description":"Default utf-8"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"run_as_admin","description":"[PRIORITY-3-DESTRUCTIVE] Run command as admin (UAC popup). ONLY use for 'admin', 'sudo', 'elevated'.","parameters":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}},
    {"type":"function","function":{"name":"kill_process","description":"[PRIORITY-3-DESTRUCTIVE] Terminate process (needs confirmation). ONLY use when user says 'kill', 'stop', 'terminate'.","parameters":{"type":"object","properties":{"name":{"type":"string","description":"e.g. notepad.exe"}},"required":["name"]}}},
    {"type":"function","function":{"name":"list_processes","description":"[PRIORITY-3-UTIL] List running processes by memory. Use for system status.","parameters":{"type":"object","properties":{},"required":[]}}},
]


class AgentWorker(QThread):
    # 文本/结果
    chunk_ready = Signal(str)
    result_ready = Signal(str)
    error_occurred = Signal(str, str)
    log_message = Signal(str)

    # 任务/进度
    task_created = Signal(str, str)
    task_finished = Signal(str, str)
    round_advanced = Signal(int)

    # 资源/指标
    token_used = Signal(str, str, int, int)
    turn_metrics_ready = Signal(object)

    # 敏感操作确认
    confirm_required = Signal(str, str)

    # 工具执行回传（共享输出面板）
    tool_executed = Signal(str, dict, str, int)  # name, args, result, elapsed_ms

    # Phase 结果
    analyze_result_ready = Signal(list)  # List[TaskItem]
    execute_result_ready = Signal(str)
    verify_result_ready = Signal(str)

    def __init__(
        self,
        mode_name: str,
        current_llm,
        current_tools: Optional[List[str]] = None,
        session_id: str = "",
        system_prompt: str = "",
        tool_map: Optional[Dict[str, Any]] = None,
        tool_definitions: Optional[List[Dict]] = None,
        enable_streaming: bool = True,
        user_rules: Optional[List[str]] = None,
        max_tool_rounds: int = 8,
        task_timeout: float = 120.0,
        project_root: str = "",
        workspace_context: str = "",
        app_version: str = "v3.x",
        llm_timeout: float = 90.0,
        tool_timeout: float = 30.0,
    ):
        super().__init__()
        import uuid
        self.worker_id = uuid.uuid4().hex[:8]
        self.session_id = session_id or self.worker_id
        self.task_timeout = max(1.0, float(task_timeout))
        self._cancel_event = threading.Event()
        self._error_code = None
        self._error_detail = None
        self._cpu_executor: Optional[ThreadPoolExecutor] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._session: Optional[AgentSession] = None
        self._loop_ready = threading.Event()
        self._pending_requests: List[tuple] = []

        self.mode_name = mode_name
        self.current_llm = current_llm
        self.current_tools = current_tools or []
        self.system_prompt = system_prompt
        self.tool_map = tool_map or {}
        self.tool_definitions = tool_definitions or []
        self.enable_streaming = enable_streaming
        self.user_rules = user_rules or []
        self.max_tool_rounds = max(1, int(max_tool_rounds)) if max_tool_rounds else 8
        self.project_root = project_root or ""
        self.workspace_context = workspace_context or ""
        self.app_version = app_version or "v3.x"
        self.llm_timeout = max(5.0, float(llm_timeout or 90.0))
        self.tool_timeout = max(5.0, float(tool_timeout or 30.0))
        self.metrics = MetricsCollector()

    # ═══════════════════════════════════════════════════════
    # 公共 Phase 请求接口（由 MainWindow 在主线程调用）
    # ═══════════════════════════════════════════════════════
    def request_analyze(self, user_text: str, context: str):
        if not self._loop_ready.is_set() or self._loop is None:
            self._pending_requests.append(("analyze", user_text, context))
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._run_analyze(user_text, context), self._loop
            )
        except Exception as e:
            print(f"[DIAG-WORKER {self.worker_id}] request_analyze error: {e}", flush=True)
            traceback.print_exc()

    def request_execute(self, task_list: List[TaskItem], original_text: str, context: str):
        if not self._loop_ready.is_set() or self._loop is None:
            self._pending_requests.append(("execute", task_list, original_text, context))
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._run_execute(task_list, original_text, context), self._loop
            )
        except Exception as e:
            print(f"[DIAG-WORKER {self.worker_id}] request_execute error: {e}", flush=True)
            traceback.print_exc()

    def request_verify(self, execution_results: List[dict], local_details: str, context: str):
        if not self._loop_ready.is_set() or self._loop is None:
            self._pending_requests.append(("verify", execution_results, local_details, context))
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._run_verify(execution_results, local_details, context), self._loop
            )
        except Exception as e:
            print(f"[DIAG-WORKER {self.worker_id}] request_verify error: {e}", flush=True)
            traceback.print_exc()

    def set_confirm_result(self, confirmed: bool):
        """MainWindow 在用户确认/取消后调用"""
        if self._session is not None:
            self._session.set_confirm_result(confirmed)

    def stop(self):
        """请求取消当前任务并结束 Worker 事件循环（工作流结束时调用）"""
        self._cancel_event.set()
        self.log_message.emit("[STOP] 用户请求取消任务")
        if self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception as e:
                print(f"[DIAG-WORKER {self.worker_id}] stop error: {e}", flush=True)

    def cancel_phase(self):
        """仅取消当前 Phase，不结束 Worker 事件循环（用户点击停止按钮时调用）"""
        self._cancel_event.set()
        # 若当前正在等待危险命令确认，直接视为取消，避免卡住
        if self._session is not None:
            self._session.set_confirm_result(False)
        self.log_message.emit("[STOP] 用户请求停止当前阶段")

    def reset_cancel(self):
        """新一轮 Phase 开始前重置取消标志"""
        self._cancel_event.clear()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # ═══════════════════════════════════════════════════════
    # QThread 入口
    # ═══════════════════════════════════════════════════════
    def run(self):
        print(f"[DIAG-WORKER {self.worker_id}] run() start", flush=True)
        try:
            self._cpu_executor = ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix=f"cpu_{self.worker_id}_",
            )
            print(f"[DIAG-WORKER {self.worker_id}] ThreadPoolExecutor created", flush=True)
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            print(f"[DIAG-WORKER {self.worker_id}] asyncio loop created", flush=True)

            # 注入 CPU/同步任务线程池到需要显式 executor 的 async 工具模块
            set_external_cpu_executor(self._cpu_executor)
            set_quant_cpu_executor(self._cpu_executor)

            # 同步 project_root 到文件工具模块
            if self.project_root and hasattr(system_tools, "set_project_root"):
                system_tools.set_project_root(self.project_root)

            # 创建跨 Phase 复用的 AgentSession
            print(f"[DIAG-WORKER {self.worker_id}] creating AgentSession...", flush=True)
            self._session = AgentSession(
                llm=self.current_llm,
                tool_map=self.tool_map,
                tool_definitions=self.tool_definitions or TOOL_DEFINITIONS,
                mode=self.mode_name,
                project_root=self.project_root,
                system_prompt=self.system_prompt,
                user_rules=self.user_rules,
                max_tool_rounds=self.max_tool_rounds,
                app_version=self.app_version,
                llm_timeout=self.llm_timeout,
                tool_timeout=self.tool_timeout,
                workspace_context=self.workspace_context,
                cpu_executor=self._cpu_executor,
                arun_map=ARUN_MAP,
            )
            print(f"[DIAG-WORKER {self.worker_id}] AgentSession created", flush=True)
            self._connect_session_signals()

            # 事件循环与 AgentSession 已就绪
            self._loop_ready.set()
            print(f"[DIAG-WORKER {self.worker_id}] loop_ready=True", flush=True)

            # 把缓存请求 flush 作为第一个回调调度到事件循环内部执行
            self._loop.call_soon(self._flush_pending_requests)

            print(f"[DIAG-WORKER {self.worker_id}] entering run_forever()", flush=True)
            self._loop.run_forever()
            print(f"[DIAG-WORKER {self.worker_id}] run_forever() returned normally", flush=True)
        except Exception as ex:
            print(f"[DIAG-WORKER {self.worker_id}] run() exception: {ex}", flush=True)
            traceback.print_exc()
            self._report_error("WORKER_RUNTIME", str(ex))
        finally:
            print(f"[DIAG-WORKER {self.worker_id}] cleanup start", flush=True)
            self._cleanup()
            print(f"[DIAG-WORKER {self.worker_id}] cleanup done", flush=True)

    # ═══════════════════════════════════════════════════════
    # async Phase 执行体
    # ═══════════════════════════════════════════════════════
    async def _run_analyze(self, user_text: str, context: str):
        print(f"[DIAG-WORKER {self.worker_id}] _run_analyze started", flush=True)
        self.reset_cancel()
        try:
            self.metrics.start_turn()
            print(f"[DIAG-WORKER {self.worker_id}] calling session.run_analyze...", flush=True)
            task_list = await asyncio.wait_for(
                self._session.run_analyze(user_text, context, cancel_event=self._cancel_event),
                timeout=self.task_timeout,
            )
            print(f"[DIAG-WORKER {self.worker_id}] session.run_analyze returned {len(task_list)} tasks", flush=True)
            self.analyze_result_ready.emit(task_list)
        except asyncio.TimeoutError:
            self._report_error("TASK_TIMEOUT", f"Analyze 阶段超过 {self.task_timeout} 秒")
        except OrchestratorCancelledError:
            self.result_ready.emit("[已取消]")
        except Exception as ex:
            print(f"[DIAG-WORKER {self.worker_id}] _run_analyze exception: {ex}", flush=True)
            traceback.print_exc()
            self._report_error("ANALYZE_ERROR", str(ex))
        print(f"[DIAG-WORKER {self.worker_id}] _run_analyze ended", flush=True)

    async def _run_execute(self, task_list: List[TaskItem], original_text: str, context: str):
        self.reset_cancel()
        try:
            self.metrics.start_turn()
            text = await asyncio.wait_for(
                self._session.run_execute(task_list, original_text, context, cancel_event=self._cancel_event),
                timeout=self.task_timeout,
            )
            self.execute_result_ready.emit(text)
        except asyncio.TimeoutError:
            self._report_error("TASK_TIMEOUT", f"Execute 阶段超过 {self.task_timeout} 秒")
        except OrchestratorCancelledError:
            self.result_ready.emit("[已取消]")
        except Exception as ex:
            self._report_error("EXECUTE_ERROR", str(ex))

    async def _run_verify(self, execution_results: List[dict], local_details: str, context: str):
        self.reset_cancel()
        try:
            self.metrics.start_turn()
            text = await asyncio.wait_for(
                self._session.run_verify(execution_results, local_details, context, cancel_event=self._cancel_event),
                timeout=self.task_timeout,
            )
            self.verify_result_ready.emit(text)
        except asyncio.TimeoutError:
            self._report_error("TASK_TIMEOUT", f"Verify 阶段超过 {self.task_timeout} 秒")
        except OrchestratorCancelledError:
            self.result_ready.emit("[已取消]")
        except Exception as ex:
            self._report_error("VERIFY_ERROR", str(ex))

    # ═══════════════════════════════════════════════════════
    # 信号连接与转发
    # ═══════════════════════════════════════════════════════
    def _flush_pending_requests(self):
        """事件循环就绪后，把启动前缓存的 Phase 请求一次性提交到 Worker 线程"""
        print(f"[DIAG-WORKER {self.worker_id}] _flush_pending_requests called", flush=True)
        if not self._pending_requests or self._loop is None:
            print(f"[DIAG-WORKER {self.worker_id}] nothing to flush", flush=True)
            return
        flushed = self._pending_requests[:]
        self._pending_requests.clear()
        print(f"[DIAG-WORKER {self.worker_id}] flushing {len(flushed)} requests", flush=True)
        for req in flushed:
            kind = req[0]
            try:
                if kind == "analyze":
                    asyncio.run_coroutine_threadsafe(
                        self._run_analyze(req[1], req[2]), self._loop
                    )
                elif kind == "execute":
                    asyncio.run_coroutine_threadsafe(
                        self._run_execute(req[1], req[2], req[3]), self._loop
                    )
                elif kind == "verify":
                    asyncio.run_coroutine_threadsafe(
                        self._run_verify(req[1], req[2], req[3]), self._loop
                    )
            except Exception as e:
                print(f"[DIAG-WORKER {self.worker_id}] flush request error: {e}", flush=True)
                traceback.print_exc()

    def _connect_session_signals(self):
        session = self._session
        session.chunk_ready.connect(self.chunk_ready.emit)
        session.result_ready.connect(self.result_ready.emit)
        session.tool_executed.connect(self.tool_executed.emit)
        session.token_used.connect(self._on_token_usage)
        session.turn_metrics_ready.connect(self.turn_metrics_ready.emit)
        session.confirm_required.connect(self.confirm_required.emit)
        session.error_occurred.connect(self.error_occurred.emit)
        session.log_message.connect(self.log_message.emit)
        session.task_created.connect(self.task_created.emit)
        session.task_finished.connect(self.task_finished.emit)
        session.round_advanced.connect(self.round_advanced.emit)

    def _on_token_usage(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        try:
            metrics = self.metrics.finish_turn(input_tokens, output_tokens)
            self.token_used.emit(provider, model, input_tokens, output_tokens)
            self.turn_metrics_ready.emit(metrics)
        except Exception as e:
            self.log_message.emit(f"[WARN] metrics collection failed: {e}")

    # ═══════════════════════════════════════════════════════
    # 错误与清理
    # ═══════════════════════════════════════════════════════
    def _report_error(self, code: str, detail: str):
        self._error_code = code
        self._error_detail = detail
        self.log_message.emit(f"[ERR:{code}] {detail}")
        self.error_occurred.emit(code, detail)

    async def _process(self):
        """BaseWorker 抽象方法占位：AgentWorker 使用自定义 run() 驱动 AgentSession"""
        pass

    def _cleanup(self):
        self._loop_ready.clear()
        self._pending_requests.clear()
        if self._session is not None:
            try:
                self._session.deleteLater()
            except Exception as e:
                print(f"[DIAG-WORKER {self.worker_id}] session deleteLater error: {e}", flush=True)
            self._session = None
        if self._cpu_executor is not None:
            try:
                if self._cancel_event.is_set():
                    self._cpu_executor.shutdown(wait=False, cancel_futures=True)
                else:
                    self._cpu_executor.shutdown(wait=True)
            except Exception as e:
                print(f"[DIAG-WORKER {self.worker_id}] executor shutdown error: {e}", flush=True)
            self._cpu_executor = None
        if self._loop is not None:
            try:
                self._loop.close()
            except Exception as e:
                print(f"[DIAG-WORKER {self.worker_id}] loop close error: {e}", flush=True)
        self._loop = None
