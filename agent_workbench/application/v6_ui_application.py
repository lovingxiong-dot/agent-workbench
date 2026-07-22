"""application/v6_ui_application.py — v6/ui 纯 UI 设计的 Application 编排入口。

Phase 2-B：将 v6/ui Presentation Foundation 接入 Runtime 数据流。
Phase 2-D.1：使用 PresentationRuntime + RendererRegistry 替代手动绑定。

职责（仅 4 项）：
  1. Runtime 生命周期：创建 WorkbenchController、启动/停止 Runtime
  2. UI 装配：接收 v6/ui 三栏组件引用
  3. Renderer 注册：通过 PresentationRuntime → RendererRegistry 注册 V6UIRenderer
  4. 初始状态加载：通过 PresentationRuntime.pipeline 转换数据

不负责（已移出）：
  - Session 管理（WorkbenchController 已有 API）
  - Agent 切换（WorkbenchController.switch_agent()）
  - Model 切换（WorkbenchController.switch_model()）
  - 文件操作（RightPanel 自身处理）
  - 信号映射逻辑（归 event_renderer / shell_adapter）
  - 事件分发（归 PresentationRuntime）

约束：
  ✓ 使用 WorkbenchController（非 WorkbenchUIController）
  ✓ 使用 PresentationRuntime + RendererRegistry
  ✓ 使用 RuntimeRequestSource + action_id（非 text 伪装命令）
  ✓ 不穿透 v6/ui 私有成员
  ✗ 不导入 WorkbenchUIController
  ✗ 不修改 v6/ui 布局/视觉设计
  ✗ 不修改 Runtime Kernel
  ✗ 不修改 Shell Contract
"""
from __future__ import annotations

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.interaction.request import RuntimeRequest, RuntimeRequestSource

from agent_workbench.presentation.runtime import PresentationRuntime
from agent_workbench.presentation.renderers.v6_ui.event_renderer import V6UIEventRenderer
from agent_workbench.presentation.renderers.v6_ui.shell_adapter import V6UIShellAdapter
from agent_workbench.presentation.renderers.v6_ui.renderer import V6UIRenderer


class V6UIApplication:
    """v6/ui 纯 UI 设计的 Application 编排器。

    Application 层是唯一合法的 Runtime 接触点。
    不拥有 UI 行为，不拥有 Renderer 内部逻辑。
    """

    def __init__(
        self,
        left_panel,
        chat_area,
        right_panel,
        config_path: str | None = None,
    ) -> None:
        # ── v6/ui 组件引用（Presentation Foundation）──
        self._left = left_panel
        self._chat = chat_area
        self._right = right_panel

        # ── Runtime 入口 ──
        self._controller = WorkbenchController(config_path=config_path)
        self._controller.start()

        # ── PresentationRuntime（Phase 2-D.1）──
        self._presentation = PresentationRuntime()

        # ── Renderer 创建并注册到 RendererRegistry ──
        event_renderer = V6UIEventRenderer(
            chat_area=self._chat,
            left_panel=self._left,
            right_panel=self._right,
        )
        shell_adapter = V6UIShellAdapter(
            left_panel=self._left,
            chat_area=self._chat,
            right_panel=self._right,
        )
        v6_renderer = V6UIRenderer(
            event_renderer=event_renderer,
            shell_adapter=shell_adapter,
        )
        self._presentation.register_renderer("v6", v6_renderer)
        self._presentation.activate_renderer("v6")

        # ── 绑定 PresentationRuntime 到 Interaction Boundary ──
        # PresentationRuntime.render() 兼容 UIEventRenderer 协议，
        # InteractionLayer 调用 render(event) → dispatch_event(event) → 活跃 Renderer
        self._controller.interaction_layer.set_renderer(self._presentation)

        # ── 连接 v6/ui 信号 → InteractionLayer ──
        self._connect_signals()

        # ── 加载初始状态 ──
        self._load_initial_state()

    # ═══════════════════════════════════════════════════════════════
    # 信号连接
    # ═══════════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        """连接 v6/ui 组件信号 → InteractionLayer。

        原则：
        - 聊天消息：RuntimeRequest(GLOBAL_CHAT, text=...)
        - 非聊天命令：RuntimeRequest(COMMAND_BAR, action_id=...)
        - 不使用 text 伪装命令
        """
        il = self._controller.interaction_layer

        # ── ChatArea → InteractionLayer ──
        self._chat.send_msg.connect(
            lambda text: il.submit_request(
                RuntimeRequest(
                    source=RuntimeRequestSource.GLOBAL_CHAT,
                    text=text,
                    session_id=self._controller.session_id,
                )
            )
        )
        self._chat.stop_msg.connect(
            lambda: il.submit_request(
                RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    action_id="stop_generation",
                )
            )
        )

        # ── LeftPanel → InteractionLayer ──
        self._left.session_selected.connect(self._on_session_selected)
        self._left.new_session_requested.connect(self._on_new_session)
        self._left.session_action.connect(self._on_session_action)

        # ── RightPanel → InteractionLayer ──
        self._right.terminal_command.connect(
            lambda cmd: il.submit_request(
                RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    text=cmd,
                    action_id="terminal_execute",
                )
            )
        )

    # ═══════════════════════════════════════════════════════════════
    # 初始状态加载
    # ═══════════════════════════════════════════════════════════════

    def _load_initial_state(self) -> None:
        """加载初始状态：会话列表、Agent 列表、模型列表。

        通过 PresentationRuntime.pipeline 转换数据。
        """
        pipeline = self._presentation.pipeline

        # ── 会话列表 → NavigationGroup → LeftPanel ──
        raw_sessions = self._get_raw_sessions()
        if raw_sessions:
            groups = pipeline.sessions_to_navigation_groups(raw_sessions)
            self._presentation.update_navigation(groups)

    def _get_raw_sessions(self) -> list[dict]:
        """通过 InteractionLayer 拉取会话原始数据。

        Phase 2-D.2.1: 不再直接访问 runtime.module_registry，
        所有 session / conversation 操作必须经过 interaction_layer。
        """
        raw: list[dict] = []
        try:
            groups = self._controller.interaction_layer.list_conversation_groups()
            for _gid, _title, sessions in groups:
                raw.extend(sessions)
        except Exception:
            pass
        return raw

    # ═══════════════════════════════════════════════════════════════
    # Session 操作
    # ═══════════════════════════════════════════════════════════════

    def _on_session_selected(self, sid: str) -> None:
        """会话选中 → 加载历史消息到 ChatArea。"""
        pipeline = self._presentation.pipeline
        try:
            session = self._controller.interaction_layer.get_session_metadata(sid)
            title = session.get("title", "") if session else ""
            subtitle = ""
            raw_messages = self._controller.get_state().get("messages", [])
            state = pipeline.messages_to_workspace_state(
                title=title,
                subtitle=subtitle,
                raw_messages=raw_messages,
            )
            self._presentation.update_workspace(state)
        except Exception:
            pass

    def _on_new_session(self) -> None:
        """新建会话。"""
        try:
            sid = self._controller.interaction_layer.create_conversation()
            if sid:
                self._left.set_active_session(sid)
        except Exception:
            pass

    def _on_session_action(self, action: str, sid: str) -> None:
        """会话操作（删除/重命名/置顶）。"""
        if action == "delete":
            try:
                self._controller.interaction_layer.delete_conversation(sid)
                # 刷新会话列表
                raw = self._get_raw_sessions()
                if raw:
                    pipeline = self._presentation.pipeline
                    groups = pipeline.sessions_to_navigation_groups(raw)
                    self._presentation.update_navigation(groups)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════════════════════════

    def shutdown(self) -> None:
        """停止 Runtime 并清理 PresentationRuntime。"""
        self._controller.interaction_layer.set_renderer(None)
        self._presentation.shutdown()
        self._controller.stop()