"""agent_workbench/ui/workbench/view_schema.py — Workbench 布局协议层。

ViewSchema 不是 Qt，也不是 Runtime。它描述的是：
> 一个 Module 的 PresentationModel 应该如何摆放在 Workbench 的各个 UI 区域。

核心职责：
- 定义 Toolbar / Inspector / StatusBar / Workspace / Dock 的布局结构。
- 通过字段名引用 PresentationModel 中的 actions / properties / statistics。
- 与具体 Renderer（Qt / Web / CLI）解耦。

数据流：
    Metadata
        ↓
    PresentationModel
        ↓
    ViewSchema（怎么摆）
        ↓
    Qt Renderer（具体实现）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolbarGroupSchema:
    """工具栏按钮分组。"""

    name: str
    items: list[str] = field(default_factory=list)  # action names


@dataclass
class ToolbarSchema:
    """工具栏布局：支持扁平 action 列表或分组。"""

    items: list[str | ToolbarGroupSchema] = field(default_factory=list)


@dataclass
class InspectorTabSchema:
    """Inspector 中一个可折叠/切换的 Tab。"""

    id: str
    title: str
    source: str = "properties"  # properties | statistics | actions
    categories: list[str] | None = None  # 仅 source=properties 时过滤 category
    collapsed: bool = False


@dataclass
class InspectorSchema:
    """Inspector 整体布局。"""

    tabs: list[InspectorTabSchema] = field(default_factory=list)
    default_tab: str = "properties"


@dataclass
class BindingSource:
    """动态数据来源定义。

    path 使用点分路径，例如：
    - "runtime.llm.tokens"
    - "task.status"
    - "agent.state"
    - "session.messages.count"

    format 可选，用于将原始值格式化为显示字符串（例如 "{:.2f} ms"）。
    """

    path: str
    format: str | None = None


@dataclass
class StatusItemSchema:
    """StatusBar 中一个统计项的引用。"""

    name: str
    source: str = "statistics"  # statistics | runtime | binding
    binding: BindingSource | None = None  # source == "binding" 时使用


@dataclass
class StatusSchema:
    """StatusBar 布局。"""

    items: list[StatusItemSchema] = field(default_factory=list)


@dataclass
class PropertyBinding:
    """Property 的动态绑定定义：当 editable=False 时，值从 Runtime 读取。"""

    path: str
    format: str | None = None


@dataclass
class DockSchema:
    """Workspace 周边 Dock 面板（可复用为 Web/CLI 的侧边栏）。"""

    region: str  # left | right | bottom | top
    title: str
    tab_source: str  # properties | statistics | actions
    tab_id: str = ""


@dataclass
class WorkspaceSchema:
    """Workspace 区域整体布局。"""

    toolbar: ToolbarSchema = field(default_factory=ToolbarSchema)
    inspector: InspectorSchema = field(default_factory=InspectorSchema)
    status: StatusSchema = field(default_factory=StatusSchema)
    docks: list[DockSchema] = field(default_factory=list)


@dataclass
class ViewSchema:
    """一个 Module 的完整 UI 布局协议。"""

    schema_id: str
    name: str
    description: str = ""
    workspace: WorkspaceSchema = field(default_factory=WorkspaceSchema)
