"""v5 适配器：隔离底层共享核心（core / agent_engine / workers）与 V5 纯 Python 回调。

本文件是 v5/service 中唯一允许导入 PySide6 的文件。
职责：
- 管理 AgentWorker 生命周期（按会话复用，会话切换不停止）；
- 将用户发送、停止、终端命令等操作转发到底层共享模块；
- 将底层 Qt 信号转换为普通 Python 回调，上层 ChatService 不感知 Qt。
"""
import asyncio
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Signal, QThread

from agent_engine.agent_session import AgentSession
from agent_engine.llm_registry import LLMRegistry
from agent_engine.orchestrator import OrchestratorCancelledError
from core.event_bus import MessageBus
from tools import TOOL_MAP, ARUN_MAP
from workers.agent_worker import AgentWorker
from workers.terminal_worker import TerminalWorker


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
                tool_definitions=AgentWorker.TOOL_DEFINITIONS,
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


class V5Adapter(QObject):
    """V5 业务适配器：连接 UI 回调与根目录共享核心。

    - 仅依赖根目录平行共享核心模块；
    - 通过底层 Qt 信号隔离，对外仅暴露普通 Python 回调；
    - 会话级 Worker 复用，切换会话不中断后台任务。
    """

    def __init__(
        self,
        config,
        session_service,
        message_bus: Optional[MessageBus] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._session_service = session_service
        self._bus = message_bus
        self._llm_registry = LLMRegistry("config/config.yaml", "config/config.yaml")
        self._engines = self._init_engines()

        self._workers: Dict[str, _ChatWorker] = {}
        self._terminal_worker: Optional[TerminalWorker] = None

        self._on_user: Callable[[str], None] = lambda text: None
        self._on_ai: Callable[[str, str], None] = lambda text, phase: None
        self._on_chunk: Callable[[str], None] = lambda text: None
        self._on_stream_end: Callable[[], None] = lambda: None
        self._on_terminal: Callable[[str], None] = lambda text: None
        self._on_open_file: Callable[[str], None] = lambda path: None
        self._on_load_url: Callable[[str], None] = lambda url: None
        self._on_switch_tab: Callable[[str], None] = lambda tab: None

        if self._bus is not None:
            self._bind_bus()

    # ── 回调设置 ────────────────────────────────────────────────
    def set_callbacks(
        self,
        on_user: Callable[[str], None] = None,
        on_ai: Callable[[str, str], None] = None,
        on_chunk: Callable[[str], None] = None,
        on_stream_end: Callable[[], None] = None,
        on_terminal: Callable[[str], None] = None,
        on_open_file: Callable[[str], None] = None,
        on_load_url: Callable[[str], None] = None,
        on_switch_tab: Callable[[str], None] = None,
    ):
        if on_user:
            self._on_user = on_user
        if on_ai:
            self._on_ai = on_ai
        if on_chunk:
            self._on_chunk = on_chunk
        if on_stream_end:
            self._on_stream_end = on_stream_end
        if on_terminal:
            self._on_terminal = on_terminal
        if on_open_file:
            self._on_open_file = on_open_file
        if on_load_url:
            self._on_load_url = on_load_url
        if on_switch_tab:
            self._on_switch_tab = on_switch_tab

    # ── 用户操作入口 ────────────────────────────────────────────
    def emit_user_send(
        self,
        session_id: str,
        text: str,
        model: str,
        mode: str,
        session_type: str,
        project_path: str,
    ):
        if not session_id or not text.strip():
            return

        self._session_service.add_message(session_id, "user", text)
        self._on_user(text)

        worker = self._get_or_create_worker(session_id, model, mode, session_type, project_path)
        worker.reset_cancel()
        worker.send(text, self._build_context(project_path))

    def emit_user_stop(self, session_id: str):
        worker = self._workers.get(session_id)
        if worker is not None:
            worker.stop()

    def emit_session_create(
        self,
        session_type: str,
        model: str,
        mode: str,
        project_path: str,
    ):
        """保留兼容入口；V5 Controller 已直接调用 SessionService，本方法供 chat_service 使用。"""
        self._session_service.create_session(
            session_type=session_type,
            mode=mode,
            model=model,
            project_path=project_path,
        )

    def emit_session_switch(self, session_id: str):
        worker = self._workers.get(session_id)
        if worker is not None:
            messages = self._session_service.list_messages(session_id)
            worker.enter(messages)

    def emit_session_delete(self, session_id: str):
        worker = self._workers.pop(session_id, None)
        if worker is not None:
            worker.stop()
            worker.wait(3000)

    def emit_session_rename(self, session_id: str, new_title: str):
        self._session_service.rename_session(session_id, new_title)

    def emit_session_pin(self, session_id: str, pinned: bool):
        self._session_service.pin_session(session_id, pinned)

    # ── 终端命令 ────────────────────────────────────────────────
    def run_terminal_command(self, command: str, cwd: str = ""):
        if self._terminal_worker and self._terminal_worker.isRunning():
            self._terminal_worker.stop()
            self._terminal_worker.wait(1000)
        self._terminal_worker = TerminalWorker(command, cwd or None)
        self._terminal_worker.output.connect(self._on_terminal)
        self._terminal_worker.start()

    # ── 内部辅助 ────────────────────────────────────────────────
    def _get_or_create_worker(
        self,
        session_id: str,
        model: str,
        mode: str,
        session_type: str,
        project_path: str,
    ) -> _ChatWorker:
        worker = self._workers.get(session_id)
        if worker is not None and worker.isRunning():
            return worker

        llm = self._get_llm(model)
        system_prompt = self._get_system_prompt(mode)
        user_rules = self._config.get("user_rules", []) or []
        agent_cfg = self._config.get("agent", {}) or {}
        mode_cfg = agent_cfg.get(mode, {}) if isinstance(agent_cfg, dict) else {}

        worker = _ChatWorker(
            session_id=session_id,
            mode=mode,
            llm=llm,
            system_prompt=system_prompt,
            user_rules=user_rules,
            max_tool_rounds=mode_cfg.get("max_tool_rounds", 8),
            task_timeout=mode_cfg.get("task_timeout", 120.0),
            llm_timeout=mode_cfg.get("llm_timeout", 90.0),
            tool_timeout=mode_cfg.get("tool_timeout", 30.0),
            project_root=project_path,
            workspace_context=self._build_workspace_context(session_id, project_path),
            app_version=self._config.get("app.version", "v5.0"),
            parent=self,
        )
        worker.chunk_ready.connect(self._on_chunk)
        worker.result_ready.connect(self._on_result)
        worker.error_occurred.connect(self._on_error)
        worker.tool_executed.connect(self._on_tool_executed)
        worker.log_message.connect(self._on_terminal)
        worker.confirm_required.connect(self._on_confirm_required)
        worker.finished.connect(lambda: self._workers.pop(session_id, None))

        messages = self._session_service.list_messages(session_id)
        worker.enter(messages)
        worker.start()
        self._workers[session_id] = worker
        return worker

    def _on_result(self, session_id: str, full_text: str):
        if full_text and full_text != "[已取消]":
            self._session_service.add_message(session_id, "ai", full_text)
        self._on_stream_end()
        self._on_ai(full_text, "")

    def _on_error(self, code: str, detail: str):
        self._on_terminal(f"[错误] {code}: {detail}")

    def _on_tool_executed(self, name: str, args: dict, result: str, elapsed_ms: int):
        self._on_terminal(f"[工具] {name}({args}) -> {result[:100]} ({elapsed_ms}ms)")

    def _on_confirm_required(self, tool_name: str, command: str):
        self._on_terminal(f"[确认] {tool_name}: {command}")

    def _get_llm(self, model: str):
        try:
            return self._llm_registry.get_llm(model)
        except Exception:
            # 回退到第一个可用 provider
            providers = self._llm_registry.list_providers()
            if providers:
                return self._llm_registry.get_llm(next(iter(providers)))
            raise

    def _get_system_prompt(self, mode: str) -> str:
        raw = self._config.raw_config
        modes = raw.get("manual_modes", {}) or {}
        return modes.get(mode, {}).get("system_prompt", "")

    def _build_workspace_context(self, session_id: str, project_path: str) -> str:
        parts = []
        if project_path:
            parts.append(f"当前项目路径: {project_path}")
        if session_id:
            parts.append(f"会话 ID: {session_id[:8]}")
        return "\n".join(parts)

    def _init_engines(self) -> Dict[str, object]:
        raw = self._config.raw_config
        try:
            from agent_engine.engines import (
                PromptEngine, InferenceEngine, ToolEngine,
                MemoryEngine, MetricsEngine, PolicyEngine,
            )
            policy = PolicyEngine(raw.get("ai_engine", {}))
            metrics = MetricsEngine()
            return {
                "registry": self._llm_registry,
                "policy": policy,
                "metrics": metrics,
                "prompt": PromptEngine(
                    base_prompts={m: c.get("system_prompt", "") for m, c in raw.get("manual_modes", {}).items()},
                    user_rules=raw.get("user_rules", []),
                    app_version=raw.get("app", {}).get("version", "v5.0"),
                ),
                "inference": InferenceEngine(policy_engine=policy, metrics_engine=metrics, llm_registry=self._llm_registry),
                "tool": ToolEngine(),
                "memory": MemoryEngine(
                    app_root=self._config.get_app_root(),
                    config=raw.get("self_context", {}),
                    policy_engine=policy,
                ),
            }
        except Exception:
            return {}

    def _bind_bus(self):
        self._bus.subscribe_namespace("ui", self._on_ui_event)

    def _on_ui_event(self, event):
        name = getattr(event, "name", "")
        if name == "open_file":
            self._on_open_file(getattr(event, "path", ""))
        elif name == "load_url":
            self._on_load_url(getattr(event, "url", ""))
        elif name == "right_panel_tab":
            self._on_switch_tab(getattr(event, "tab_name", ""))
