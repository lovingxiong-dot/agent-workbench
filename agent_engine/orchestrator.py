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
"""
import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


class AgentOrchestrator:
    # 工具结果回传给 LLM 的最大长度，防止原始 HTML/错误信息撑爆上下文
    TOOL_RESULT_MAX_LEN = 3000
    # 接近上限时，给 LLM 追加强制总结提示
    FORCE_ANSWER_THRESHOLD = 1

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

    async def run(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        cancel_event=None,
    ) -> str:
        """
        执行一次完整的 Agent 推理流程。

        callbacks 可选键：
          - log(str): 日志文本
          - tool_start(str, str): (task_id, description)
          - tool_end(str, str): (task_id, result_summary)
          - chunk(str): 流式文本片段
          - round(int): 当前 ReAct 轮次
          - error(str, str): (error_code, detail)

        返回最终文本（即便出错也会返回描述文本）。
        """
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
            allowed_defs = [d for d in self.tool_definitions if d["function"]["name"] in self.tool_map]
            model_name = str(self.llm.model) if hasattr(self.llm, 'model') else ""
            skip_tools = any(m in model_name for m in ("gemma2", "gemma:"))
            llm = self.llm.bind_tools(allowed_defs) if (allowed_defs and not skip_tools) else self.llm

            round_count = 0
            while round_count < self.max_tool_rounds:
                _check_cancel()

                _emit("metrics_start")
                response = await llm.ainvoke(messages)

                # 提取 token 用量（部分 provider/streaming 模式下可能缺失）
                usage_metadata = getattr(response, "usage_metadata", None) or {}
                usage_payload = {
                    "provider": model_name,
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
                        result = await asyncio.to_thread(self.tool_executor, tool_name, tool_args)
                        result_text = str(result) if result is not None else ""
                        # 截断过长的工具结果，避免 LLM 上下文被原始 HTML 撑爆
                        if len(result_text) > self.TOOL_RESULT_MAX_LEN:
                            result_text = result_text[:self.TOOL_RESULT_MAX_LEN] + (
                                f"\n\n[... 工具结果已截断，原始长度 {len(str(result))} 字符]"
                            )
                        _emit("tool_end", task_id, result_text[:200])
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
                final_response = await self.llm.ainvoke(final_messages)
                reply = final_response.content or ""
                if reply:
                    if self.enable_streaming:
                        for line in reply.replace('\r\n', '\n').split('\n'):
                            _check_cancel()
                            _emit("chunk", line + '\n')
                    _emit("log", f"[RESULT] forced summary length={len(reply.strip())}")
                    return reply.strip()
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
        """
        按 phase 执行 LLM 调用。

        - analyze: 让 LLM 输出任务清单（JSON 或 Markdown 列表）
        - execute: 复用 run() 完整执行
        - verify: 让 LLM 检查执行结果并返回验证结论
        """
        phase = (phase or "").lower()
        mode = (mode or "").lower()

        # 保存原始 prompt，执行完恢复
        original_prompt = self.system_prompt
        original_workspace_context = self.workspace_context

        try:
            self.workspace_context = context or self.workspace_context

            if phase == "analyze":
                self.system_prompt = self._build_analyze_prompt(mode)
                # analyze 阶段不绑定工具，让 LLM 纯输出任务清单
                return await self._run_without_tools(user_input, chat_history, callbacks, cancel_event)
            elif phase == "verify":
                self.system_prompt = self._build_verify_prompt(mode)
                return await self._run_without_tools(user_input, chat_history, callbacks, cancel_event)
            elif phase in ("execute", "confirm", "archive"):
                # execute 用默认 system_prompt；confirm/archive 由 UI/框架处理，不调用 LLM
                return await self.run(user_input, chat_history, callbacks, cancel_event)
            else:
                return await self.run(user_input, chat_history, callbacks, cancel_event)
        finally:
            self.system_prompt = original_prompt
            self.workspace_context = original_workspace_context

    async def _run_without_tools(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        cancel_event=None,
    ) -> str:
        """不绑定工具的 LLM 调用，用于 analyze/verify 阶段"""
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
            _check_cancel()
            _emit("metrics_start")
            response = await self.llm.ainvoke(messages)

            usage_metadata = getattr(response, "usage_metadata", None) or {}
            usage_payload = {
                "provider": str(self.llm.model) if hasattr(self.llm, "model") else "",
                "input_tokens": int(usage_metadata.get("input_tokens", 0) or 0),
                "output_tokens": int(usage_metadata.get("output_tokens", 0) or 0),
            }

            reply = response.content or ""
            _emit("metrics_first_token")
            _emit("token_usage", usage_payload)

            if self.enable_streaming and reply:
                for line in reply.replace("\r\n", "\n").split("\n"):
                    _check_cancel()
                    _emit("chunk", line + "\n")
            _emit("log", f"[RESULT] phase_result length={len(reply.strip() if reply else '')}")
            return reply.strip() if reply else ""

        except OrchestratorCancelledError:
            _emit("log", "[STOP] 任务已取消")
            raise
        except Exception as ex:
            _emit("error", "ORCHESTRATOR", str(ex))
            _emit("log", f"[ERR] {ex}")
            return f"Error: {str(ex)}"

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
                "\n\nPlan 模式需要制定执行计划。请输出任务清单，每个任务包含具体描述。"
                "输出格式为 JSON 数组或 Markdown 列表，例如：\n"
                '[{"description": "步骤1: xxx"}, {"description": "步骤2: yyy"}]'
            )
        elif mode == "craft":
            base += (
                "\n\nCraft 模式需要生成可执行的任务清单。请把用户需求拆分为 3-7 个具体任务，"
                "每个任务应该是独立的执行单元。输出格式为 JSON 数组或 Markdown 列表，例如：\n"
                '[{"description": "读取文件 xxx"}, {"description": "修改文件 yyy"}, {"description": "运行测试"}]'
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
        prompt += f"\n\n## YOUR IDENTITY\nYou are AI Agent Workbench v2 running on model '{model_id}'. When asked who/what model you are, state: 'I am AI Agent Workbench v2, powered by {model_id}.' Never claim to be Claude, GPT, Gemini, or any other brand."
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
