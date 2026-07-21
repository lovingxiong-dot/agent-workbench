"""
AgentSession — 跨 Phase 复用同一 Orchestrator 的执行会话

职责：
- 在 Analyze / Execute / Verify 各阶段复用同一个 AgentOrchestrator 实例，
  消除每阶段重建 Orchestrator + LLM 的开销，使 Confirm 阶段延迟降至毫秒级。
- 维护 phase_messages：Analyze / Verify 共享轻量级摘要，Execute 独立消息列表，
  避免 Analyze 阶段的工具结果污染 Execute 上下文。
- 通过 Qt 信号与外部（AgentWorker → MainWindow）通信。
"""
import asyncio
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from agent_engine.orchestrator import AgentOrchestrator
from agent_engine.phase_manager import PhaseManager, TaskItem


class AgentSession(QObject):
    # 文本/结果
    chunk_ready = Signal(str)
    result_ready = Signal(str)

    # 工具执行回传（共享输出面板）
    tool_executed = Signal(str, dict, str, int)  # name, args, result, elapsed_ms

    # 资源/指标
    token_used = Signal(str, str, int, int)
    turn_metrics_ready = Signal(object)

    # 敏感操作确认
    confirm_required = Signal(str, str)  # tool_name, command

    # 日志/进度
    error_occurred = Signal(str, str)
    log_message = Signal(str)
    task_created = Signal(str, str)
    task_finished = Signal(str, str)
    round_advanced = Signal(int)

    def __init__(
        self,
        llm,
        tool_map: Dict[str, Any],
        tool_definitions: List[Dict],
        mode: str,
        project_root: str,
        system_prompt: str,
        user_rules: Optional[List[str]] = None,
        max_tool_rounds: int = 8,
        app_version: str = "v3.x",
        llm_timeout: float = 90.0,
        tool_timeout: float = 30.0,
        workspace_context: str = "",
        cpu_executor=None,
        arun_map: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.mode = mode
        self.project_root = project_root
        self.current_session_id: str = ""
        # 当前房间的完整对话历史（Session-as-Room）
        self.chat_history: List[BaseMessage] = []
        self.phase_messages: List[BaseMessage] = []
        self._confirm_event: Optional[asyncio.Event] = None
        self._confirm_result = False

        self.orchestrator = AgentOrchestrator(
            llm=llm,
            tool_map=tool_map,
            tool_definitions=tool_definitions,
            system_prompt=system_prompt,
            user_rules=user_rules,
            max_tool_rounds=max_tool_rounds,
            enable_streaming=True,
            workspace_context=workspace_context,
            app_version=app_version,
            llm_timeout=llm_timeout,
            tool_timeout=tool_timeout,
            cpu_executor=cpu_executor,
            arun_map=arun_map,
            confirm_callback=self._confirm_callback,
        )

    # ═══════════════════════════════════════════════════
    # Session-as-Room 生命周期
    # ═══════════════════════════════════════════════════
    def enter(self, session_id: str, messages: List[dict]):
        """进入房间：加载历史，重建当前 Session 的完整上下文。

        Args:
            session_id: 房间标识。
            messages: 从 SessionService 加载的原始消息列表，按时间序排列。
        """
        self.leave()
        self.current_session_id = session_id
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self.chat_history.append(HumanMessage(content=content))
            elif role == "ai":
                self.chat_history.append(AIMessage(content=content))
            elif role == "system":
                self.chat_history.append(SystemMessage(content=content))

    def leave(self):
        """离开房间：清空当前 Session 的上下文，不保留任何跨房间状态。"""
        self.current_session_id = ""
        self.chat_history.clear()
        self.phase_messages.clear()

    def add_user_message(self, content: str):
        """追加用户消息到当前房间历史。"""
        self.chat_history.append(HumanMessage(content=content))

    def add_assistant_message(self, content: str):
        """追加 AI 消息到当前房间历史。"""
        self.chat_history.append(AIMessage(content=content))

    def get_chat_history(self) -> List[BaseMessage]:
        """返回当前房间的完整对话历史副本。"""
        return list(self.chat_history)

    # ═══════════════════════════════════════════════════
    # Phase 执行入口
    # ═══════════════════════════════════════════════════
    async def run_analyze(self, user_text: str, context: str, cancel_event=None) -> tuple:
        """Analyze 阶段：复用 Orchestrator，返回 (task_list, full_text)。"""
        self.orchestrator.set_phase("analyze", self.mode, context)
        full_text = await self.orchestrator.arun(
            user_text, list(self.phase_messages), callbacks=self._callbacks(), cancel_event=cancel_event
        )

        # 记录摘要，不把完整工具调用历史带入下一阶段
        self.phase_messages.append(HumanMessage(content=user_text))
        self.phase_messages.append(AIMessage(content=full_text[:1500]))
        self._trim_phase_messages()

        task_list = PhaseManager.parse_task_list(full_text)
        return (task_list, full_text)

    async def run_execute(self, task_list: List[TaskItem], original_text: str, context: str, cancel_event=None) -> str:
        """Execute 阶段：独立消息列表，避免 Analyze 工具结果污染"""
        self.orchestrator.set_phase("execute", self.mode, context)
        task_summary = "\n".join(f"{i}. {t.description}" for i, t in enumerate(task_list, 1))
        user_text = f"执行任务清单：\n{task_summary}\n\n原始需求：{original_text}"
        return await self.orchestrator.arun(
            user_text, chat_history=[], callbacks=self._callbacks(), cancel_event=cancel_event
        )

    async def run_verify(self, execution_results: List[dict], local_details: str, context: str, cancel_event=None) -> str:
        """Verify 阶段：可读取 phase_messages 中的原始需求摘要"""
        self.orchestrator.set_phase("verify", self.mode, context)
        result_summary = "\n".join(
            f"- {r.get('task', '')}: {str(r.get('result', ''))[:200]}"
            for r in execution_results
        )
        user_text = (
            f"执行结果摘要：\n{result_summary}\n\n"
            f"本地验证结果：\n{local_details}\n\n"
            "请判断任务是否完成，是否存在明显错误。"
        )
        return await self.orchestrator.arun(
            user_text, list(self.phase_messages), callbacks=self._callbacks(), cancel_event=cancel_event
        )

    # ═══════════════════════════════════════════════════════
    # 敏感操作确认
    # ═══════════════════════════════════════════════════════
    async def _confirm_callback(self, tool_name: str, args: Any) -> bool:
        """Orchestrator 遇到危险命令时回调此方法，阻塞等待用户确认"""
        self._confirm_event = asyncio.Event()
        self._confirm_result = False
        command = args.get("command", "") if isinstance(args, dict) else str(args)
        self.confirm_required.emit(tool_name, command)
        await self._confirm_event.wait()
        return self._confirm_result

    def set_confirm_result(self, confirmed: bool):
        """由外部（MainWindow）调用，恢复被暂停的危险命令确认"""
        self._confirm_result = confirmed
        if self._confirm_event is not None:
            self._confirm_event.set()

    # ═══════════════════════════════════════════════════════
    # 内部回调转发
    # ═══════════════════════════════════════════════════════
    def _on_log(self, msg: str):
        self.log_message.emit(str(msg))

    def _on_tool_end(self, task_id: str, summary: str):
        self.task_finished.emit(task_id, summary)

    def _on_token_usage(self, usage: dict):
        provider = usage.get("provider") or ""
        model = usage.get("model") or ""
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        self.token_used.emit(provider, model, input_tokens, output_tokens)

    def _on_metrics_start(self):
        pass

    def _on_metrics_first_token(self):
        pass

    def _trim_phase_messages(self):
        """滑动窗口：保留最近 6 轮（12 条消息），避免上下文无限膨胀"""
        while len(self.phase_messages) > 12:
            self.phase_messages.pop(0)

    def _callbacks(self) -> Dict[str, Any]:
        """Orchestrator 回调：转发为 Qt 信号"""
        return {
            "log": self._on_log,
            "tool_start": self.task_created.emit,
            "tool_end": self._on_tool_end,
            "tool_executed": self.tool_executed.emit,
            "chunk": self.chunk_ready.emit,
            "round": self.round_advanced.emit,
            "token_usage": self._on_token_usage,
            "error": self.error_occurred.emit,
        }
