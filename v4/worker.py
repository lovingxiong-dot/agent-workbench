"""
v4/worker.py — v4 原生 Worker：八引擎驱动的 ReAct 推理循环

设计原则：
- 零绞杀者：不依赖旧 AgentWorker / AgentOrchestrator / AgentSession。
- 八引擎原生驱动：PromptEngine → 系统提示，ContextEngine → 消息组装，
  ToolEngine → 工具绑定与执行，PolicyEngine/MetricsEngine → 配置与观测，
  直接调用 LLM（通过 LLMRegistry）并自行检测 tool_calls、执行 ReAct 循环。
- QThread + asyncio 事件循环：流式输出通过 Signal 回传主线程。
"""
import asyncio
import threading
import traceback
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from services.config_service import ConfigService
from agent_engine.llm_registry import LLMRegistry
from agent_engine.engines import (
    ContextEngine, PromptEngine, InferenceEngine, ToolEngine,
    MetricsEngine, PolicyEngine, PhaseEngine, Message,
)
from tools import TOOL_MAP, ARUN_MAP
from workers.agent_worker import TOOL_DEFINITIONS
from tools import system as system_tools


class V4Worker(QThread):
    """v4 原生 Worker：八引擎驱动 ReAct 推理循环

    信号接口：
    - chunk_ready(str)              → 流式文本块
    - result_ready(str, str)        → (session_id, full_text)
    - error_occurred(str, str)      → (code, detail)
    - phase_changed(str, int)       → (phase_name, task_count)
    - confirm_required(list)        → task_list
    - phase_complete(bool, str)     → (success, message)
    - phase_error(str, str)         → (code, detail)
    """

    chunk_ready = Signal(str)
    result_ready = Signal(str, str)
    error_occurred = Signal(str, str)
    phase_changed = Signal(str, int)
    confirm_required = Signal(list)
    phase_complete = Signal(bool, str)
    phase_error = Signal(str, str)
    tool_called = Signal(str, dict, str, int, bool)  # name, args, result, elapsed_ms, success

    def __init__(
        self,
        mode_name: str,
        model_id: str,
        session_id: str = "",
        project_root: str = "",
        max_tool_rounds: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.mode_name = mode_name
        self.model_id = model_id
        self.session_id = session_id
        self.project_root = project_root or ""

        self._cancel_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._cpu_executor: Optional[ThreadPoolExecutor] = None
        self._loop_ready = threading.Event()
        self._pending_task: Optional[str] = None
        self._streaming_buffer: str = ""

        # 配置
        self._config = ConfigService(config_path="config/config.yaml")
        self._max_tool_rounds = (
            max_tool_rounds if max_tool_rounds is not None
            else self._config.get_max_tool_rounds(mode_name)
        )
        self._llm_timeout = self._config.get_llm_timeout(mode_name)
        self._tool_timeout = self._config.get_tool_timeout(mode_name)
        self._llm_registry = LLMRegistry("config/config.yaml", "config/config.yaml")

        # Phase 确认等待机制（QThread 内使用 asyncio.Event）
        self._confirm_event: Optional[asyncio.Event] = None
        self._confirm_confirmed: bool = False
        self._task_list: List[str] = []

    # ── 公共 API ──────────────────────────────────────

    def confirm(self, confirmed: bool):
        """用户确认/取消当前 phase（由 WorkerManager 桥接 UserConfirmEvent 调用）。"""
        self._confirm_confirmed = confirmed
        if self._confirm_event:
            try:
                self._confirm_event.set()
            except Exception:
                pass

    def submit(self, user_text: str):
        """将用户文本提交到 Worker 内部事件循环。"""
        if not self._loop_ready.is_set() or self._loop is None:
            self._pending_task = user_text
            return
        asyncio.run_coroutine_threadsafe(self._run(user_text), self._loop)

    def stop(self):
        """停止 Worker：取消任务，退出事件循环。"""
        self._cancel_event.set()
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
        self.quit()

    def cancel_task(self):
        """仅取消当前任务，不退出事件循环。"""
        self._cancel_event.set()

    # ── QThread 入口 ──────────────────────────────────

    def run(self):
        try:
            self._cpu_executor = ThreadPoolExecutor(
                max_workers=4, thread_name_prefix=f"v4w_{self.session_id[-8:]}_",
            )
            # 注入 cpu_executor 到需要它的工具模块
            try:
                from tools.external_apis import set_cpu_executor
                set_cpu_executor(self._cpu_executor)
            except Exception:
                pass
            try:
                from tools.quant import set_cpu_executor as set_quant_executor
                set_quant_executor(self._cpu_executor)
            except Exception:
                pass

            # 同步 project_root 到文件工具
            if self.project_root and hasattr(system_tools, "set_project_root"):
                system_tools.set_project_root(self.project_root)

            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._loop_ready.set()

            if self._pending_task:
                asyncio.run_coroutine_threadsafe(
                    self._run(self._pending_task), self._loop
                )
                self._pending_task = None

            self._loop.run_forever()
        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit("WORKER_RUNTIME", str(e)[:300])
        finally:
            if self._cpu_executor:
                self._cpu_executor.shutdown(wait=False, cancel_futures=True)

    # ── 推理核心 ──────────────────────────────────────

    async def _run(self, user_text: str):
        """异步推理入口：ask 保持直接执行；plan/craft 走 Phase 流程。"""
        self._cancel_event.clear()
        self._streaming_buffer = ""
        self._task_list = []

        try:
            if self.mode_name == "ask":
                await self._execute_loop(user_text)
            else:
                await self._run_phased(user_text)
        except Exception as e:
            traceback.print_exc()
            self.phase_error.emit("WORKER_RUNTIME", str(e)[:300])

    async def _run_phased(self, user_text: str):
        """Phase 驱动流程：analyze → confirm → execute → verify → archive。"""
        phase_engine = PhaseEngine()
        phases = phase_engine._definitions.get(
            self.mode_name, ["analyze", "archive"]
        )
        if not phases:
            phases = ["analyze", "archive"]

        current_phase = phases[0]
        phase_idx = 0

        while current_phase:
            if self._cancel_event.is_set():
                self.phase_complete.emit(False, "用户取消了任务")
                return

            self.phase_changed.emit(current_phase, len(self._task_list))

            if current_phase == "analyze":
                await self._phase_analyze(user_text)
            elif current_phase == "confirm":
                confirmed = await self._phase_confirm()
                if not confirmed:
                    self.phase_complete.emit(False, "用户取消了任务执行")
                    return
            elif current_phase == "execute":
                await self._phase_execute(user_text)
            elif current_phase == "verify":
                await self._phase_verify()
            elif current_phase == "archive":
                # archive 只是收尾占位
                pass

            phase_idx += 1
            if phase_idx >= len(phases):
                break
            current_phase = phases[phase_idx]

        self.phase_changed.emit("archive", len(self._task_list))
        self.phase_complete.emit(True, "")

    async def _phase_analyze(self, user_text: str):
        """分析阶段：让 LLM 输出任务清单，并解析为 task_list。"""
        engines = self._init_engines()
        prompt_engine = engines["prompt_engine"]
        system_prompt = prompt_engine.build_system_prompt(self.mode_name, "analyze")
        if self.project_root:
            system_prompt = prompt_engine.inject_context(
                system_prompt, f"当前项目目录: {self.project_root}"
            )

        messages: List[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_text),
        ]

        response = await self._invoke_llm(messages, phase="analyze")
        if response is None:
            raise RuntimeError("analyze phase LLM 调用失败")

        reply = response.content or ""
        self._task_list = self._extract_task_list(reply)
        # 让分析结果也出现在聊天区
        self._emit_reply(reply)

    async def _phase_confirm(self) -> bool:
        """确认阶段：发送任务清单并阻塞等待用户确认。"""
        if not self._task_list:
            # 没有任务则跳过确认
            return True
        self.confirm_required.emit(list(self._task_list))

        self._confirm_event = asyncio.Event()
        self._confirm_confirmed = False
        try:
            await asyncio.wait_for(self._confirm_event.wait(), timeout=600.0)
        except asyncio.TimeoutError:
            return False
        finally:
            self._confirm_event = None
        return self._confirm_confirmed

    async def _phase_execute(self, user_text: str):
        """执行阶段：复用 ReAct 循环，并将任务清单作为上下文注入。"""
        if self._task_list:
            context = "## 已确认任务清单\n" + "\n".join(
                f"{i+1}. {t}" for i, t in enumerate(self._task_list)
            )
            if self.project_root:
                context += f"\n\n当前项目目录: {self.project_root}"
            await self._execute_loop(user_text, extra_context=context)
        else:
            await self._execute_loop(user_text)

    async def _phase_verify(self):
        """验证阶段：对 execute 结果进行验证性总结。"""
        result_text = self._streaming_buffer or ""
        if not result_text:
            return

        engines = self._init_engines()
        prompt_engine = engines["prompt_engine"]
        system_prompt = prompt_engine.build_system_prompt(self.mode_name, "verify")
        messages: List[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"请验证以下执行结果是否完成用户需求，并给出简要总结。\n\n{result_text}"),
        ]

        response = await self._invoke_llm(messages, phase="verify")
        if response is not None and response.content:
            self._emit_reply("\n\n## 验证总结\n" + response.content)

    def _init_engines(self) -> Dict[str, Any]:
        """初始化并返回八引擎实例（不含 PhaseEngine）。"""
        cfg = self._config.config
        policy = PolicyEngine(cfg.get("ai_engine", {}))
        metrics = MetricsEngine()
        ContextEngine(policy_engine=policy, metrics_engine=metrics)

        prompt_engine = PromptEngine(
            base_prompts={
                m: c.get("system_prompt", "")
                for m, c in cfg.get("manual_modes", {}).items()
            },
            user_rules=cfg.get("user_rules", []),
            app_version=cfg.get("app", {}).get("version", "v4.x"),
            model_name=self.model_id,
        )
        tool_engine = ToolEngine(
            tool_map=TOOL_MAP,
            tool_definitions=TOOL_DEFINITIONS,
            policy_engine=policy,
            cpu_executor=self._cpu_executor,
            arun_map=ARUN_MAP,
        )
        return {
            "policy": policy,
            "metrics": metrics,
            "prompt_engine": prompt_engine,
            "tool_engine": tool_engine,
        }

    async def _execute_loop(self, user_text: str, extra_context: str = ""):
        """ReAct 执行循环：ask 与 execute phase 共用。"""
        engines = self._init_engines()
        prompt_engine = engines["prompt_engine"]
        tool_engine = engines["tool_engine"]

        system_prompt = prompt_engine.build_system_prompt(self.mode_name, "execute")
        if self.project_root:
            system_prompt = prompt_engine.inject_context(
                system_prompt, f"当前项目目录: {self.project_root}"
            )
        if extra_context:
            system_prompt = prompt_engine.inject_context(system_prompt, extra_context)

        messages: List[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_text),
        ]

        round_count = 0
        reply = ""
        while round_count < self._max_tool_rounds:
            if self._cancel_event.is_set():
                reply = self._streaming_buffer or "[已取消]"
                break

            response = await self._invoke_llm(messages, phase="execute")
            if response is None:
                break

            if hasattr(response, "tool_calls") and response.tool_calls:
                messages.append(Message(
                    role="assistant", content="",
                    tool_calls=response.tool_calls,
                ))
                for tc in response.tool_calls:
                    if self._cancel_event.is_set():
                        break
                    t0 = time.monotonic()
                    tool_result = await tool_engine.call(
                        tc["name"], tc.get("args", {}), "execute"
                    )
                    elapsed_ms = int((time.monotonic() - t0) * 1000)
                    result_text = (
                        tool_result.result if tool_result.success
                        else f"[工具错误] {tool_result.result}"
                    )
                    self.tool_called.emit(
                        tc["name"], tc.get("args", {}), result_text,
                        elapsed_ms, tool_result.success,
                    )
                    messages.append(Message(
                        role="tool", content=result_text,
                        tool_call_id=tc.get("id", ""),
                    ))
                round_count += 1
                if self._max_tool_rounds - round_count <= 1:
                    messages.append(Message(
                        role="system",
                        content="工具调用轮次即将用尽，请基于已有工具结果直接回答用户。不要再调用工具。",
                    ))
                continue

            reply = response.content or ""
            if not reply:
                tool_results = [m.content for m in messages if m.role == "tool"]
                reply = "\n\n".join(tool_results) if tool_results else "[工具执行完成]"

            self._emit_reply(reply)
            break

        else:
            reply = "[已达到最大工具调用轮数]"
            self._emit_reply(reply)

        self.result_ready.emit(self.session_id, reply.strip())

    def _emit_reply(self, text: str):
        """将文本通过 chunk_ready 流式发送，并保存到缓冲区。"""
        self._streaming_buffer = text
        for line in text.replace("\r\n", "\n").split("\n"):
            self.chunk_ready.emit(line + "\n")

    def _extract_task_list(self, text: str) -> List[str]:
        """从 analyze phase 的文本回复中解析任务清单。"""
        tasks: List[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            # 匹配：1. xxx、- xxx、* xxx、- [ ] xxx
            if line[0].isdigit() and "." in line[:3]:
                tasks.append(line.split(".", 1)[-1].strip())
            elif line.startswith(("- ", "* ", "- [ ] ", "- [x] ")):
                task = line
                for prefix in ("- [ ] ", "- [x] ", "- ", "* "):
                    if task.startswith(prefix):
                        task = task[len(prefix):]
                        break
                tasks.append(task.strip())
        return tasks

    # ── LLM 调用辅助 ──────────────────────────────────

    async def _invoke_llm(self, messages: List[Message], phase: str = "execute"):
        """调用 LLM 并返回原始 AIMessage（含 tool_calls），支持超时和取消。"""
        llm = self._llm_registry.get_llm(self.model_id)
        # 仅 execute phase 绑定工具；analyze/verify 只输出文本计划/验证总结
        if phase == "execute":
            try:
                from agent_engine.engines import ToolEngine
                tool_engine = ToolEngine(tool_map=TOOL_MAP, tool_definitions=TOOL_DEFINITIONS)
                llm = tool_engine.bind_for_phase(phase, llm)
            except Exception:
                pass  # bind_tools 失败时降级为纯文本对话

        lc_messages = [m.to_langchain() for m in messages]

        try:
            response = await asyncio.wait_for(
                llm.ainvoke(lc_messages), timeout=self._llm_timeout,
            )
            return response
        except asyncio.TimeoutError:
            if phase == "execute":
                self.error_occurred.emit("LLM_TIMEOUT", f"LLM超时 {self._llm_timeout}s")
            else:
                self.phase_error.emit(f"{phase.upper()}_TIMEOUT", f"{phase}阶段LLM超时 {self._llm_timeout}s")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if phase == "execute":
                self.error_occurred.emit("LLM_ERROR", str(e)[:300])
            else:
                self.phase_error.emit(f"{phase.upper()}_ERROR", str(e)[:300])
        return None
