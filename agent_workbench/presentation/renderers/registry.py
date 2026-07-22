"""presentation/renderers/registry.py — Renderer Registry。

Phase 2-C.3：独立的 Renderer 注册表，强制 Single Active Renderer Rule。

规则：
1. Registry 可以注册多个 Renderer
2. Runtime 同时只能激活一个 Renderer
3. Renderer 生命周期状态机：
     inactive ──activate()──→ active ──deactivate()──→ inactive
4. 禁止：active + active（尝试激活第二个 Renderer 时拒绝）

设计原因：
- 未来 Web / Mobile / Desktop 多端并存时，同一时刻只能有一个 Renderer 消费事件
- 防止两个 Renderer 同时修改同一 UI 状态导致竞态

约束：
  ✓ 纯 Python 状态机，无 UI 框架依赖
  ✗ 禁止 PySide6、QWidget、v6/ui
  ✗ 禁止 Runtime Implementation import
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Protocol

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    WorkspaceState,
)


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

    Phase 2-C.3：RendererRegistry 的注册单元。
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


class RendererState(str, Enum):
    """Renderer 生命周期状态。"""
    INACTIVE = "inactive"   # 已注册但未激活
    ACTIVE = "active"       # 当前活跃，接收事件和状态同步
    STOPPED = "stopped"     # 已停止（start() 被调用后 stop() 被调用）


@dataclass
class RendererEntry:
    """Registry 中的一个 Renderer 条目。

    追踪 Renderer 实例及其生命周期状态。
    """
    id: str
    instance: RendererProtocol
    state: RendererState = RendererState.INACTIVE

    def activate(self) -> None:
        """激活 Renderer。

        调用 start() 启动 UI 组件，设置状态为 ACTIVE。
        """
        self.instance.start()
        self.state = RendererState.ACTIVE

    def deactivate(self) -> None:
        """停用 Renderer。

        调用 stop() 清理 UI 组件，设置状态为 INACTIVE。
        """
        try:
            self.instance.stop()
        except Exception:
            pass
        self.state = RendererState.INACTIVE


class RendererRegistry:
    """Renderer 注册表。

    强制 Single Active Renderer Rule：
    - 同一时刻只能有一个 Renderer 处于 ACTIVE 状态
    - 尝试激活第二个 Renderer 时抛出 RendererRegistryError
    - 必须先 deactivate() 才能 activate() 另一个

    使用模式：
        registry = RendererRegistry()
        registry.register("qt", qt_renderer)
        registry.register("web", web_renderer)
        registry.activate("qt")       # OK
        registry.activate("web")      # ❌ RendererRegistryError: 'qt' is still active
        registry.deactivate()         # 先停用 qt
        registry.activate("web")      # OK
    """

    def __init__(self) -> None:
        self._entries: Dict[str, RendererEntry] = {}
        self._active_id: str | None = None

    # ── Registration ──

    def register(self, renderer_id: str, renderer: RendererProtocol) -> None:
        """注册一个 Renderer。

        注册后 Renderer 处于 INACTIVE 状态，不会自动启动。

        参数：
        - renderer_id: 唯一标识（如 "qt", "web", "cli", "mobile"）
        - renderer: 实现 RendererProtocol 的实例

        异常：
        - RendererRegistryError: 如果 renderer_id 已注册
        """
        if renderer_id in self._entries:
            raise RendererRegistryError(
                f"Renderer '{renderer_id}' is already registered"
            )
        self._entries[renderer_id] = RendererEntry(
            id=renderer_id,
            instance=renderer,
        )

    def unregister(self, renderer_id: str) -> None:
        """注销一个 Renderer。

        如果该 Renderer 是活跃的，先 deactivate() 再注销。

        参数：
        - renderer_id: 要注销的 Renderer 标识

        异常：
        - RendererRegistryError: 如果 renderer_id 未注册
        """
        if renderer_id not in self._entries:
            raise RendererRegistryError(
                f"Renderer '{renderer_id}' is not registered"
            )

        # 如果正在注销活跃 Renderer，先停用
        if renderer_id == self._active_id:
            self.deactivate()

        self._entries.pop(renderer_id)

    # ── Single Active Renderer Rule ──

    def activate(self, renderer_id: str) -> None:
        """激活指定 Renderer。

        强制 Single Active Renderer Rule：
        - 如果已有活跃 Renderer，抛出 RendererRegistryError
        - 必须先 deactivate() 当前活跃 Renderer

        参数：
        - renderer_id: 已注册的 Renderer 标识

        异常：
        - RendererRegistryError: 如果已有活跃 Renderer 或 renderer_id 未注册
        """
        if renderer_id not in self._entries:
            raise RendererRegistryError(
                f"Renderer '{renderer_id}' is not registered"
            )

        # ── Single Active Renderer Rule ──
        if self._active_id is not None and self._active_id != renderer_id:
            active_entry = self._entries.get(self._active_id)
            raise RendererRegistryError(
                f"Cannot activate '{renderer_id}': "
                f"Renderer '{self._active_id}' is still active. "
                f"Call deactivate() first."
            )

        entry = self._entries[renderer_id]
        entry.activate()
        self._active_id = renderer_id

    def deactivate(self) -> None:
        """停用当前活跃 Renderer。

        如果无活跃 Renderer，此调用无操作（幂等）。
        """
        if self._active_id is None:
            return
        entry = self._entries.get(self._active_id)
        if entry is not None:
            entry.deactivate()
        self._active_id = None

    # ── Query ──

    def get_active(self) -> RendererProtocol | None:
        """获取当前活跃 Renderer 实例。"""
        if self._active_id is None:
            return None
        entry = self._entries.get(self._active_id)
        return entry.instance if entry else None

    def get_active_id(self) -> str | None:
        """获取当前活跃 Renderer 标识。"""
        return self._active_id

    def get(self, renderer_id: str) -> RendererProtocol | None:
        """获取指定 Renderer 实例（不激活）。"""
        entry = self._entries.get(renderer_id)
        return entry.instance if entry else None

    def get_state(self, renderer_id: str) -> RendererState | None:
        """获取指定 Renderer 的生命周期状态。"""
        entry = self._entries.get(renderer_id)
        return entry.state if entry else None

    def list_ids(self) -> List[str]:
        """列出所有已注册 Renderer 标识。"""
        return list(self._entries.keys())

    def list_entries(self) -> List[RendererEntry]:
        """列出所有已注册 Renderer 条目（含状态）。"""
        return list(self._entries.values())

    def has_active(self) -> bool:
        """是否有活跃 Renderer。"""
        return self._active_id is not None

    def is_registered(self, renderer_id: str) -> bool:
        """检查 renderer_id 是否已注册。"""
        return renderer_id in self._entries

    @property
    def count(self) -> int:
        """已注册 Renderer 数量。"""
        return len(self._entries)


class RendererRegistryError(Exception):
    """RendererRegistry 操作错误。"""
    pass