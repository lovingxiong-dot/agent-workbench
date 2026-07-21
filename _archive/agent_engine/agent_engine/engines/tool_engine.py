"""
Tool Engine — 工具注册、权限校验、执行编排、结果处理

实现 IToolEngine 接口，负责管理工具生命周期：
- 工具注册与查找
- Phase 级白名单权限校验
- 危险操作二次确认
- 同步/异步工具统一执行 + 超时 + 结果截断
"""
import asyncio
import inspect
import time
from typing import Any, Callable, Dict, List, Optional

from .interfaces import IToolEngine, ToolResult

# 默认 Phase 白名单：analyze/verify 只开放只读工具，execute 开放全部
_DEFAULT_PHASE_ALLOWLISTS: Dict[str, Optional[set]] = {
    "analyze": {
        "web_fetch", "fetch_financial_news", "fetch_macro_data", "fetch_stock_data",
        "read_file", "list_dir", "clipboard_read", "list_processes",
    },
    "verify": {
        "web_fetch", "fetch_financial_news", "fetch_macro_data", "fetch_stock_data",
        "read_file", "list_dir", "clipboard_read", "list_processes",
    },
    "execute": None,  # None = 不限制
}

# 危险关键词：命中则触发确认回调
_DANGEROUS_KEYWORDS = (
    "del ", "delete", "rm -", "rd /s", "rmdir /s", "format ",
    "mkfs", "shutdown", "reg delete", "reg add", "diskpart",
)

# 超时与截断
_DEFAULT_TOOL_TIMEOUT = 30.0
_RESULT_TRUNCATE_LEN = 5000


class ToolEngine(IToolEngine):
    """工具引擎

    职责：
    - register：注册工具函数与定义
    - call：按 Phase 白名单校验后执行工具，支持超时和结果截断
    - bind_for_phase：按 Phase 过滤工具定义并绑定到 LLM
    - get_by_name：按名称查找工具函数
    """

    def __init__(
        self,
        tool_map: Optional[Dict[str, Callable]] = None,
        tool_definitions: Optional[List[Dict]] = None,
        policy_engine=None,
        confirm_callback: Optional[Callable[[str, Any], Any]] = None,
        cpu_executor=None,
        arun_map: Optional[Dict[str, Callable]] = None,
        phase_allowlists: Optional[Dict[str, Optional[set]]] = None,
    ):
        self._tool_map: Dict[str, Callable] = dict(tool_map or {})
        self._tool_definitions: List[Dict] = list(tool_definitions or [])
        self._arun_map: Dict[str, Callable] = dict(arun_map or {})
        self.policy = policy_engine
        self.confirm_callback = confirm_callback
        self.cpu_executor = cpu_executor
        self.phase_allowlists = phase_allowlists or _DEFAULT_PHASE_ALLOWLISTS

    # ── IToolEngine 实现 ────────────────────────────

    def register(self, name: str, func: Callable, definition: Dict) -> None:
        """注册工具"""
        self._tool_map[name] = func
        # 去重：覆盖同名定义
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
        """调用工具（含权限校验 + 危险确认 + 超时 + 截断）"""
        start = time.monotonic()

        # 1. 查找工具
        tool_func = self._tool_map.get(name)
        if tool_func is None:
            return ToolResult(name=name, result=f"Tool '{name}' not registered",
                              elapsed_ms=0, success=False)

        # 2. Phase 白名单校验
        if not self._is_tool_allowed(name, phase):
            return ToolResult(
                name=name,
                result=f"Tool '{name}' is not allowed in {phase} phase",
                elapsed_ms=0, success=False,
            )

        # 3. 危险操作二次确认
        if name in ("run_command", "run_as_admin"):
            if self._is_dangerous(args):
                if self.confirm_callback:
                    try:
                        confirmed = await self.confirm_callback(name, args)
                    except Exception:
                        confirmed = False
                    if not confirmed:
                        return ToolResult(
                            name=name, result="User cancelled sensitive operation",
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

        # 4. 执行工具（超时保护）
        timeout = self._get_tool_timeout()
        try:
            result_str = await asyncio.wait_for(
                self._execute_tool(name, tool_func, args), timeout=timeout
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            # 5. 结果截断
            if len(result_str) > _RESULT_TRUNCATE_LEN:
                result_str = result_str[:_RESULT_TRUNCATE_LEN] + (
                    f"\n\n[结果已截断，原始长度 {len(result_str)} 字符]"
                )

            return ToolResult(name=name, result=result_str,
                              elapsed_ms=elapsed_ms, success=True)

        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                name=name, result=f"Tool '{name}' timed out after {timeout:.0f}s",
                elapsed_ms=elapsed_ms, success=False,
            )
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                name=name, result=f"Tool '{name}' failed: {str(e)[:300]}",
                elapsed_ms=elapsed_ms, success=False,
            )

    def bind_for_phase(self, phase: str, llm) -> Any:
        """按 Phase 过滤工具定义，绑定到 LLM

        规则：
        - analyze/verify：仅绑定只读/查找类工具
        - execute：绑定全部工具
        - 若没有匹配的工具定义，返回原始 llm（不绑定）
        """
        allowed_defs = self._get_allowed_definitions(phase)
        if not allowed_defs:
            return llm

        # 检查 LLM 是否已绑定过工具（langchain bind_tools 会返回新对象）
        try:
            return llm.bind_tools(allowed_defs)
        except AttributeError:
            # 若 LLM 不支持 bind_tools，直接返回
            return llm

    def get_by_name(self, name: str) -> Optional[Callable]:
        """按名称查找工具函数"""
        return self._tool_map.get(name)

    # ── 内部 ────────────────────────────────────────

    async def _execute_tool(self, name: str, tool_func: Callable, args: Any) -> str:
        """执行单个工具：优先 async（arun_map），其次协程函数，最后同步回退"""
        # 1. arun_map 中的原生异步
        arun_func = self._arun_map.get(name)
        if arun_func and callable(arun_func):
            result = await arun_func(args)
            return str(result) if not isinstance(result, str) else result

        # 2. 工具函数自身是协程
        if inspect.iscoroutinefunction(tool_func):
            result = await tool_func(args)
            return str(result) if not isinstance(result, str) else result

        # 3. 同步工具：在 cpu_executor 中执行，避免阻塞事件循环
        loop = asyncio.get_running_loop()
        executor = self.cpu_executor
        if executor is None:
            raise RuntimeError("cpu_executor not set for synchronous tool execution")

        def _run_sync():
            return tool_func.run(args)

        result = await loop.run_in_executor(executor, _run_sync)
        return str(result) if not isinstance(result, str) else result

    def _is_tool_allowed(self, name: str, phase: str) -> bool:
        """检查工具在指定 Phase 是否允许"""
        allowed = self.phase_allowlists.get(phase)
        if allowed is None:
            return True  # execute 阶段不限
        return name in allowed

    def _get_allowed_definitions(self, phase: str) -> List[Dict]:
        """获取指定 Phase 允许的工具定义列表"""
        allowed = self.phase_allowlists.get(phase)
        if allowed is None:
            return list(self._tool_definitions)

        result = []
        for d in self._tool_definitions:
            try:
                func_name = d.get("function", {}).get("name", "")
                if func_name in allowed and func_name in self._tool_map:
                    result.append(d)
            except Exception:
                continue
        return result

    def _get_tool_timeout(self) -> float:
        """从策略引擎读取工具超时值"""
        if self.policy:
            try:
                return float(self.policy.get("tool.timeout", _DEFAULT_TOOL_TIMEOUT))
            except Exception:
                pass
        return _DEFAULT_TOOL_TIMEOUT

    @staticmethod
    def _is_dangerous(args: Any) -> bool:
        """判断工具参数是否包含危险关键词"""
        if isinstance(args, dict):
            command = args.get("command", "")
        else:
            command = str(args) if args else ""
        if not command:
            return False
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in _DANGEROUS_KEYWORDS)
