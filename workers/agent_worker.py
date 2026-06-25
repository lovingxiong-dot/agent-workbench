import json
import asyncio
import threading
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# Tool definitions - kept in worker for now
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "以当前权限执行系统命令、启动程序或打开文件/文件夹",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "要执行的命令"}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_as_admin",
            "description": "以管理员权限执行命令（会弹出 UAC 窗口等待用户确认）",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "要执行的命令"}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_stock_data",
            "description": "获取股票历史数据，支持A股/港股/美股",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码，如 000001 或 AAPL"},
                    "start_date": {"type": "string", "description": "开始日期 yyyy-mm-dd"},
                    "end_date": {"type": "string", "description": "结束日期 yyyy-mm-dd"}
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "运行量化策略回测",
            "parameters": {
                "type": "object",
                "properties": {"strategy_code": {"type": "string", "description": "策略代码"}},
                "required": ["strategy_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mt5_get_price",
            "description": "获取 MT5 实时报价",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string", "description": "交易品种"}},
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mt5_place_order",
            "description": "MT5 下单（需二次确认）",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "交易品种"},
                    "volume": {"type": "number", "description": "手数"},
                    "order_type": {"type": "string", "description": "buy/sell"}
                },
                "required": ["symbol", "volume", "order_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_financial_news",
            "description": "获取财经新闻和全球市场快讯",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词（可选，不填则获取全球快讯）"},
                    "limit": {"type": "number", "description": "返回条数，默认5"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_macro_data",
            "description": "获取宏观经济数据：cpi(CPI), gdp(GDP), pmi(PMI)",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "经济指标: cpi, gdp, pmi"}
                },
                "required": ["indicator"]
            }
        }
    },
]

DANGEROUS_KEYWORDS = [
    "del ", "delete", "rm -", "rd /s", "rmdir /s", "format ",
    "mkfs", "shutdown", "reg delete", "reg add", "diskpart",
]


class AgentWorker(QThread):
    """后台 Agent 推理线程，支持流式输出"""
    chunk_ready = Signal(str)          # Streaming chunk
    result_ready = Signal(str)         # Final complete result
    log_message = Signal(str)
    task_created = Signal(str, str)    # task_id, description
    task_finished = Signal(str, str)   # task_id, result
    confirm_required = Signal(str, str) # tool_name, command
    token_used = Signal(str, str, int, int)  # provider, model, input, output

    def __init__(self, user_text, mode_name, current_llm, current_tools,
                 session_id, system_prompt="", tool_map=None, tool_definitions=None,
                 enable_streaming=True):
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
        self.confirm_event = threading.Event()
        self.confirm_result = False
        self._stop_flag = False

    def stop(self):
        """请求停止生成"""
        self._stop_flag = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process())
        finally:
            loop.close()

    async def _process(self):
        system_msg = SystemMessage(content=self.system_prompt or "你是全能 AI 助手。")
        messages = [system_msg, HumanMessage(content=self.user_text)]

        try:
            allowed_defs = [d for d in self.tool_definitions if d["function"]["name"] in self.current_tools]
            llm_with_tools = self.current_llm.bind_tools(allowed_defs) if allowed_defs else self.current_llm

            if self.enable_streaming:
                # Streaming with tool calls support
                full_reply = ""
                async for chunk in llm_with_tools.astream(messages):
                    if self._stop_flag:
                        self.chunk_ready.emit("\n\n[已停止生成]")
                        return
                    if chunk.content:
                        full_reply += chunk.content
                        self.chunk_ready.emit(chunk.content)
                    if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                        input_tokens = chunk.usage_metadata.get('input_tokens', 0)
                        output_tokens = chunk.usage_metadata.get('output_tokens', 0)
                        provider = self.current_llm.model_name if hasattr(self.current_llm, 'model_name') else "unknown"
                        self.token_used.emit(provider, str(self.current_llm.model), input_tokens, output_tokens)

                if full_reply.strip():
                    self.result_ready.emit(full_reply.strip())
                else:
                    # Fallback to non-streaming if streaming produced nothing
                    response = await llm_with_tools.ainvoke(messages)
                    reply = response.content
                    self.result_ready.emit(reply)
            else:
                response = await llm_with_tools.ainvoke(messages)
                
                if hasattr(response, "tool_calls") and response.tool_calls:
                    self.log_message.emit(f"🔧 调用工具: {[tc['name'] for tc in response.tool_calls]}")
                    for tc in response.tool_calls:
                        tool_name = tc["name"]
                        tool_args = tc["args"]
                        task_id = f"{tool_name}_{datetime.now().strftime('%H%M%S')}"
                        self.task_created.emit(task_id, f"执行工具 {tool_name}")
                        result = await asyncio.to_thread(self._sync_call_tool, tool_name, tool_args)
                        self.task_finished.emit(task_id, str(result)[:200])
                        messages.append(AIMessage(content=f"工具 {tool_name} 结果: {result}"))
                        self.log_message.emit(f"✅ {tool_name}")
                    final_response = await self.current_llm.ainvoke(messages)
                    reply = final_response.content
                else:
                    reply = response.content

                self.result_ready.emit(reply)

        except Exception as ex:
            self.result_ready.emit(f"❌ 错误: {str(ex)}")
            self.log_message.emit(f"❌ {ex}")

    def _sync_call_tool(self, name, args):
        tool_func = self.tool_map.get(name)
        if not tool_func:
            return f"工具 {name} 不存在"
        try:
            if isinstance(args, str):
                args = json.loads(args)
            if name in ("run_command", "run_as_admin"):
                command = args.get("command", "") if isinstance(args, dict) else str(args)
                if self._is_dangerous(command):
                    self.confirm_required.emit(name, command)
                    self.confirm_event.wait()
                    if not self.confirm_result:
                        return "用户取消了敏感操作"
            return tool_func.run(args)
        except Exception as e:
            return f"工具执行失败: {str(e)}"

    def _is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in DANGEROUS_KEYWORDS)
