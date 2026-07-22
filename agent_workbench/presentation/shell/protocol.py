"""presentation/shell/protocol.py — Shell Protocol 接口 + OS 级抽象模型。

Shell Boundary Contract — Agent Workbench OS Presentation Constitution
═══════════════════════════════════════════════════════════════════════

Shell Layer defines presentation contracts for the Agent Workbench OS.
Shell is renderer-independent — it describes WHAT to display, not HOW.

Allowed:
  ✓ Pure Python data models (dataclasses)
  ✓ Protocol interfaces (typing.Protocol)
  ✓ Data transformers (ViewModel → Shell Model)
  ✓ Type annotations and enumerations

Forbidden:
  ✗ PySide6 imports
  ✗ Runtime imports
  ✗ Agent execution
  ✗ Tool execution
  ✗ Storage access
  ✗ Business logic
  ✗ Widget creation or manipulation

Supported renderers:
  - Desktop UI (PySide6)
  - Web UI
  - Mobile UI
  - CLI UI
  - Embedded UI

Phase 1-B：定义协议和模型，不实现任何具体 Shell。
使用 typing.Protocol 实现 Structural Typing——任何满足方法签名的类都是 ShellProtocol。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol


# ═══════════════════════════════════════════════════════════════════
# Navigation 抽象
# ═══════════════════════════════════════════════════════════════════

@dataclass
class NavigationItem:
    """OS 级导航项——不包含任何 UI 组件名。

    QtShell 内部映射：NavigationItem → LeftPanel SessionItem
    WebShell 内部映射：NavigationItem → Sidebar Item
    """
    id: str
    title: str
    preview: str = ""
    kind: str = "session"  # "session" | "agent" | "capability"
    group: str = "default"
    is_active: bool = False


@dataclass
class NavigationGroup:
    """OS 级导航分组——结构模型，非运行时状态。

    NavigationGroup 表示导航的层级组织结构（分组 + 项）。
    与 WorkspaceState 不同：WorkspaceState 是运行时状态快照，
    NavigationGroup 是静态结构描述。

    QtShell 内部映射：NavigationGroup → SessionGroup
    """
    id: str
    title: str
    items: List[NavigationItem] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Workspace 抽象
# ═══════════════════════════════════════════════════════════════════

@dataclass
class WorkspaceMessage:
    """OS 级消息——不包含 UI 渲染信息。

    QtShell 内部映射：WorkspaceMessage → ChatScene message bubble
    """
    id: str
    role: str  # "user" | "assistant" | "tool"
    content: str
    tool_calls: List[dict] = field(default_factory=list)


@dataclass
class WorkspaceState:
    """OS 级 Workspace 状态——不包含 UI 组件引用。

    命名采用 *State 后缀（非 *ViewModel），
    与 presentation/view_models/ 的 ViewModel 做层级区分。

    QtShell 内部映射：WorkspaceState → ChatArea + HeaderBar
    """
    title: str = ""
    subtitle: str = ""
    messages: List[WorkspaceMessage] = field(default_factory=list)
    models: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Inspector 抽象
# ═══════════════════════════════════════════════════════════════════

@dataclass
class InspectorState:
    """OS 级 Inspector 状态——不包含 UI 组件引用。

    QtShell 内部映射：InspectorState → RightPanel
    Workbench Shell 映射：InspectorState → Inspector (Property/Action/Statistic)
    """
    object_id: str = ""
    properties: List[dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Command 抽象
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CommandState:
    """OS 级命令/状态栏状态。"""
    prompt: str = ""
    status_text: str = ""
    is_processing: bool = False


# ═══════════════════════════════════════════════════════════════════
# Shell Protocol
# ═══════════════════════════════════════════════════════════════════

class ShellProtocol(Protocol):
    """Workbench OS Shell Protocol——OS 级界面契约。

    使用 typing.Protocol 定义（Structural Typing）：
    - 不要求继承：任何实现同名方法的类都满足此协议
    - 方法签名是唯一的契约

    每个 Shell 实现（QtShell / WebShell / MobileShell）内部负责
    将 OS 抽象映射到自身 UI 组件。
    """

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        """刷新左侧导航区域。

        QtShell 映射：NavigationGroup → SessionGroup → LeftPanel
        Workbench 映射：NavigationGroup → Navigator QListWidget
        """
        ...

    def update_workspace(self, state: WorkspaceState) -> None:
        """刷新中间工作区。

        QtShell 映射：WorkspaceState → HeaderBar + ChatScene
        Workbench 映射：WorkspaceState → WorkspaceHost
        """
        ...

    def update_inspector(self, state: InspectorState) -> None:
        """刷新右侧属性面板。

        QtShell 映射：InspectorState → RightPanel
        Workbench 映射：InspectorState → Inspector
        """
        ...

    def update_command(self, state: CommandState) -> None:
        """刷新底部命令/状态区。"""
        ...
