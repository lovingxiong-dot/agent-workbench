"""presentation/runtime.py — Presentation Runtime 生命周期服务。

Phase 2-C.2：将 Presentation 从静态工具箱升级为生命周期服务。
Phase 2-C.3：Renderer 注册管理委托给 RendererRegistry。

职责：
  - Presentation 生命周期管理（start/shutdown）
  - InteractionEvent 分发（Runtime → Renderer）
  - Shell State 同步（Nav/Workspace/Inspector/Command）
  - 数据转换编排（owns PresentationPipeline）

不负责：
  - Renderer 注册表状态机（委托给 RendererRegistry）
  - UI 创建（归 Application 层）
  - Runtime 执行（归 agent_workbench/runtime/）
  - Widget 管理（归 v6/ui）

约束：
  ✓ 依赖：PresentationProtocols（protocols/） + ShellContract（shell/） + RendererRegistry
  ✗ 禁止：PySide6、v6/ui、QWidget、ChatArea、LeftPanel、RightPanel
  ✗ 禁止：Runtime Implementation（engine, executor, session, llm, tool）
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent
from agent_workbench.presentation.renderers.registry import (
    RendererProtocol,
    RendererRegistry,
    RendererRegistryError,
    RendererState,
)
from agent_workbench.presentation.shell.integration import PresentationPipeline
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    NavigationItem,
    WorkspaceState,
)

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════
# Presentation Runtime
# ═══════════════════════════════════════════════════════════════════

class PresentationRuntime:
    """Presentation 层运行时。

    职责：
    - Presentation 生命周期管理（start/shutdown）
    - 分发 InteractionEvent 到活跃 Renderer
    - 同步 ShellContract 状态到活跃 Renderer
    - 编排数据转换（owns PresentationPipeline）

    Renderer 注册管理委托给 RendererRegistry（Phase 2-C.3）。

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

        初始状态：Registry 就绪，Pipeline 就绪。
        """
        self._registry = RendererRegistry()
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
        for entry in self._registry.list_entries():
            if entry.state == RendererState.INACTIVE:
                try:
                    entry.instance.start()
                except Exception:
                    pass

    def shutdown(self) -> None:
        """关闭 Presentation Runtime。

        停用并注销所有 Renderer，释放资源。
        """
        self._registry.deactivate()
        for rid in list(self._registry.list_ids()):
            try:
                self._registry.unregister(rid)
            except RendererRegistryError:
                pass
        self._started = False

    @property
    def is_started(self) -> bool:
        """PresentationRuntime 是否已启动。"""
        return self._started

    # ═══════════════════════════════════════════════════════════════
    # Renderer Registry（委托给 RendererRegistry）
    # ═══════════════════════════════════════════════════════════════

    @property
    def registry(self) -> RendererRegistry:
        """获取底层 RendererRegistry 实例。

        Application 层可直接访问 registry 进行高级操作（如查询状态）。
        """
        return self._registry

    def register_renderer(self, renderer_id: str, renderer: RendererProtocol) -> None:
        """注册一个 Renderer（委托给 RendererRegistry）。"""
        self._registry.register(renderer_id, renderer)

    def unregister_renderer(self, renderer_id: str) -> None:
        """注销一个 Renderer（委托给 RendererRegistry）。"""
        self._registry.unregister(renderer_id)

    def activate_renderer(self, renderer_id: str) -> None:
        """激活指定 Renderer（委托给 RendererRegistry）。

        强制 Single Active Renderer Rule：
        - 如果已有活跃 Renderer，抛出 RendererRegistryError
        - 必须先 deactivate_renderer() 再 activate_renderer()
        """
        self._registry.activate(renderer_id)

    def deactivate_renderer(self) -> None:
        """停用当前活跃 Renderer（委托给 RendererRegistry）。"""
        self._registry.deactivate()

    def get_active_renderer(self) -> RendererProtocol | None:
        """获取当前活跃 Renderer 实例。"""
        return self._registry.get_active()

    def get_renderer(self, renderer_id: str) -> RendererProtocol | None:
        """获取指定 Renderer 实例（不激活）。"""
        return self._registry.get(renderer_id)

    def list_renderers(self) -> List[str]:
        """列出所有已注册 Renderer 标识。"""
        return self._registry.list_ids()

    @property
    def active_renderer_id(self) -> str | None:
        """当前活跃 Renderer 标识。"""
        return self._registry.get_active_id()

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