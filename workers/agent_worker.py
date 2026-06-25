import json
import asyncio
import threading
from datetime import datetime
from langchain_core.messages import HumanMessage

from workers.base_worker import BaseWorker, WorkerCancelledError
from agent_engine.orchestrator import AgentOrchestrator
from services.metrics_collector import MetricsCollector
from tools import system as system_tools

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
    {"type":"function","function":{"name":"kill_process","description":"[PRIORITY-3-DESTRUCTIVE] Terminate process (needs confirmation). ONLY use for 'kill', 'stop', 'terminate'.","parameters":{"type":"object","properties":{"name":{"type":"string","description":"e.g. notepad.exe"}},"required":["name"]}}},
    {"type":"function","function":{"name":"list_processes","description":"[PRIORITY-3-UTIL] List running processes by memory. Use for system status.","parameters":{"type":"object","properties":{},"required":[]}}},
]

DANGEROUS_KEYWORDS = [
    "del ", "delete", "rm -", "rd /s", "rmdir /s", "format ",
    "mkfs", "shutdown", "reg delete", "reg add", "diskpart",
]


class AgentWorker(BaseWorker):
    def __init__(self, user_text, mode_name, current_llm, current_tools,
                 session_id, system_prompt="", tool_map=None, tool_definitions=None,
                 enable_streaming=True, chat_history=None, user_rules=None,
                 max_tool_rounds=8, task_timeout=120.0, project_root="",
                 workspace_context=""):
        super().__init__(session_id=session_id, task_timeout=task_timeout)
        self.user_text = user_text
        self.mode_name = mode_name
        self.current_llm = current_llm
        self.current_tools = current_tools or []
        self.system_prompt = system_prompt
        self.tool_map = tool_map or {}
        self.tool_definitions = tool_definitions or []
        self.enable_streaming = enable_streaming
        self.chat_history = chat_history or []
        self.user_rules = user_rules or []
        self.max_tool_rounds = max(1, int(max_tool_rounds)) if max_tool_rounds else 8
        self.project_root = project_root or ""
        self.workspace_context = workspace_context or ""
        self.confirm_event = threading.Event()
        self.confirm_result = False
        self.metrics = MetricsCollector()

    async def _process(self):
        """AgentWorker 现在只是 Orchestrator 的薄封装：负责生命周期和信号转换。"""
        try:
            # 同步 project_root 到文件工具模块
            if self.project_root and hasattr(system_tools, "set_project_root"):
                system_tools.set_project_root(self.project_root)

            orchestrator = AgentOrchestrator(
                llm=self.current_llm,
                tool_map=self.tool_map,
                tool_definitions=self.tool_definitions,
                system_prompt=self.system_prompt,
                user_rules=self.user_rules,
                max_tool_rounds=self.max_tool_rounds,
                enable_streaming=self.enable_streaming,
                tool_executor=self._sync_call_tool,
                workspace_context=self.workspace_context,
            )

            callbacks = {
                "log": self.log_message.emit,
                "tool_start": self.task_created.emit,
                "tool_end": self.task_finished.emit,
                "chunk": self._emit_chunk_with_first_token,
                "round": self.round_advanced.emit,
                "metrics_start": self.metrics.start_turn,
                "metrics_first_token": self.metrics.mark_first_token,
                "token_usage": self._on_token_usage,
                "error": lambda code, detail: self._report_error(code, detail),
            }

            final_text = await orchestrator.run(
                user_input=self.user_text,
                chat_history=self.chat_history,
                callbacks=callbacks,
                cancel_event=self._cancel_event,
            )
            self.result_ready.emit(final_text)

        except WorkerCancelledError:
            self.log_message.emit("[STOP] 任务已取消")
            raise
        except Exception as ex:
            self._report_error("AGENT_PROCESS", str(ex))
            self.result_ready.emit(f"Error: {str(ex)}")

    def _emit_chunk_with_first_token(self, chunk: str):
        """转发 chunk，并在第一次时标记首 token 时间"""
        self.metrics.mark_first_token()
        self.chunk_ready.emit(chunk)

    def _on_token_usage(self, usage: dict):
        """收到最终 token 用量后：完成本轮指标并发出信号"""
        try:
            input_tokens = int(usage.get("input_tokens", 0) or 0)
            output_tokens = int(usage.get("output_tokens", 0) or 0)
            metrics = self.metrics.finish_turn(input_tokens, output_tokens)

            provider = usage.get("provider") or ""
            model = str(self.current_llm.model) if hasattr(self.current_llm, "model") else ""
            self.token_used.emit(provider, model, input_tokens, output_tokens)
            self.turn_metrics_ready.emit(metrics)
        except Exception as e:
            # 指标收集失败不应中断主流程
            self.log_message.emit(f"[WARN] metrics collection failed: {e}")

    def _sync_call_tool(self, name, args):
        tool_func = self.tool_map.get(name)
        if not tool_func:
            return f"Tool {name} not found"
        try:
            if isinstance(args, str):
                args = json.loads(args)
            if name in ("run_command", "run_as_admin"):
                command = args.get("command", "") if isinstance(args, dict) else str(args)
                if self._is_dangerous(command):
                    self.confirm_result = False  # 每次确认前重置
                    self.confirm_required.emit(name, command)
                    self.confirm_event.wait()
                    confirmed = self.confirm_result
                    self.confirm_result = False  # 使用后重置
                    if not confirmed:
                        return "User cancelled sensitive operation"
            return tool_func.run(args)
        except Exception as e:
            return f"Tool error: {str(e)}"

    def _is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in DANGEROUS_KEYWORDS)
