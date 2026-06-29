"""
AgentOrchestrator — Agent 执行管道编排器

负责将一次用户请求分解为标准化阶段：
  1. 意图/模式确认
  2. 上下文组装（system prompt + 历史记忆 + 用户输入）
  3. 工具注入（bind_tools）
  4. ReAct 多轮循环
  5. 结果回传（流式/最终）

设计原则：
- 不依赖 PySide6 / UI，只通过 callbacks 与外部通信
- 不直接读取文件，所有配置由调用方传入
- 可被 AgentWorker、后台任务、测试代码复用
- 支持 Phase 切换：Analyze / Execute / Verify 共享同一 Orchestrator 实例
"""
import asyncio
import inspect
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


class AgentOrchestrator:
    # 工具结果回传给 LLM 的最大长度，防止原始 HTML/错误信息撑爆上下文
    TOOL_RESULT_MAX_LEN = 5000
    # 接近上限时，给 LLM 追加强制总结提示
    FORCE_ANSWER_THRESHOLD = 1

    # 默认超时（秒）：LLM 单次调用、单轮工具执行、任务总超时由外部控制
    DEFAULT_LLM_TIMEOUT = 90.0
    DEFAULT_TOOL_TIMEOUT = 30.0

    # Phase 默认可用工具集合：Analyze/Verify 只保留读/查类工具，Execute 开放全部
    DEFAULT_PHASE_TOOLS: Dict[str, Optional[Any]] = {
        "analyze": {
            "web_fetch", "fetch_financial_news", "fetch_macro_data", "fetch_stock_data",
            "read_file", "list_dir", "clipboard_read", "list_processes",
        },
        "verify": {
            "web_fetch", "fetch_financial_news", "fetch_macro_data", "fetch_stock_data",
            "read_file", "list_dir", "clipboard_read", "list_processes",
        },
        "execute": None,  # None 表示不限制，使用全部工具
    }

    def __init__(
        self,
        llm,
        tool_map: Dict[str, Callable],
        tool_definitions: List[Dict],
        system_prompt: str,
        user_rules: Optional[List[str]] = None,
        max_tool_rounds: int = 8,
        enable_streaming: bool = True,
        tool_executor: Optional[Callable[[str, Any], str]] = None,
        workspace_context: str = "",
        app_version: str = "v3.x",
        llm_timeout: float = DEFAULT_LLM_TIMEOUT,
        tool_timeout: float = DEFAULT_TOOL_TIMEOUT,
        cpu_executor=None,
        arun_map: Optional[Dict[str, Callable]] = None,
        confirm_callback: Optional[Callable[[str, Any], Any]] = None,
        phase_tool_allowlists: Optional[Dict[str, Optional[Any]]] = None,
        engines: Optional[Dict[str, Any]] = None,
    ):
        self.llm = llm
        self.tool_map = tool_map or {}
        self.tool_definitions = tool_definitions or []
        self.base_system_prompt = system_prompt or "You are a helpful AI assistant."
        self.system_prompt = self.base_system_prompt
        self.user_rules = user_rules or []
        self.max_tool_rounds = max(1, int(max_tool_rounds))
        self.enable_streaming = enable_streaming
        self.tool_executor = tool_executor or self._default_tool_executor
        self.workspace_context = workspace_context or ""
        self.app_version = app_version or "v3.x"
        self.llm_timeout = max(5.0, float(llm_timeout or self.DEFAULT_LLM_TIMEOUT))
        self.tool_timeout = max(5.0, float(tool_timeout or self.DEFAULT_TOOL_TIMEOUT))
        self.cpu_executor = cpu_executor
        self.arun_map = arun_map or {}
        self.confirm_callback = confirm_callback
        self._current_phase = "execute"
        self._current_mode = "craft"
        # 合并自定义 Phase 工具白名单；None 表示该 Phase 不限制
        self.phase_tool_allowlists: Dict[str, Optional[Any]] = dict(self.DEFAULT_PHASE_TOOLS)
        if phase_tool_allowlists:
            self.phase_tool_allowlists.update(phase_tool_allowlists)
        # v3.11.ai-engine: 绞杀者模式 — 新引擎注入
        self._engines = engines or {}

    # ═══════════════════════════════════════════════════════
    # Phase 切换（P0-2 新增）
    # ═══════════════════════════════════════════════════════
    def set_phase(self, phase: str, mode: str = "", context: str = ""):
        """切换当前 Phase，更新 system_prompt 与 workspace_context

        Args:
            phase: 目标阶段 (analyze/execute/verify)
            mode: 当前模式 (ask/plan/craft)，用于生成对应阶段的 prompt
            context: 工作区上下文

        规则：
        - analyze/verify 阶段在 base_system_prompt 后**追加**阶段特定指令，不覆盖
        - execute 阶段使用 base_system_prompt
        """
        phase = (phase or "execute").lower()
        mode = (mode or "craft").lower()
        self._current_phase = phase
        self._current_mode = mode

        # v3.11.ai-engine: PromptEngine 委托
        prompt_engine = self._engines.get("prompt")
        if prompt_engine and hasattr(prompt_engine, "build_system_prompt"):
            self.system_prompt = prompt_engine.build_system_prompt(mode, phase)
        else:
            # 回退旧逻辑
            if phase == "analyze":
                self.system_prompt = self.base_system_prompt + "\n\n" + self._build_analyze_prompt(mode)
            elif phase == "verify":
                self.system_prompt = self.base_system_prompt + "\n\n" + self._build_verify_prompt(mode)
            elif phase == "execute":
                self.system_prompt = self.base_system_prompt

        if context:
            self.workspace_context = context

    def bind_tools_for_phase(self, phase: str):
        """根据 phase 决定绑定哪些工具；返回绑定后的 LLM"""
        # v3.11.ai-engine: ToolEngine 委托
        tool_engine = self._engines.get("tool")
        if tool_engine and hasattr(tool_engine, "bind_for_phase"):
            return tool_engine.bind_for_phase(phase, self.llm)

        # 回退旧逻辑
        phase = (phase or "execute").lower()
        allowed_names = self.phase_tool_allowlists.get(phase)

        def _is_allowed(name: str) -> bool:
            if name not in self.tool_map:
                return False
            if allowed_names is None:
                return True
            return name in allowed_names

        allowed_defs = [d for d in self.tool_definitions if _is_allowed(d["function"]["name"])]
        if not allowed_defs:
            return self.llm
        model_name = str(self.llm.model) if hasattr(self.llm, 'model') else ""
        skip_tools = any(m in model_name for m in ("gemma2", "gemma:"))
        return self.llm.bind_tools(allowed_defs) if not skip_tools else self.llm

    def _is_tool_allowed_in_phase(self, name: str, phase: str) -> bool:
        """运行时校验工具是否在当前 Phase 白名单中"""
        allowed_names = self.phase_tool_allowlists.get(phase)
        if allowed_names is None:
            return True
        return name in allowed_names

    # ═══════════════════════════════════════════════════════
    # 公共执行接口
    # ═══════════════════════════════════════════════════════
    def run(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        cancel_event=None,
    ) -> str:
        """同步兼容包装"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 已在事件循环中，创建新任务
                return loop.create_task(
                    self.arun(user_input, chat_history, callbacks, cancel_event)
                )
            return loop.run_until_complete(
                self.arun(user_input, chat_history, callbacks, cancel_event)
            )
        except RuntimeError:
            return asyncio.run(
                self.arun(user_input, chat_history, callbacks, cancel_event)
            )

    async def _invoke_llm_with_cancel(
        self,
        llm,
        messages,
        timeout: float,
        cancel_event,
    ):
        """调用 LLM，支持超时和取消事件轮询。

        通过每 500ms 检查一次 cancel_event，确保用户点击停止按钮后，
        即使 LLM 响应缓慢也能被及时中断，避免事件循环被长期阻塞。
        """
        if cancel_event is None:
            return await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)

        llm_task = asyncio.create_task(llm.ainvoke(messages))
        try:
            while not llm_task.done():
                if cancel_event.is_set():
                    llm_task.cancel()
                    try:
                        await llm_task
                    except asyncio.CancelledError:
                        pass
                    raise OrchestratorCancelledError("任务已取消")
                try:
                    await asyncio.wait_for(asyncio.shield(llm_task), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
            return llm_task.result()
        except asyncio.CancelledError:
            raise OrchestratorCancelledError("任务已取消")

    async def arun(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        cancel_event=None,
    ) -> str:
        """执行一次完整的 Agent 推理流程（异步原生）。"""
        callbacks = callbacks or {}
        chat_history = list(chat_history) if chat_history else []

        def _emit(name: str, *args):
            cb = callbacks.get(name)
            if cb:
                try:
                    cb(*args)
                except Exception as e:
                    self._log(callbacks, f"[ORCH_CALLBACK_ERR] {name}: {e}")

        def _check_cancel():
            if cancel_event and cancel_event.is_set():
                raise OrchestratorCancelledError("任务已取消")

        messages = self._build_messages(user_input, chat_history)

        try:
            llm = self.bind_tools_for_phase(self._current_phase)

            round_count = 0
            while round_count < self.max_tool_rounds:
                _check_cancel()

                _emit("metrics_start")
                try:
                    response = await self._invoke_llm_with_cancel(
                        llm, messages, self.llm_timeout, cancel_event
                    )
                except asyncio.TimeoutError:
                    elapsed = self.llm_timeout
                    _emit("error", "LLM_TIMEOUT", f"LLM 响应超过 {elapsed:.0f} 秒未返回")
                    _emit("log", f"[ERR] LLM_TIMEOUT: LLM 响应超过 {elapsed:.0f} 秒")
                    return f"Error: LLM 响应超时（>{elapsed:.0f}s）。请检查模型服务是否正常运行，或稍后重试。"

                # 提取 token 用量（部分 provider/streaming 模式下可能缺失）
                usage_metadata = getattr(response, "usage_metadata", None) or {}
                usage_payload = {
                    "provider": str(self.llm.model) if hasattr(self.llm, 'model') else "",
                    "input_tokens": int(usage_metadata.get("input_tokens", 0) or 0),
                    "output_tokens": int(usage_metadata.get("output_tokens", 0) or 0),
                }

                if hasattr(response, "tool_calls") and response.tool_calls:
                    _emit("log", f"[TOOL] Calling: {[tc['name'] for tc in response.tool_calls]} (round {round_count + 1})")
                    tool_call_msg = AIMessage(content="", tool_calls=response.tool_calls)
                    messages.append(tool_call_msg)

                    for tc in response.tool_calls:
                        _check_cancel()
                        tool_name = tc["name"]
                        tool_args = tc["args"]
                        task_id = f"{tool_name}_{datetime.now().strftime('%H%M%S')}"
                        _emit("tool_start", task_id, f"Running {tool_name}")
                        tool_start_at = datetime.now()
                        try:
                            result = await asyncio.wait_for(
                                self._call_tool(tool_name, tool_args),
                                timeout=self.tool_timeout
                            )
                        except asyncio.TimeoutError:
                            elapsed = self.tool_timeout
                            _emit("error", "TOOL_TIMEOUT", f"工具 {tool_name} 执行超过 {elapsed:.0f} 秒")
                            _emit("log", f"[ERR] TOOL_TIMEOUT: {tool_name} 执行超过 {elapsed:.0f} 秒")
                            result = f"[工具超时] {tool_name} 执行超过 {elapsed:.0f} 秒，已中断。"
                        elapsed_ms = int((datetime.now() - tool_start_at).total_seconds() * 1000)
                        result_text = str(result) if result is not None else ""
                        # 截断过长的工具结果，避免 LLM 上下文被原始 HTML 撑爆
                        raw_len = len(result_text)
                        if len(result_text) > self.TOOL_RESULT_MAX_LEN:
                            result_text = result_text[:self.TOOL_RESULT_MAX_LEN] + (
                                f"\n\n[... 工具结果已截断，原始长度 {raw_len} 字符]"
                            )
                        _emit("tool_end", task_id, result_text[:200])
                        _emit("tool_executed", tool_name, tool_args, result_text, elapsed_ms)
                        _emit("log", f"[OK] {tool_name}")
                        messages.append(ToolMessage(
                            content=result_text,
                            tool_call_id=tc["id"],
                        ))

                    _check_cancel()
                    round_count += 1
                    _emit("round", round_count)
                    # 接近上限时强制 LLM 不要再调用工具，直接总结回答
                    if self.max_tool_rounds - round_count <= self.FORCE_ANSWER_THRESHOLD:
                        messages.append(SystemMessage(
                            content=(
                                "你已经用完了几乎所有可用的工具调用轮次。"
                                "请基于已获得的工具结果直接回答用户问题，"
                                "不要再发起新的工具调用。"
                            )
                        ))
                    continue

                reply = response.content or ""
                has_tool_calls = bool(getattr(response, 'tool_calls', None))
                _emit("log", f"[SUMMARY] round={round_count}, content length={len(reply)}, has_tool_calls={has_tool_calls}")
                if not reply:
                    results = [msg.content for msg in messages if isinstance(msg, ToolMessage)]
                    reply = "\n\n".join(results) if results else "[Tool executed]"

                _emit("metrics_first_token")
                _emit("token_usage", usage_payload)

                if self.enable_streaming and reply:
                    for line in reply.replace('\r\n', '\n').split('\n'):
                        _check_cancel()
                        _emit("chunk", line + '\n')
                _emit("log", f"[RESULT] result_ready length={len(reply.strip() if reply else '')}")
                return reply.strip() if reply else "[Tool executed]"

            # 超过最大轮数：先尝试让 LLM 基于已有结果做一次最终总结
            _emit("log", f"[WARN] Exceeded max tool rounds ({self.max_tool_rounds}), forcing final summary")
            final_messages = list(messages)
            final_messages.append(SystemMessage(
                content=(
                    "工具调用轮次已达上限。请严格根据已经获得的工具结果，"
                    "用中文给用户一个简洁、准确的最终回答。不要调用任何新工具。"
                )
            ))
            try:
                final_response = await self._invoke_llm_with_cancel(
                    self.llm, final_messages, self.llm_timeout, cancel_event
                )
                reply = final_response.content or ""
                if reply:
                    if self.enable_streaming:
                        for line in reply.replace('\r\n', '\n').split('\n'):
                            _check_cancel()
                            _emit("chunk", line + '\n')
                    _emit("log", f"[RESULT] forced summary length={len(reply.strip())}")
                    return reply.strip()
            except asyncio.TimeoutError:
                _emit("error", "LLM_TIMEOUT", f"最终总结 LLM 响应超过 {self.llm_timeout:.0f} 秒")
                _emit("log", f"[ERR] LLM_TIMEOUT: 最终总结超时")
            except Exception as ex:
                _emit("log", f"[WARN] Final summary failed: {ex}")

            # 兜底：返回截断后的工具摘要，避免把原始 HTML/错误堆栈直接喷到对话框
            results = [msg.content for msg in messages if isinstance(msg, ToolMessage)]
            fallback = self._build_fallback_reply(results)
            if self.enable_streaming and fallback:
                for line in fallback.replace('\r\n', '\n').split('\n'):
                    _check_cancel()
                    _emit("chunk", line + '\n')
            return fallback

        except OrchestratorCancelledError:
            _emit("log", "[STOP] 任务已取消")
            raise
        except Exception as ex:
            _emit("error", "ORCHESTRATOR", str(ex))
            _emit("log", f"[ERR] {ex}")
            return f"Error: {str(ex)}"

    async def _call_tool(self, name: str, args: Any) -> str:
        """调用工具：优先使用 ToolEngine（如有），否则走旧逻辑"""

        # v3.11.ai-engine: ToolEngine 委托
        tool_engine = self._engines.get("tool")
        if tool_engine and hasattr(tool_engine, "call"):
            result = await tool_engine.call(name, args, self._current_phase)
            return result.result

        # 回退旧逻辑
        tool_func = self.tool_map.get(name)
        if not tool_func:
            return f"Tool {name} not found"
        if isinstance(args, str):
            import json
            try:
                args = json.loads(args)
            except Exception:
                pass

        # 敏感操作二次确认
        if name in ("run_command", "run_as_admin"):
            command = args.get("command", "") if isinstance(args, dict) else str(args)
            if self._is_dangerous(command):
                if self.confirm_callback:
                    try:
                        confirmed = await self.confirm_callback(name, args)
                    except Exception:
                        confirmed = False
                    if not confirmed:
                        return "User cancelled sensitive operation"
                else:
                    return "Sensitive operation blocked: no confirm callback configured"

        # Phase 级工具白名单：即使 LLM 意外请求，运行时也拒绝执行非白名单工具
        if not self._is_tool_allowed_in_phase(name, self._current_phase):
            return f"Tool {name} is not allowed in {self._current_phase} phase"

        # P0-3 原生异步：优先从 ARUN_MAP 取 arun 协程
        arun_func = self.arun_map.get(name)
        if arun_func and callable(arun_func):
            return await arun_func(args)
        # 若工具函数本身是协程函数
        if inspect.iscoroutinefunction(tool_func):
            return await tool_func(args)
        # 同步工具回退：显式使用 cpu_executor，禁止使用 asyncio.to_thread（避免绕过线程池）
        loop = asyncio.get_running_loop()
        executor = self.cpu_executor
        if executor is None:
            raise RuntimeError("Orchestrator.cpu_executor is not set for synchronous tool fallback")
        return await loop.run_in_executor(executor, tool_func.run, args)

    @staticmethod
    def _is_dangerous(command: str) -> bool:
        """判断命令是否包含危险关键词"""
        if not command:
            return False
        dangerous_keywords = (
            "del ", "delete", "rm -", "rd /s", "rmdir /s", "format ",
            "mkfs", "shutdown", "reg delete", "reg add", "diskpart",
        )
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in dangerous_keywords)

    async def run_phase(
        self,
        phase: str,
        mode: str,
        user_input: str,
        context: str = "",
        chat_history: Optional[List] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        cancel_event=None,
    ) -> str:
        """按 phase 执行 LLM 调用（兼容旧接口，内部复用 arun）"""
        self.set_phase(phase, mode, context)
        return await self.arun(user_input, chat_history, callbacks, cancel_event)

    # ═══════════════════════════════════════════════════════
    # Prompt 构建
    # ═══════════════════════════════════════════════════════
    def _build_analyze_prompt(self, mode: str) -> str:
        """Analyze 阶段的 system prompt"""
        base = (
            "你是 AI Agent Workbench 的分析专家。请仔细分析用户需求，"
            "输出一个可执行的任务清单。"
        )
        if mode == "ask":
            base += (
                "\n\nAsk 模式只分析、不执行。请给出：1) 用户意图；2) 需要查看/确认的信息；"
                "3) 建议的后续操作。输出格式为 Markdown 列表。"
            )
        elif mode == "plan":
            base += (
                "\n\nPlan 模式需要制定执行计划。请把用户需求拆分为 3-7 个具体任务，"
                "每个任务应该是独立的规划单元。"
                "\n\n工具调用要求："
                "\n在输出任务清单前，必须先使用 read_file、list_dir、web_fetch 等只读工具收集完成任务所必需的信息。"
                "不要直接编造文件内容或假设目录结构。"
                "\n\n输出格式要求："
                "\n1. 只输出任务清单，不要输出分析过程、解释、建议或总结。"
                "\n2. 优先使用 JSON 数组格式：[{\"description\": \"步骤1: xxx\"}, {\"description\": \"步骤2: yyy\"}]"
                "\n3. 每个任务描述必须包含具体可执行动作，但应优先使用工作台内置工具，"
                "例如 '使用 list_dir 列出 xxx 目录'、'使用 read_file 读取 xxx 文件'、'使用 write_file 写入 xxx 文件'。"
                "\n4. 只有在没有对应专用工具时才使用 run_command，避免把 PowerShell / cmd / shell 命令直接写入任务描述。"
            )
        elif mode == "craft":
            base += (
                "\n\nCraft 模式需要生成可执行的任务清单。请把用户需求拆分为 3-7 个具体任务，"
                "每个任务应该是独立的执行单元。"
                "\n\n工具调用要求："
                "\n在输出任务清单前，必须先使用 read_file、list_dir、web_fetch 等只读工具收集完成任务所必需的信息。"
                "不要直接编造文件内容或假设目录结构。"
                "\n\n输出格式要求："
                "\n1. 只输出任务清单，不要输出分析过程、解释、建议或总结。"
                "\n2. 优先使用 JSON 数组格式：[{\"description\": \"步骤1: xxx\"}, {\"description\": \"步骤2: yyy\"}]"
                "\n3. 每个任务描述必须包含具体可执行动作，但应优先使用工作台内置工具，"
                "例如 '使用 list_dir 列出 xxx 目录'、'使用 read_file 读取 xxx 文件'、'使用 write_file 写入 xxx 文件'。"
                "\n4. 只有在没有对应专用工具时才使用 run_command，避免把 PowerShell / cmd / shell 命令直接写入任务描述。"
            )
        else:
            base += "\n\n请输出任务清单，格式为 Markdown 列表。"
        return base

    def _build_verify_prompt(self, mode: str) -> str:
        """Verify 阶段的 system prompt"""
        return (
            "你是 AI Agent Workbench 的验证专家。请根据下方的执行结果，"
            "判断任务是否完成、是否存在明显错误。"
            "\n\n输出要求："
            "\n1. 首先给出结论：通过 / 未通过"
            "\n2. 简要说明理由"
            "\n3. 如果未通过，给出修复建议"
        )

    def _build_messages(self, user_input: str, chat_history: List):
        model_id = str(self.llm.model) if hasattr(self.llm, 'model') else "unknown"
        prompt = self.system_prompt
        prompt += f"\n\n## YOUR IDENTITY\nYou are AI Agent Workbench {self.app_version} running on model '{model_id}'. When asked who/what model you are, state: 'I am AI Agent Workbench {self.app_version}, powered by {model_id}.' Never claim to be Claude, GPT, Gemini, or any other brand."
        if self.user_rules:
            rule_lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(self.user_rules))
            prompt += f"\n\n## USER RULES (MUST FOLLOW)\n{rule_lines}"
        if self.workspace_context:
            prompt += f"\n\n## CURRENT WORKSPACE CONTEXT (MUST USE THIS WHEN ANSWERING)\n{self.workspace_context}"
        return [SystemMessage(content=prompt)] + chat_history + [HumanMessage(content=user_input)]

    def _build_fallback_reply(self, results: List[str]) -> str:
        """超过最大轮数且最终总结失败时的兜底回复：精简展示工具结果，避免原始 HTML 刷屏。"""
        if not results:
            return "[工具已执行，但没有返回可用结果]"
        lines = []
        for idx, r in enumerate(results, 1):
            text = r.strip()
            # 只取前 500 字符，并按行截断
            if len(text) > 500:
                text = text[:500] + "\n[... 已截断]"
            lines.append(f"【来源 {idx}】\n{text}")
        body = "\n\n".join(lines)
        return (
            "工具调用次数已达上限，以下是我已获取到的部分原始信息，供你参考：\n\n"
            f"{body}\n\n"
            "如需更准确的分析，可以缩小问题范围或换用 Plan/Craft 模式。"
        )

    def _default_tool_executor(self, name: str, args: Any) -> str:
        tool_func = self.tool_map.get(name)
        if not tool_func:
            return f"Tool {name} not found"
        try:
            if isinstance(args, str):
                import json
                args = json.loads(args)
            return tool_func.run(args)
        except Exception as e:
            return f"Tool error: {str(e)}"

    def _log(self, callbacks: Dict[str, Callable], text: str):
        cb = callbacks.get("log")
        if cb:
            try:
                cb(text)
            except Exception:
                pass


class OrchestratorCancelledError(Exception):
    pass
