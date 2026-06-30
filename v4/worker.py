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
    MetricsEngine, PolicyEngine, Message,
)
from tools import TOOL_MAP, ARUN_MAP
from workers.agent_worker import TOOL_DEFINITIONS
from tools import system as system_tools


class V4Worker(QThread):
    """v4 原生 Worker：八引擎驱动 ReAct 推理循环

    信号接口与旧 AgentWorker 兼容：
    - chunk_ready(str)          → 流式文本块
    - result_ready(str, str)    → (session_id, full_text)
    - error_occurred(str, str)  → (code, detail)
    """

    chunk_ready = Signal(str)
    result_ready = Signal(str, str)
    error_occurred = Signal(str, str)

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
        self._config = ConfigService(config_path="config.yaml")
        self._max_tool_rounds = (
            max_tool_rounds if max_tool_rounds is not None
            else self._config.get_max_tool_rounds(mode_name)
        )
        self._llm_timeout = self._config.get_llm_timeout(mode_name)
        self._tool_timeout = self._config.get_tool_timeout(mode_name)
        self._llm_registry = LLMRegistry("config.yaml", "config.yaml")

    # ── 公共 API ──────────────────────────────────────

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
        """异步推理入口：初始化引擎 → ReAct 循环 → 流式输出。"""
        self._cancel_event.clear()
        self._streaming_buffer = ""

        try:
            cfg = self._config.config
            policy = PolicyEngine(cfg.get("ai_engine", {}))
            metrics = MetricsEngine()
            ctx_engine = ContextEngine(policy_engine=policy, metrics_engine=metrics)

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

            # 构建系统提示
            system_prompt = prompt_engine.build_system_prompt(self.mode_name, "execute")
            if self.project_root:
                system_prompt = prompt_engine.inject_context(
                    system_prompt, f"当前项目目录: {self.project_root}"
                )

            # 组装消息
            messages: List[Message] = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_text),
            ]

            # ── ReAct 循环 ──
            round_count = 0
            reply = ""
            while round_count < self._max_tool_rounds:
                if self._cancel_event.is_set():
                    reply = self._streaming_buffer or "[已取消]"
                    break

                response = await self._invoke_llm(messages)
                if response is None:
                    break  # 错误已通过 error_occurred 上报

                # 检测 tool_calls
                if hasattr(response, "tool_calls") and response.tool_calls:
                    messages.append(Message(
                        role="assistant", content="",
                        tool_calls=response.tool_calls,
                    ))
                    for tc in response.tool_calls:
                        if self._cancel_event.is_set():
                            break
                        tool_result = await tool_engine.call(
                            tc["name"], tc.get("args", {}), "execute"
                        )
                        result_text = (
                            tool_result.result if tool_result.success
                            else f"[工具错误] {tool_result.result}"
                        )
                        messages.append(Message(
                            role="tool", content=result_text,
                            tool_call_id=tc.get("id", ""),
                        ))
                    round_count += 1
                    # 接近上限时强制 LLM 直接回答
                    if self._max_tool_rounds - round_count <= 1:
                        messages.append(Message(
                            role="system",
                            content="工具调用轮次即将用尽，请基于已有工具结果直接回答用户。不要再调用工具。",
                        ))
                    continue

                # 无 tool_calls → 最终回答
                reply = response.content or ""
                if not reply:
                    # 兜底：收集所有工具结果
                    tool_results = [
                        m.content for m in messages if m.role == "tool"
                    ]
                    reply = "\n\n".join(tool_results) if tool_results else "[工具执行完成]"

                self._streaming_buffer = reply
                for line in reply.replace("\r\n", "\n").split("\n"):
                    self.chunk_ready.emit(line + "\n")
                break

            else:
                # 超过最大轮数
                reply = "[已达到最大工具调用轮数]"
                self.chunk_ready.emit(reply + "\n")

            self.result_ready.emit(self.session_id, reply.strip())

        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit("WORKER_RUNTIME", str(e)[:300])

    # ── LLM 调用辅助 ──────────────────────────────────

    async def _invoke_llm(self, messages: List[Message]):
        """调用 LLM 并返回原始 AIMessage（含 tool_calls），支持超时和取消。"""
        llm = self._llm_registry.get_llm(self.model_id)
        # 绑定工具到 LLM
        try:
            from agent_engine.engines import ToolEngine
            allowed_defs = [
                d for d in TOOL_DEFINITIONS
                if d.get("function", {}).get("name") in TOOL_MAP
            ]
            if allowed_defs:
                # 跳过 gemma 系列（不支持 bind_tools）
                model_name = str(llm.model) if hasattr(llm, "model") else ""
                if not any(m in model_name.lower() for m in ("gemma2", "gemma:")):
                    llm = llm.bind_tools(allowed_defs)
        except Exception:
            pass  # bind_tools 失败时降级为纯文本对话

        lc_messages = [m.to_langchain() for m in messages]

        try:
            response = await asyncio.wait_for(
                llm.ainvoke(lc_messages), timeout=self._llm_timeout,
            )
            return response
        except asyncio.TimeoutError:
            self.error_occurred.emit("LLM_TIMEOUT", f"LLM超时 {self._llm_timeout}s")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.error_occurred.emit("LLM_ERROR", str(e)[:300])
        return None
