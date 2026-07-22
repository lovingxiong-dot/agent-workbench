"""presentation/runtime.py — Presentation Runtime 生命周期服务。

Phase 2-C.2：将 Presentation 从静态工具箱升级为生命周期服务。

职责：
  - Presentation 生命周期管理（start/shutdown）
  - Renderer 生命周期协调（注册/激活/停用）
  - InteractionEvent 分发（Runtime → Renderer）
  - Shell State 同步（Nav/Workspace/Inspector/Command）
  - 数据转换编排（owns PresentationPipeline）

不负责：
  - UI 创建（归 Application 层）
  - Runtime 执行（归 agent_workbench/runtime/）
  - Widget 管理（归 v6/ui）

约束：
  ✓ 依赖：PresentationProtocols（protocols/） + ShellContract（shell/）
  ✗ 禁止：PySide6、v6/ui、QWidget、ChatArea、LeftPanel、RightPanel
  ✗ 禁止：Runtime Implementation（engine, executor, session, llm, tool）
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Protocol

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent
from agent_workbench.presentation.protocols.interaction.renderer import UIEventRenderer
from agent_workbench.presentation.shell.integration import PresentationPipeline
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    NavigationItem,
    ShellProtocol,
    WorkspaceState,
)

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════
# Renderer Lifecycle Protocol
# ═══════════════════════════════════════════════════════════════════

class RendererProtocol(Protocol):
    """Renderer 生命周期协议。

    Renderer 是 UI 技术栈无关的生命周期抽象。
    每个具体 Renderer（Qt / Web / CLI / Mobile）必须实现此协议。

    与 UIEventRenderer 的区别：
    - UIEventRenderer：纯事件消费（render 方法）
    - RendererProtocol：生命周期管理 + 事件消费 + 状态同步

    Phase 2-C.3 将扩展为 RendererRegistry 的注册单元。
    """

    def start(self) -> None:
        """启动 Renderer。

        调用时机：PresentationRuntime.start() 时。
        具体实现：创建 UI 组件、连接信号、初始化显示。
        """
        ...

    def stop(self) -> None:
        """停止 Renderer。

        调用时机：PresentationRuntime.shutdown() 或切换 Renderer 时。
        具体实现：清理 UI 组件、断开信号、释放资源。
        """
        ...

    def render(self, event: InteractionEvent) -> None:
        """渲染一个 InteractionEvent（兼容 UIEventRenderer 协议）。

        具体实现：根据 event.type 分发到对应 UI 组件更新。
        """
        ...

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        """同步导航状态。

        具体实现：NavigationGroup[] → LeftPanel / Sidebar
        """
        ...

    def update_workspace(self, state: WorkspaceState) -> None:
        """同步工作区状态。

        具体实现：WorkspaceState → ChatArea / HeaderBar
        """
        ...

    def update_inspector(self, state: InspectorState) -> None:
        """同步属性面板状态。

        具体实现：InspectorState → RightPanel / Inspector
        """
        ...

    def update_command(self, state: CommandState) -> None:
        """同步命令/状态栏状态。

        具体实现：CommandState → StatusBar / CommandBar
        """
        ...


# ═══════════════════════════════════════════════════════════════════
# Presentation Runtime
# ═══════════════════════════════════════════════════════════════════

class PresentationRuntime:
    """Presentation 层运行时。

    职责：
    - 管理 Renderer 生命周期
    - 分发 InteractionEvent 到活跃 Renderer
    - 同步 ShellContract 状态到活跃 Renderer
    - 编排数据转换（owns PresentationPipeline）

    生命周期：
      start() → register_renderer() → activate_renderer() → [运行]
      → dispatch_event() / update_navigation() / update_workspace() ...
      → shutdown()

    使用方：
    - Application 层（V6UIApplication）
    - 未来：Web / CLI / Mobile 启动器
    """

    def __init__(self) -> None:
        """初始化 PresentationRuntime。

        初始状态：无 Renderer 注册，Pipeline 就绪。
        """
        self._renderers: Dict[str, RendererProtocol] = {}
        self._active_renderer_id: str | None = None
        self._pipeline = PresentationPipeline()
        self._started = False

    # ═══════════════════════════════════════════════════════════════
    # Lifecycle
    # ═══════════════════════════════════════════════════════════════

    def start(self) -> None:
        """启动 Presentation Runtime。

        激活所有已注册 Renderer 的 start() 方法。
        如果某个 Renderer 失败，不影响其他 Renderer 启动。
        """
        self._started = True
        for rid, renderer in self._renderers.items():
            try:
                renderer.start()
            except Exception:
                # 单个 Renderer 启动失败不影响 PresentationRuntime 运行
                pass

    def shutdown(self) -> None:
        """关闭 Presentation Runtime。

        停用所有 Renderer，清空注册表，释放资源。
        """
        for rid, renderer in self._renderers.items():
            try:
                renderer.stop()
            except Exception:
                pass
        self._renderers.clear()
        self._active_renderer_id = None
        self._started = False

    @property
    def is_started(self) -> bool:
        """PresentationRuntime 是否已启动。"""
        return self._started

    # ═══════════════════════════════════════════════════════════════
    # Renderer Registry
    # ═══════════════════════════════════════════════════════════════

    def register_renderer(self, renderer_id: str, renderer: RendererProtocol) -> None:
        """注册一个 Renderer。

        注册不会自动启动 Renderer。必须调用 start() 或 activate_renderer()。

        参数：
        - renderer_id: 唯一标识（如 "qt", "web", "cli", "mobile"）
        - renderer: 实现 RendererProtocol 的实例
        """
        if renderer_id in self._renderers:
            raise ValueError(f"Renderer '{renderer_id}' already registered")
        self._renderers[renderer_id] = renderer

    def unregister_renderer(self, renderer_id: str) -> None:
        """注销一个 Renderer。

        如果该 Renderer 是活跃的，先停用再注销。
        """
        if renderer_id == self._active_renderer_id:
            self._active_renderer_id = None
        renderer = self._renderers.pop(renderer_id, None)
        if renderer is not None:
            try:
                renderer.stop()
            except Exception:
                pass

    def activate_renderer(self, renderer_id: str) -> None:
        """激活指定 Renderer。

        切换时：
        - 旧 Renderer 收到 stop()
        - 新 Renderer 收到 start()（如果尚未启动）
        - 更新活跃 Renderer 引用

        参数：
        - renderer_id: 已注册的 Renderer 标识
        """
        if renderer_id not in self._renderers:
            raise ValueError(f"Renderer '{renderer_id}' not registered")

        # 停用旧 Renderer
        old = self._active_renderer_id
        if old is not None and old != renderer_id:
            old_renderer = self._renderers.get(old)
            if old_renderer is not None:
                try:
                    old_renderer.stop()
                except Exception:
                    pass

        self._active_renderer_id = renderer_id

    def get_active_renderer(self) -> RendererProtocol | None:
        """获取当前活跃 Renderer。"""
        if self._active_renderer_id is None:
            return None
        return self._renderers.get(self._active_renderer_id)

    def get_renderer(self, renderer_id: str) -> RendererProtocol | None:
        """获取指定 Renderer（不激活）。"""
        return self._renderers.get(renderer_id)

    def list_renderers(self) -> List[str]:
        """列出所有已注册 Renderer 标识。"""
        return list(self._renderers.keys())

    @property
    def active_renderer_id(self) -> str | None:
        """当前活跃 Renderer 标识。"""
        return self._active_renderer_id

    # ═══════════════════════════════════════════════════════════════
    # Event Dispatch
    # ═══════════════════════════════════════════════════════════════

    def dispatch_event(self, event: InteractionEvent) -> None:
        """将 InteractionEvent 分发给活跃 Renderer。

        如果无活跃 Renderer，事件静默丢弃。
        Renderer 异常不会传播到调用方。
        """
        renderer = self.get_active_renderer()
        if renderer is None:
            return
        try:
            renderer.render(event)
        except Exception:
            # Renderer 错误不得破坏 PresentationRuntime
            pass

    # ═══════════════════════════════════════════════════════════════
    # Shell State Sync
    # ═══════════════════════════════════════════════════════════════

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        """同步导航状态到活跃 Renderer。"""
        renderer = self.get_active_renderer()
        if renderer is not None:
            try:
                renderer.update_navigation(groups)
            except Exception:
                pass

    def update_workspace(self, state: WorkspaceState) -> None:
        """同步工作区状态到活跃 Renderer。"""
        renderer = self.get_active_renderer()
        if renderer is not None:
            try:
                renderer.update_workspace(state)
            except Exception:
                pass

    def update_inspector(self, state: InspectorState) -> None:
        """同步属性面板状态到活跃 Renderer。"""
        renderer = self.get_active_renderer()
        if renderer is not None:
            try:
                renderer.update_inspector(state)
            except Exception:
                pass

    def update_command(self, state: CommandState) -> None:
        """同步命令/状态栏状态到活跃 Renderer。"""
        renderer = self.get_active_renderer()
        if renderer is not None:
            try:
                renderer.update_command(state)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════
    # Data Pipeline（owns PresentationPipeline）
    # ═══════════════════════════════════════════════════════════════

    @property
    def pipeline(self) -> PresentationPipeline:
        """获取 PresentationPipeline 实例。

        Application 层通过此属性访问数据转换能力：
          runtime.pipeline.sessions_to_navigation_groups(raw_sessions)
        """
        return self._pipeline

    def sessions_to_navigation_groups(
        self, raw_sessions: List[Dict[str, Any]]
    ) -> List[NavigationGroup]:
        """Runtime Session 原始数据 → NavigationGroup 列表。"""
        return self._pipeline.sessions_to_navigation_groups(raw_sessions)

    def messages_to_workspace_state(
        self,
        title: str,
        subtitle: str,
        raw_messages: List[Dict[str, Any]],
        models: List[str] | None = None,
    ) -> WorkspaceState:
        """Runtime Message 原始数据 → WorkspaceState。"""
        return self._pipeline.messages_to_workspace_state(
            title=title, subtitle=subtitle, raw_messages=raw_messages, models=models,
        )

    def capabilities_to_navigation_items(
        self, raw_capabilities: List[Dict[str, Any]]
    ) -> List[NavigationItem]:
        """Runtime Capability 原始数据 → NavigationItem 列表。"""
        return self._pipeline.capabilities_to_navigation_items(raw_capabilities)

    def metadata_to_inspector_state(
        self, module_id: str, raw_properties: List[Dict[str, Any]]
    ) -> InspectorState:
        """Runtime Metadata → InspectorState。"""
        return self._pipeline.metadata_to_inspector_state(module_id, raw_properties)