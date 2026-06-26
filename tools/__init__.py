"""
工具注册入口。
导出：
- TOOL_MAP: name -> LangChain Tool/StructuredTool（供 bind_tools 使用）
- ARUN_MAP: name -> async callable（供 Orchestrator._call_tool 优先调用）
"""

# 同步工具（LangChain @tool 对象）
from .system import (
    run_command, run_as_admin,
    read_file, write_file, list_dir,
    web_fetch,
    clipboard_read, clipboard_write,
    send_notification,
    list_processes, kill_process,
    run_python, run_powershell, run_bash,
)
from .system import (
    arun_command, arun_read_file, arun_write_file, arun_list_dir,
    arun_web_fetch, arun_clipboard_read, arun_clipboard_write,
    arun_list_processes, arun_kill_process,
    arun_run_python, arun_run_powershell, arun_run_bash,
)
from .quant import fetch_stock_data, run_backtest, arun_fetch_stock_data
from .mt5 import mt5_get_price, mt5_place_order
from .external_apis import fetch_financial_news, fetch_macro_data
from .external_apis import arun_fetch_financial_news, arun_fetch_macro_data

TOOL_MAP = {
    "run_command": run_command,
    "run_as_admin": run_as_admin,
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "web_fetch": web_fetch,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "send_notification": send_notification,
    "list_processes": list_processes,
    "kill_process": kill_process,
    "fetch_stock_data": fetch_stock_data,
    "run_backtest": run_backtest,
    "mt5_get_price": mt5_get_price,
    "mt5_place_order": mt5_place_order,
    "fetch_financial_news": fetch_financial_news,
    "fetch_macro_data": fetch_macro_data,
    "run_python": run_python,
    "run_powershell": run_powershell,
    "run_bash": run_bash,
}

ARUN_MAP = {
    "run_command": arun_command,
    "read_file": arun_read_file,
    "write_file": arun_write_file,
    "list_dir": arun_list_dir,
    "web_fetch": arun_web_fetch,
    "clipboard_read": arun_clipboard_read,
    "clipboard_write": arun_clipboard_write,
    "list_processes": arun_list_processes,
    "kill_process": arun_kill_process,
    "fetch_stock_data": arun_fetch_stock_data,
    "fetch_financial_news": arun_fetch_financial_news,
    "fetch_macro_data": arun_fetch_macro_data,
    "run_python": arun_run_python,
    "run_powershell": arun_run_powershell,
    "run_bash": arun_run_bash,
}
