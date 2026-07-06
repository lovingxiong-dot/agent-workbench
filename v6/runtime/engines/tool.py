"""v6/runtime/engines/tool.py — ToolEngine：工具注册、权限校验、执行编排、结果处理。

设计来源：V4 agent_engine/engines/tool_engine.py（提取核心逻辑）。

职责：读取 ctx.metadata["tool_calls"] / ctx.phase，写回 ctx.metadata["tool_results"]。
"""
from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Callable, Dict, List, Optional

from v6.runtime.engines.interfaces import IToolEngine, ToolResult


_DEFAULT_PHASE_ALLOWLISTS: Dict[str, Optional[set]] = {
    "analyze": {
        "web_fetch",
        "fetch_financial_news",
        "fetch_macro_data",
        "fetch_stock_data",
        "read_file",
        "list_dir",
        "clipboard_read",
        "list_processes",
    },
    "verify": {
        "web_fetch",
        "fetch_financial_news",
        "fetch_macro_data",
        "fetch_stock_data",
        "read_file",
        "list_dir",
        "clipboard_read",
        "list_processes",
    },
    "execute": None,
}

_DANGEROUS_KEYWORDS = (
    "del ",
    "delete",
    "rm -",
    "rd /s",
    "rmdir /s",
    "format ",
    "mkfs",
    "shutdown",
    "reg delete",
    "reg add",
    "diskpart",
)

_DEFAULT_TOOL_TIMEOUT = 30.0
_RESULT_TRUNCATE_LEN = 5000


class ToolEngine(IToolEngine):
    """工具引擎。"""

    def __init__(
        self,
        tool_map: Optional[Dict[str, Callable]] = None,
        tool_definitions: Optional[List[Dict]] = None,
        policy_engine=None,
        confirm_callback: Optional[Callable[[str, Any], Any]] = None,
        cpu_executor=None,
        arun_map: Optional[Dict[str, Callable]] = None,
        phase_allowlists: Optional[Dict[str, Optional[set]]] = None,
    ) -> None:
        self._tool_map: Dict[str, Callable] = dict(tool_map or {})
        self._tool_definitions: List[Dict] = list(tool_definitions or [])
        self._arun_map: Dict[str, Callable] = dict(arun_map or {})
        self.policy = policy_engine
        self.confirm_callback = confirm_callback
        self.cpu_executor = cpu_executor
        self.phase_allowlists = phase_allowlists or _DEFAULT_PHASE_ALLOWLISTS

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """执行 ctx.metadata['tool_calls'] 中的工具调用，结果写回 ctx.metadata['tool_results']。"""
        calls = ctx.metadata.get("tool_calls", [])
        if not isinstance(calls, list):
            ctx.metadata["tool_results"] = []
            return ctx

        results = []
        for call in calls:
            name = call.get("name", "") if isinstance(call, dict) else ""
            args = call.get("args", {}) if isinstance(call, dict) else {}
            result = await self.call(name, args, phase=ctx.phase or "execute")
            results.append(result)

        ctx.metadata["tool_results"] = results
        return ctx

    def register(self, name: str, func: Callable, definition: Dict) -> None:
        """注册工具。"""
        self._tool_map[name] = func
        existing_idx = None
        for i, d in enumerate(self._tool_definitions):
            if d.get("function", {}).get("name") == name:
                existing_idx = i
                break
        if existing_idx is not None:
            self._tool_definitions[existing_idx] = definition
        else:
            self._tool_definitions.append(definition)

    async def call(
        self, name: str, args: Dict[str, Any], phase: str = "execute"
    ) -> ToolResult:
        """调用工具（含权限校验 + 危险确认 + 超时 + 截断）。"""
        start = time.monotonic()

        tool_func = self._tool_map.get(name)
        if tool_func is None:
            return ToolResult(
                name=name, result=f"Tool '{name}' not registered", elapsed_ms=0, success=False
            )

        if not self._is_tool_allowed(name, phase):
            return ToolResult(
                name=name,
                result=f"Tool '{name}' is not allowed in {phase} phase",
                elapsed_ms=0,
                success=False,
            )

        if name in ("run_command", "run_as_admin"):
            if self._is_dangerous(args):
                if self.confirm_callback:
                    try:
                        confirmed = await self.confirm_callback(name, args)
                    except Exception:
                        confirmed = False
                    if not confirmed:
                        return ToolResult(
                            name=name,
                            result="User cancelled sensitive operation",
                            elapsed_ms=int((time.monotonic() - start) * 1000),
                            success=False,
                        )
                else:
                    return ToolResult(
                        name=name,
                        result="Sensitive operation blocked: no confirm callback configured",
                        elapsed_ms=int((time.monotonic() - start) * 1000),
                        success=False,
                    )

        timeout = self._get_tool_timeout()
        try:
            result_str = await asyncio.wait_for(
                self._execute_tool(name, tool_func, args), timeout=timeout
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            if len(result_str) > _RESULT_TRUNCATE_LEN:
                result_str = result_str[:_RESULT_TRUNCATE_LEN] + (
                    f"\n\n[结果已截断，原始长度 {len(result_str)} 字符]"
                )

            return ToolResult(name=name, result=result_str, elapsed_ms=elapsed_ms, success=True)

        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                name=name,
                result=f"Tool '{name}' timed out after {timeout:.0f}s",
                elapsed_ms=elapsed_ms,
                success=False,
            )
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                name=name,
                result=f"Tool '{name}' failed: {str(e)[:300]}",
                elapsed_ms=elapsed_ms,
                success=False,
            )

    def bind_for_phase(self, phase: str, llm) -> Any:
        """按 Phase 过滤工具定义并绑定到 LLM。"""
        allowed_defs = self._get_allowed_definitions(phase)
        if not allowed_defs:
            return llm
        try:
            return llm.bind_tools(allowed_defs)
        except AttributeError:
            return llm

    def get_by_name(self, name: str) -> Optional[Callable]:
        """按名称查找工具函数。"""
        return self._tool_map.get(name)

    async def _execute_tool(self, name: str, tool_func: Callable, args: Any) -> str:
        """执行单个工具：优先 async，其次协程，最后同步回退。"""
        arun_func = self._arun_map.get(name)
        if arun_func and callable(arun_func):
            result = await arun_func(args)
            return str(result) if not isinstance(result, str) else result

        if inspect.iscoroutinefunction(tool_func):
            result = await tool_func(args)
            return str(result) if not isinstance(result, str) else result

        loop = asyncio.get_running_loop()
        executor = self.cpu_executor
        if executor is None:
            raise RuntimeError("cpu_executor not set for synchronous tool execution")

        def _run_sync():
            return tool_func(args)

        result = await loop.run_in_executor(executor, _run_sync)
        return str(result) if not isinstance(result, str) else result

    def _is_tool_allowed(self, name: str, phase: str) -> bool:
        """检查工具在指定 Phase 是否允许。"""
        allowed = self.phase_allowlists.get(phase)
        if allowed is None:
            return True
        return name in allowed

    def _get_allowed_definitions(self, phase: str) -> List[Dict]:
        """获取指定 Phase 允许的工具定义列表。"""
        allowed = self.phase_allowlists.get(phase)
        if allowed is None:
            return list(self._tool_definitions)

        result: List[Dict] = []
        for d in self._tool_definitions:
            try:
                func_name = d.get("function", {}).get("name", "")
                if func_name in allowed and func_name in self._tool_map:
                    result.append(d)
            except Exception:
                continue
        return result

    def _get_tool_timeout(self) -> float:
        """从策略引擎读取工具超时值。"""
        if self.policy:
            try:
                return float(self.policy.get("tool.timeout", _DEFAULT_TOOL_TIMEOUT))
            except Exception:
                pass
        return _DEFAULT_TOOL_TIMEOUT

    @staticmethod
    def _is_dangerous(args: Any) -> bool:
        """判断工具参数是否包含危险关键词。"""
        if isinstance(args, dict):
            command = args.get("command", "")
        else:
            command = str(args) if args else ""
        if not command:
            return False
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in _DANGEROUS_KEYWORDS)
