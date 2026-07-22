# Shell Adapter Architecture Report

> 生成日期：2026-07-21
> 状态：审核中，禁止代码实施
> 前置条件：v6.13 Architecture Freeze, v6.14 Shell Integration Phase

---

## 0. 核心问题

### Q1: v6/ui 如何成为 Qt Shell？

**答**：v6/ui 已经是 Qt Shell，不需要"成为"。需要做的是**去除硬编码 Demo 数据，改为 bind() 注入**。

当前状态：

```python
# v6/ui/function_page.py — 当前：硬编码 Demo
_SECTIONS = [
    ("tools", "工具", "tool", [
        ("web_search", "Web 搜索", "联网检索实时信息"),
        ("code_interpreter", "代码解释器", "执行 Python 脚本"),
        ...
    ]),
    ...
]
```

目标状态：

```python
# 外部注入
function_page.bind_capabilities(capability_view_models)

# FunctionPage 内部
def bind_capabilities(self, caps: list[CapabilityViewModel]) -> None:
    """从 ViewModel 重建所有功能行，替代 _SECTIONS。"""
    self.clear()
    for cap in caps:
        row = FunctionRow(cap.id, cap.name, cap.description, cap.type, cap.enabled)
        self.add_row(row)
```

**关键原则**：v6/ui 不 import Runtime，不 import Controller，不 import Registry。它只接收 ViewModel 作为数据源。

### Q2: Presentation Contract 如何注入？

**答**：通过新增的 `presentation/shell/` 层，方向永远单向：

```
Runtime (不感知 UI)
    │
    ▼
presentation/adapters/        (Runtime → ViewModel, 已有)
    │
    ▼
presentation/shell/           (ViewModel → Shell Contract, 新增)
    ├── protocol.py           (ShellProtocol 接口定义)
    ├── models/               (Shell 抽象模型: Navigation/Workspace/Inspector)
    ├── transformers/         (ViewModel → Shell Model 转换)
    └── implementations/      (具体 Shell 实现)
        ├── qt_shell.py       (Qt Shell: Navigation→LeftPanel, Workspace→ChatArea, Inspector→RightPanel)
        ├── web_shell.py      (Web Shell: Navigation→Sidebar, Workspace→Main, Inspector→Panel)
        └── mobile_shell.py   (Mobile Shell: 未来)
```

命名原则：
- `shell/` 是架构概念——Shell Protocol 是 OS 级契约
- `implementations/` 是具体 Shell 实现——每个 Shell 内部自行决定组件映射
- `transformers/` 是数据转换——不做 UI 操作，不创建 Widget

数据注入时机：由 `WorkbenchUIController` 在 Runtime 状态变更时调用 Shell Protocol。

数据注入方式：方法调用（`update_navigation()` / `update_workspace()`），不是信号驱动。

### Q3: Workbench OS 如何保持多 Shell 扩展能力？

**答**：通过 **Shell Protocol 接口**——使用 OS 级抽象（Navigation/Workspace/Inspector），不暴露具体 UI 组件名。

```python
# presentation/shell/protocol.py — OS 级抽象契约

class ShellProtocol:
    """Workbench OS Shell 协议：定义 OS 级界面抽象，不包含任何具体 UI 组件名。"""

    def update_navigation(self, items: list[NavigationItem]) -> None: ...
    def update_workspace(self, workspace: WorkspaceState) -> None: ...
    def update_inspector(self, data: InspectorState) -> None: ...
    def update_command(self, command_state: CommandState) -> None: ...
```

**Qt Shell 内部映射**（未暴露给 Protocol）：

```python
# presentation/shell/implementations/qt_shell.py — Phase 1-D
class QtShell(ShellProtocol):
    """Qt Shell：内部将 OS 抽象映射到 v6/ui 组件。"""

    def __init__(self, left_panel, chat_area, right_panel): ...

    def update_navigation(self, items):
        # OS 抽象 Navigation → Qt 组件 LeftPanel
        self._left_panel.update_sessions(...)

    def update_workspace(self, ws):
        # OS 抽象 Workspace → Qt 组件 ChatArea
        self._chat_area.load_messages(...)

    def update_inspector(self, data):
        # OS 抽象 Inspector → Qt 组件 RightPanel
        self._right_panel.set_data(...)
```

**Web Shell 同一协议，不同映射**：

```python
class WebShell(ShellProtocol):
    def update_navigation(self, items):
        # OS 抽象 Navigation → React Sidebar
        self._sidebar.set_items(items)

    def update_workspace(self, ws):
        # OS 抽象 Workspace → React Main
        self._main.set_content(ws)
```

未来换 Shell 时，`WorkbenchUIController` 代码**零修改**——只替换 `ShellProtocol` 实现。

---

## 1. 数据流拓扑

### 1.1 完整数据流

```
┌─────────────────────────────────────────────┐
│                 Runtime (FROZEN)              │
│  AgentModule, SessionModule, ToolModule,      │
│  CapabilityRegistry, InteractionLayer, ...    │
└────────────┬────────────────────────────────┘
             │
             │ getattr() transitional pattern
             ▼
┌─────────────────────────────────────────────┐
│        presentation/adapters/ (已有)          │
│  AgentAdapter, ConversationAdapter,           │
│  CapabilityAdapter, MemoryAdapter, ...        │
│                                               │
│  Runtime Object → ViewModel (dataclass)       │
└────────────┬────────────────────────────────┘
             │
             │ 纯数据流（ViewModel 实例）
             ▼
┌─────────────────────────────────────────────┐
│     presentation/shell/        (Phase 1-B 实施)
│  ShellProtocol + Models + Transformers          │
│                                               │
│  ViewModel → Shell Model (NavigationItem, etc.) │
│  不创建 Widget，纯数据转换                      │
└────────────┬────────────────────────────────┘
             │
             │ 方法调用（bind_xxx / set_xxx）
             ▼
┌─────────────────────────────────────────────┐
│             v6/ui/ (Pure Shell)               │
│  LeftPanel, ChatArea, FunctionPage, ...       │
│                                               │
│  只展示数据，不持有 Runtime 引用              │
└─────────────────────────────────────────────┘
```

### 1.2 禁止的逆向流

```
❌ v6/ui → import runtime
❌ v6/ui → import controller
❌ v6/ui → import registry
❌ v6/ui → import agent_workbench.runtime
❌ Shell Adapter → 创建新 Widget
❌ Shell Adapter → 修改 Widget 视觉属性
```

---

## 2. 硬编码清除清单

### 2.1 FunctionPage._SECTIONS（最高优先级）

**文件**：`v6/ui/function_page.py`（项目根目录，非 workspace）

**当前**：

```python
_SECTIONS = [
    ("tools", "工具", "tool", [
        ("web_search", "Web 搜索", "联网检索实时信息"),
        ("code_interpreter", "代码解释器", "执行 Python 脚本"),
        ("file_reader", "文件阅读器", "读取并分析本地文件"),
    ]),
    ("mcps", "MCP 服务", "mcp", [
        ("filesystem", "文件系统 MCP", "访问本地文件系统"),
        ("browser", "浏览器 MCP", "控制浏览器操作"),
    ]),
    ("skills", "技能", "skill", [
        ("refactor", "重构技能", "批量重构代码结构"),
        ("test_gen", "测试生成", "为选中代码生成测试"),
    ]),
    ("automations", "自动化", "automation", [
        ("auto_commit", "自动提交", "生成提交信息并提交"),
        ("sync_docs", "同步文档", "自动同步 README 与注释"),
    ]),
]
```

**改造方案**：添加 `bind_capabilities()` 方法，保留 `_SECTIONS` 作为 fallback。

**禁止**：改成从 Runtime 导入 `ToolModule` / `CapabilityRegistry`。

### 2.2 ChatArea._models / _modes（硬编码字符串）

**文件**：`v6/ui/chat_area.py`

**当前**：

```python
self._modes = ["Agent", "Chat", "Coder"]
self._models = ["gpt-4o", "gpt-4o-mini", "claude-3.5"]
```

**改造方案**：已有 `load_models(models: list[str])` 方法。只需外部调用。

### 2.3 ChatArea._load_demo()（Demo 会话内容）

**文件**：`v6/ui/chat_area.py`

**当前**：

```python
def _load_demo(self) -> None:
    self._header.set_title("项目分析助手", "f:\\Agent\\agent_workbench")
    self.append_user("帮我分析当前项目，给出优化建议。")
    self.append_ai("已进入分析流程...", "Analyze")
    self._scene.add_step(1, "扫描目录结构与关键文件。")
    ...
```

**改造方案**：保留 `_load_demo()` 作为独立运行时的 fallback。当 `load_messages()` 被调用时，自动清除 demo 数据（已在现有代码中实现）。

### 2.4 LeftPanel 初始状态（无硬编码）

`v6/ui/left_panel.py` 通过 `update_sessions([])` 初始化为空，无硬编码问题。

---

## 3. Shell Protocol 与 QtShell 接口设计

### 3.1 ShellProtocol — OS 级抽象契约

```python
# presentation/shell/protocol.py (Phase 1-B 实施)

from dataclasses import dataclass, field
from typing import List

# ── Shell 抽象模型 ──

@dataclass
class NavigationItem:
    """OS 级导航项——不包含任何 UI 组件名。"""
    id: str
    title: str
    preview: str = ""
    kind: str = "session"  # "session" | "agent" | "capability"
    group: str = "default"
    is_active: bool = False


@dataclass
class NavigationGroup:
    """导航分组——接口模型，非运行时状态。"""
    id: str
    title: str
    items: List[NavigationItem] = field(default_factory=list)


@dataclass
class WorkspaceMessage:
    """Workspace 消息——OS 级消息概念。"""
    id: str
    role: str  # "user" | "assistant" | "tool"
    content: str
    tool_calls: List[dict] = field(default_factory=list)


@dataclass
class WorkspaceState:
    """Workspace 状态——OS 级工作区抽象。"""
    title: str = ""
    subtitle: str = ""
    messages: List[WorkspaceMessage] = field(default_factory=list)
    models: List[str] = field(default_factory=list)


@dataclass
class InspectorState:
    """Inspector 状态——OS 级属性面板抽象。"""
    object_id: str = ""
    properties: List[dict] = field(default_factory=list)


class ShellProtocol(Protocol):
    """Workbench OS Shell Protocol——OS 级界面契约。

    使用 typing.Protocol 定义接口（Structural Typing），
    不要求继承：任何实现同名方法的类都满足此协议。
    """

    def update_navigation(self, groups: List[NavigationState]) -> None:
        """刷新左侧导航区域。"""
        ...

    def update_workspace(self, ws: WorkspaceViewModel) -> None:
        """刷新中间工作区。"""
        ...

    def update_inspector(self, data: InspectorViewModel) -> None:
        """刷新右侧属性面板。"""
        ...

    def update_command(self, command_state: dict) -> None:
        """刷新命令/状态栏状态。"""
        ...
```

### 3.2 QtShell — 内部映射实现（Phase 1-D）

```python
# presentation/shell/implementations/qt_shell.py (Phase 1-D 实施)

class QtShell(ShellProtocol):
    """Qt Shell 实现：将 OS 抽象映射到 v6/ui 组件。

    内部映射关系（不暴露给 Protocol）：
        Navigation → LeftPanel
        Workspace  → ChatArea
        Inspector  → RightPanel
    """

    def __init__(self) -> None:
        self._left_panel: LeftPanel | None = None
        self._chat_area: ChatArea | None = None
        self._right_panel: RightPanel | None = None

    def attach_left_panel(self, panel: LeftPanel) -> None:
        self._left_panel = panel

    def attach_chat_area(self, area: ChatArea) -> None:
        self._chat_area = area

    def attach_right_panel(self, panel: RightPanel) -> None:
        self._right_panel = panel

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        """Navigation → LeftPanel。"""
        if self._left_panel is None:
            return
        data = [(g.id, g.title, [
            {"id": it.id, "title": it.title, "preview": it.preview}
            for it in g.items
        ]) for g in groups]
        self._left_panel.update_sessions(data)

    def update_workspace(self, ws: WorkspaceState) -> None:
        """Workspace → ChatArea。"""
        if self._chat_area is None:
            return
        self._chat_area._scene.clear()
        for msg in ws.messages:
            if msg.role == "user":
                self._chat_area._scene.add_user_message(msg.content)
            elif msg.role == "assistant":
                self._chat_area._scene.add_ai_message(msg.content)
            elif msg.role == "tool":
                for tc in msg.tool_calls:
                    self._chat_area._scene.add_tool(
                        tc.get("name", ""), tc.get("result", {}), tc.get("status", "ok"))
        if ws.models:
            self._chat_area._models = ws.models
            self._chat_area._model_i = 0
            self._chat_area._input.set_model(ws.models[0])

    def update_inspector(self, data: InspectorState) -> None:
        """Inspector → RightPanel。"""
        if self._right_panel:
            self._right_panel.set_data(data)

    def update_command(self, command_state: dict) -> None:
        pass
```

### 3.3 Transformers — ViewModel → Shell Model（Phase 1-B）

`presentation/shell/transformers/` 目录包含 ViewModel → Shell 抽象模型的纯数据转换函数。不 import PySide6，不创建 Widget。

```python
# presentation/shell/transformers/session_transformer.py
def to_navigation_groups(sessions: list[SessionViewModel]) -> list[NavigationState]:
    """SessionViewModel → NavigationGroup + NavigationItem。"""
    groups: dict[str, list] = {}
    for s in sessions:
        gid = s.group_id or "default"
        groups.setdefault(gid, []).append(s)
    return [NavigationState(id=gid, title=gid, items=[
        NavigationItem(id=s.id, title=s.title, preview=s.preview,
                       kind="session", group=gid, is_active=s.is_active)
        for s in items
    ]) for gid, items in groups.items()]

# presentation/shell/transformers/message_transformer.py
def to_workspace_view_model(
    title: str, subtitle: str,
    messages: list[MessageViewModel],
    models: list[str],
) -> WorkspaceState:
    """MessageViewModel → WorkspaceState。"""
    return WorkspaceState(
        title=title, subtitle=subtitle,
        messages=[WorkspaceMessage(id=m.id, role=m.role, content=m.content, tool_calls=m.tool_calls) for m in messages],
        models=models,
    )

# presentation/shell/transformers/capability_transformer.py
def to_navigation_items(capabilities: list[CapabilityViewModel]) -> list[NavigationItem]:
    """CapabilityViewModel → NavigationItem（功能页作为导航展示）。"""
    return [NavigationItem(id=c.id, title=c.name, preview=c.description, kind=c.category) for c in capabilities]
```

---

## 4. 集成架构

### 4.1 核心原则：先完善链路，不增加 Shell

v6/ui 是 Qt Shell Implementation，不是"另一个窗口"。当前阶段目标不是把 v6/ui 接入 Workbench，而是**完成 Presentation Boundary 数据流**。

```
                    WorkbenchUIController
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
  Workbench (Host)   Shell Layer     WorkbenchController
  NavigatorHost      (Phase 1-B)     Runtime (FROZEN)
  WorkspaceHost      
  InspectorHost      
  StatusBarHost      
```

**当前 Phase 1-B/1-C**：

- Shell Layer 只做数据转换，不创建 Qt Widget
- 完善现有 Workbench Shell（NavigatorHost/WorkspaceHost 等）的 Presentation 接入
- v6/ui 作为视觉源保持独立，不嵌入 Workbench

**Phase 1-D（远期）**：

- 在 Shell Protocol 稳定后，实现 QtShellAdapter
- v6/ui 作为 Qt Shell 实现，通过协议接入

### 4.2 为何不将 v6/ui 作为独立窗口

- v6/ui 不是"另一个窗口"，它是 Qt Shell Implementation
- 未来 Web Shell / Mobile Shell / CLI Shell 都遵循同一 Shell Protocol
- 独立窗口方案会混淆 Shell 身份与 Window 实例
- 正确方式：Shell Protocol 成熟后，通过 WorkspaceHost 切换 Shell 实现

### 4.3 边界确认

```
              Runtime (FROZEN)
                  │
                  │ Metadata + InteractionEvent
                  ▼
        Presentation Boundary
        ├── view_models/     (数据契约, 稳定)
        ├── adapters/        (Runtime → ViewModel, 稳定)
        └── shell/           (ViewModel → Shell, Phase 1-B 开始)
                  │
                  ▼
            Shell Implementation
        ├── v6/ui/           (Qt Shell, 视觉源)
        │   └── Phase 1-D 接入
        └── ui/workbench/    (OS Shell Host, 已有)
            └── Phase 1-C 完善接入
```

- **WorkbenchUIController** 是唯一的编排者
- **Shell Layer** 不创建 Widget（Phase 1-B），只做数据转换
- **v6/ui** 与 **Workbench Host** 无直接引用关系
- **两套 Shell 不同时运行**——Phase 1-C 完善 Workbench Shell，Phase 1-D 才引入 Qt Shell

---

## 5. 实施 Phase 规划

### Phase 1-A: 纯 UI 去硬编码（修改 v6/ui 文件）

**目标**：消除 v6/ui 中的硬编码 Demo 数据，增加 bind() 数据入口。

**影响范围**：仅 `v6/ui/` 下的文件（项目根目录）

**操作**：
1. `v6/ui/function_page.py`：添加 `bind_capabilities(capabilities: list)` + `_clear_rows()`，保留 `_SECTIONS` 作为 fallback
2. `v6/ui/chat_area.py`：已有 `load_messages()` / `load_models()`，无需额外修改
3. `v6/ui/left_panel.py`：已有 `load_sessions()` / `load_agents()`，无需额外修改

**禁止**：v6/ui import Runtime / Controller / Registry

**验证**：独立运行 FunctionPage / ChatArea / LeftPanel 的 `__main__` 测试仍可工作

---

### Phase 1-B: Shell Protocol + Models + Transformers（新增文件，纯 Python）

**目标**：建立 Shell Protocol 接口和 OS 级抽象模型（Navigation / Workspace / Inspector）。只做数据转换，不创建任何 Qt Widget。

**影响范围**：新增 `presentation/shell/` 目录，不修改现有代码

**操作**：
1. 创建 `presentation/shell/__init__.py`
2. 创建 `presentation/shell/protocol.py` — ShellProtocol(Protocol) 接口 + NavigationItem / NavigationState / WorkspaceState / InspectorState 模型定义
3. 创建 `presentation/shell/transformers/`：
   - `session_transformer.py` — SessionViewModel → NavigationState
   - `message_transformer.py` — MessageViewModel → WorkspaceState
   - `capability_transformer.py` — CapabilityViewModel → NavigationItem
4. 创建 `presentation/shell/tests/` — 纯数据转换单元测试

**禁止**：
- ❌ import PySide6 / QWidget
- ❌ 创建 v6/ui 实例
- ❌ import Runtime
- ❌ 文件名含 "adapter"（与 `presentation/adapters/` 职责区分）
- ❌ Shell Protocol 方法名包含具体 UI 组件名（LeftPanel/ChatArea 等）

---

### Phase 1-C: 完善现有 Workbench Shell 的 Presentation 接入

**目标**：让现有 Workbench Shell（NavigatorHost/WorkspaceHost 等）通过 Presentation Layer 接收数据，而不是直接引入 v6/ui 组件。

**影响范围**：`workbench_ui_controller.py`

**操作**：
1. 在 `_refresh_navigator()` 中，从 Runtime 获取 Session/Agent 数据，通过已有 Adapter 转为 ViewModel
2. 通过 NavigatorHost 的 `load_presentations()` / `register_module()` 等已有接口注入数据
3. 不创建 LeftPanel/ChatArea 实例

**禁止**：
- ❌ 创建 v6/ui 组件实例
- ❌ 将 LeftPanel/ChatArea 挂载到 Workbench

---

### Phase 1-D（远期）: QtShell 实现

**前置条件**：Shell Protocol 接口稳定，Transformers 数据转换链路验证通过。

**目标**：实现 `QtShell implements ShellProtocol`，将 v6/ui 作为 Qt Shell 正式接入 Workbench OS。

**操作**：
1. 创建 `presentation/shell/implementations/qt_shell.py`
2. 实现 `ShellProtocol.update_navigation/update_workspace/update_inspector`
3. QtShell 内部将 OS 抽象映射到 v6/ui 组件：
   - Navigation → LeftPanel
   - Workspace → ChatArea
   - Inspector → RightPanel

**关键**：`QtShell`（实现），不是 `QtShellAdapter`（适配器）。Shell 是架构概念，Adapter 是实现方式。

---

## 6. 禁止清单

| # | 禁止操作 | 原因 |
|---|---------|------|
| 1 | 修改 `workbench.py` | Workbench 是 Host Shell，不依赖具体 UI |
| 2 | 将 LeftPanel/ChatArea 加入 Workbench | 两套 Shell 不应同时运行，避免 UI 概念混合 |
| 3 | 修改 Runtime 任何文件 | Frozen Zone |
| 4 | 修改 metadata() 接口 | Frozen Zone |
| 5 | v6/ui import Runtime | 打破单向数据流 |
| 6 | Shell Layer 创建 Widget（Phase 1-B） | 协议层只做数据转换，不创建 UI |
| 7 | 删除 Navigator/NavigatorHost | 它们是 OS 层抽象 |
| 8 | 创建新 ViewModel 大全 | 已有 6 个足够 |
| 9 | Shell Protocol 暴露 UI 组件名 | Navigation 而非 LeftPanel |
| 10 | Transformer 文件命名为 "adapter" | 与 `presentation/adapters/` 职责混淆 |

---

## 7. 最终目录结构（冻结后）

```
presentation/
├── view_models/              (已有, 数据契约)
│   ├── agent.py
│   ├── conversation.py
│   ├── capability.py
│   ├── memory.py
│   ├── settings.py
│   └── session.py
│
├── adapters/                 (已有, Runtime → ViewModel)
│   ├── agent_adapter.py
│   ├── conversation_adapter.py
│   ├── capability_adapter.py
│   ├── memory_adapter.py
│   └── settings_adapter.py
│
└── shell/                    (新增)
    ├── __init__.py
    ├── protocol.py           (ShellProtocol(Protocol) + NavigationItem / NavigationState / WorkspaceState / InspectorState)
    ├── models/               (Shell 抽象模型, 可选独立目录)
    │   ├── navigation.py
    │   ├── workspace.py
    │   └── inspector.py
    ├── transformers/         (ViewModel → Shell Model)
    │   ├── session.py
    │   ├── message.py
    │   └── capability.py
    ├── tests/                (数据转换单元测试)
    └── implementations/      (具体 Shell 实现)
        ├── qt_shell.py       (Phase 1-D: Navigation→LeftPanel, Workspace→ChatArea)
        ├── web_shell.py      (未来)
        └── mobile_shell.py   (未来)
```

---

## 8. 与之前报告的区别

之前的 `shell-integration-architecture-report.md` 是**诊断报告**（组件树映射、断裂点分析）。

本文档是**设计文档**（Shell Protocol 接口、数据流、集成点、Phase 规划）。

两份互补：诊断报告解释"问题是什么"，设计文档规定"怎么修"。当前设计聚焦 OS 级抽象，采用 `QtShell implements ShellProtocol` 而非 `QtShellAdapter` 的命名体系。

---

> 审核状态：等待用户审核。审核通过后进入 Phase 1-A 实施。
> 
> 实施原则：每次只改一个文件，每步验证不会破坏现有功能。
