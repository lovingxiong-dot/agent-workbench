"""v5 聊天 Worker：隔离底层 AgentSession 与 V5 适配器。

本文件仅包含 `_ChatWorker`，负责在独立线程中复用 AgentSession，
支持加载历史消息与流式输出。`V5Adapter` 从本模块导入该类。
"""
import asyncio
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from PySide6.QtCore import Signal, QThread

from agent_engine.agent_session import AgentSession
from agent_engine.orchestrator import OrchestratorCancelledError
from tools import TOOL_MAP, ARUN_MAP
from workers.agent_worker import AgentWorker, TOOL_DEFINITIONS


class _ChatWorker(QThread):
    """V5 专属聊天 Worker：在独立线程中复用 AgentSession，支持加载历史与流式输出。"""

    chunk_ready = Signal(str)
    result_ready = Signal(str, str)  # session_id, full_text
    error_occurred = Signal(str, str)
    tool_executed = Signal(str, dict, str, int)  # name, args, result, elapsed_ms
    log_message = Signal(str)
    confirm_required = Signal(str, str)

    def __init__(
        self,
        session_id: str,
        mode: str,
        llm,
        system_prompt: str,
        user_rules: List[str],
        max_tool_rounds: int,
        task_timeout: float,
        llm_timeout: float,
        tool_timeout: float,
        project_root: str,
        workspace_context: str,
        app_version: str,
        parent=None,
    ):
        super().__init__(parent)
        self.session_id = session_id
        self.mode = mode
        self.llm = llm
        self.system_prompt = system_prompt
        self.user_rules = user_rules or []
        self.max_tool_rounds = max(1, int(max_tool_rounds))
        self.task_timeout = max(1.0, float(task_timeout))
        self.llm_timeout = max(5.0, float(llm_timeout))
        self.tool_timeout = max(5.0, float(tool_timeout))
        self.project_root = project_root
        self.workspace_context = workspace_context
        self.app_version = app_version

        self._cancel_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._session: Optional[AgentSession] = None
        self._loop_ready = threading.Event()
        self._pending: List[tuple] = []
        self._cpu_executor: Optional[ThreadPoolExecutor] = None

    # ── 公共接口（任意线程安全） ──────────────────────────────────
    def enter(self, messages: List[dict]):
        self._pending.append(("enter", messages))
        self._flush_if_ready()

    def send(self, user_text: str, context: str = ""):
        self._pending.append(("send", user_text, context))
        self._flush_if_ready()

    def stop(self):
        self._cancel_event.set()
        if self._session is not None:
            self._session.set_confirm_result(False)
        if self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
        self.quit()

    def confirm(self, confirmed: bool):
        """用户确认/取消危险命令。"""
        if self._session is not None:
            self._session.set_confirm_result(confirmed)

    def reset_cancel(self):
        self._cancel_event.clear()

    # ── QThread 入口 ────────────────────────────────────────────
    def run(self):
        try:
            self._cpu_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix=f"v5_{self.session_id[:8]}_")
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            from tools import system as system_tools
            if self.project_root and hasattr(system_tools, "set_project_root"):
                system_tools.set_project_root(self.project_root)

            self._session = AgentSession(
                llm=self.llm,
                tool_map=TOOL_MAP,
                tool_definitions=TOOL_DEFINITIONS,
                mode=self.mode,
                project_root=self.project_root,
                system_prompt=self.system_prompt,
                user_rules=self.user_rules,
                max_tool_rounds=self.max_tool_rounds,
                app_version=self.app_version,
                llm_timeout=self.llm_timeout,
                tool_timeout=self.tool_timeout,
                workspace_context=self.workspace_context,
                cpu_executor=self._cpu_executor,
                arun_map=ARUN_MAP,
            )
            self._connect_session_signals()
            self._loop_ready.set()
            self._flush_pending()
            self._loop.run_forever()
        except Exception as ex:
            self.error_occurred.emit("WORKER_RUNTIME", str(ex))
            traceback.print_exc()
        finally:
            self._cleanup()

    # ── 内部执行 ────────────────────────────────────────────────
    async def _run_send(self, user_text: str, context: str):
        self.reset_cancel()
        try:
            self._session.add_user_message(user_text)
            _, full_text = await asyncio.wait_for(
                self._session.run_analyze(user_text, context, cancel_event=self._cancel_event),
                timeout=self.task_timeout,
            )
            self._session.add_assistant_message(full_text)
            self.result_ready.emit(self.session_id, full_text)
        except asyncio.TimeoutError:
            self.error_occurred.emit("TASK_TIMEOUT", f"任务超过 {self.task_timeout:.0f} 秒")
            self.result_ready.emit(self.session_id, "")
        except OrchestratorCancelledError:
            self.result_ready.emit(self.session_id, "[已取消]")
        except Exception as ex:
            traceback.print_exc()
            self.error_occurred.emit("SEND_ERROR", str(ex))
            self.result_ready.emit(self.session_id, "")

    # ── 信号连接 ────────────────────────────────────────────────
    def _connect_session_signals(self):
        session = self._session
        session.chunk_ready.connect(self.chunk_ready.emit)
        session.tool_executed.connect(self.tool_executed.emit)
        session.log_message.connect(self.log_message.emit)
        session.error_occurred.connect(self.error_occurred.emit)
        session.confirm_required.connect(self.confirm_required.emit)

    def _flush_if_ready(self):
        if self._loop_ready.is_set():
            self._flush_pending()

    def _flush_pending(self):
        if not self._pending or self._loop is None:
            return
        items = self._pending[:]
        self._pending.clear()
        for item in items:
            kind = item[0]
            try:
                if kind == "enter":
                    _, messages = item
                    self._session.enter(self.session_id, messages)
                elif kind == "send":
                    _, user_text, context = item
                    asyncio.run_coroutine_threadsafe(
                        self._run_send(user_text, context), self._loop
                    )
            except Exception as ex:
                traceback.print_exc()
                self.error_occurred.emit("WORKER_FLUSH", str(ex))

    def _cleanup(self):
        self._loop_ready.clear()
        self._pending.clear()
        if self._session is not None:
            try:
                self._session.deleteLater()
            except Exception:
                pass
            self._session = None
        if self._cpu_executor is not None:
            try:
                if self._cancel_event.is_set():
                    self._cpu_executor.shutdown(wait=False, cancel_futures=True)
                else:
                    self._cpu_executor.shutdown(wait=True)
            except Exception:
                pass
            self._cpu_executor = None
        if self._loop is not None:
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None
