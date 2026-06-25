import json
import asyncio
import threading
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

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


class AgentWorker(QThread):
    chunk_ready = Signal(str)
    result_ready = Signal(str)
    log_message = Signal(str)
    task_created = Signal(str, str)
    task_finished = Signal(str, str)
    confirm_required = Signal(str, str)
    token_used = Signal(str, str, int, int)

    def __init__(self, user_text, mode_name, current_llm, current_tools,
                 session_id, system_prompt="", tool_map=None, tool_definitions=None,
                 enable_streaming=True, chat_history=None, user_rules=None):
        super().__init__()
        self.user_text = user_text
        self.mode_name = mode_name
        self.current_llm = current_llm
        self.current_tools = current_tools or []
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.tool_map = tool_map or {}
        self.tool_definitions = tool_definitions or []
        self.enable_streaming = enable_streaming
        self.chat_history = chat_history or []
        self.user_rules = user_rules or []
        self.confirm_event = threading.Event()
        self.confirm_result = False
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process())
        finally:
            loop.close()

    async def _process(self):
        prompt = self.system_prompt or "You are a helpful AI assistant."
        model_id = str(self.current_llm.model) if hasattr(self.current_llm, 'model') else "unknown"
        prompt += f"\n\n## YOUR IDENTITY\nYou are AI Agent Workbench v2 running on model '{model_id}'. When asked who/what model you are, state: 'I am AI Agent Workbench v2, powered by {model_id}.' Never claim to be Claude, GPT, Gemini, or any other brand."
        if self.user_rules:
            rule_lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(self.user_rules))
            prompt += f"\n\n## USER RULES (MUST FOLLOW)\n{rule_lines}"
        system_msg = SystemMessage(content=prompt)
        messages = [system_msg] + list(self.chat_history) + [HumanMessage(content=self.user_text)]

        try:
            allowed_defs = [d for d in self.tool_definitions if d["function"]["name"] in self.current_tools]
            model_name = str(self.current_llm.model) if hasattr(self.current_llm, 'model') else ""
            skip_tools = any(m in model_name for m in ("gemma2", "gemma:"))
            llm = self.current_llm.bind_tools(allowed_defs) if (allowed_defs and not skip_tools) else self.current_llm

            response = await llm.ainvoke(messages)

            if hasattr(response, "tool_calls") and response.tool_calls:
                self.log_message.emit(f"[TOOL] Calling: {[tc['name'] for tc in response.tool_calls]}")
                response.content = ""
                messages.append(response)

                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    task_id = f"{tool_name}_{datetime.now().strftime('%H%M%S')}"
                    self.task_created.emit(task_id, f"Running {tool_name}")
                    result = await asyncio.to_thread(self._sync_call_tool, tool_name, tool_args)
                    self.task_finished.emit(task_id, str(result)[:200])
                    self.log_message.emit(f"[OK] {tool_name}")
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

                final_resp = await self.current_llm.ainvoke(messages)
                reply = final_resp.content or ""
                # Fallback: if LLM summary is empty, emit raw tool results
                if not reply:
                    results = [msg.content for msg in messages if isinstance(msg, ToolMessage)]
                    reply = "\n\n".join(results) if results else "[Tool executed]"

                if self.enable_streaming and reply:
                    for line in reply.replace('\r\n', '\n').split('\n'):
                        self.chunk_ready.emit(line + '\n')
                self.result_ready.emit(reply.strip() if reply else "[Tool executed]")
            else:
                reply = response.content or ""
                if self.enable_streaming and reply:
                    for line in reply.replace('\r\n', '\n').split('\n'):
                        if self._stop_flag:
                            break
                        self.chunk_ready.emit(line + '\n')
                self.result_ready.emit(reply.strip())

        except Exception as ex:
            self.result_ready.emit(f"Error: {str(ex)}")
            self.log_message.emit(f"[ERR] {ex}")

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
                    self.confirm_required.emit(name, command)
                    self.confirm_event.wait()
                    if not self.confirm_result:
                        return "User cancelled sensitive operation"
            return tool_func.run(args)
        except Exception as e:
            return f"Tool error: {str(e)}"

    def _is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in DANGEROUS_KEYWORDS)
