"""presentation/renderers/v6_ui/renderer.py — V6UI Renderer 复合入口。

Phase 2-D.1：将 V6UIEventRenderer + V6UIShellAdapter 组合为单一 RendererProtocol 实现。

RendererProtocol 要求：
  - start() / stop()      生命周期
  - render(event)         事件消费
  - update_navigation()   导航同步
  - update_workspace()    工作区同步
  - update_inspector()    属性面板同步
  - update_command()      状态栏同步

V6UIRenderer 将 V6UIEventRenderer（事件流）和 V6UIShellAdapter（状态流）
组合为单一 Renderer，满足 RendererProtocol，可注册到 RendererRegistry。

约束：
  ✓ 只调用 v6/ui 组件公共 API
  ✗ 不穿透 v6/ui 私有成员
  ✗ 不 import Runtime Implementation
  ✗ 不 import PySide6（v6/ui 组件内部处理）
"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent
from agent_workbench.presentation.renderers.v6_ui.event_renderer import V6UIEventRenderer
from agent_workbench.presentation.renderers.v6_ui.shell_adapter import V6UIShellAdapter
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    WorkspaceState,
)


class V6UIRenderer:
    """v6/ui Renderer 复合入口。

    组合 V6UIEventRenderer（事件流）和 V6UIShellAdapter（状态流），
    实现 RendererProtocol，可注册到 RendererRegistry。

    生命周期：
      start() → 初始化 UI 状态
      stop()  → 清理 UI 状态
    """

    def __init__(
        self,
        event_renderer: V6UIEventRenderer,
        shell_adapter: V6UIShellAdapter,
    ) -> None:
        self._event = event_renderer
        self._shell = shell_adapter
        self._started = False

    # ── Lifecycle ──

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    # ── Event Rendering（委托给 V6UIEventRenderer）──

    def render(self, event: InteractionEvent) -> None:
        self._event.render(event)

    # ── Shell State Sync（委托给 V6UIShellAdapter）──

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        self._shell.update_navigation(groups)

    def update_workspace(self, state: WorkspaceState) -> None:
        self._shell.update_workspace(state)

    def update_inspector(self, state: InspectorState) -> None:
        self._shell.update_inspector(state)

    def update_command(self, state: CommandState) -> None:
        self._shell.update_command(state)