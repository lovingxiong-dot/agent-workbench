# Workbench OS v6.14 — Shell Integration Architecture Report

> 生成日期：2026-07-21
> 状态：审核中（禁止代码实施）
> 前置条件：v6.13 Architecture Freeze 已验证通过

---

## 0. 问题诊断

### 发现的断裂点

workbench.py 的桥接代码（已回退）引用 `self._left_panel` 和 `self._chat_area`，但实际架构是：

```python
Workbench._navigator  → NavigatorHost → Navigator (QListWidget)
Workbench._workspace  → WorkspaceHost → QStackedWidget
```

而非：

```python
Workbench._left_panel → LeftPanel  # 不存在
Workbench._chat_area  → ChatArea   # 不存在
```

### 根因分析

这是 v6.13 架构升级后两条 UI 演进线未被正确合并的表现：

| 线 | 定位 | 关键组件 | 状态 |
|----|------|---------|------|
| Workbench OS Shell | 可替换的 Shell 框架 | NavigatorHost, WorkspaceHost, InspectorHost, StatusBarHost | 已有 |
| v6/ui Pure UI | 第一个 Qt Shell 参考实现 | LeftPanel, ChatArea, RightPanel, HeaderBar, InputArea, ChatScene | 已有 |

两条线各自正确——但它们之间的 **Shell Adapter 层缺失**。

---

## 1. Workbench OS Shell 组件树（现有）

```
Workbench (QSplitter 三栏)
│
├── [左] NavigatorHost (WorkbenchAreaHost)
│   └── Navigator (QWidget)
│       ├── 顶部功能 Tab: QListWidget
│       │   ├── Chat ──→ WorkspaceHost.switch_to("chat")
│       │   ├── Skills ──→ WorkspaceHost.switch_to("skill")
│       │   └── Tools ──→ WorkspaceHost.switch_to("tool")
│       └── Settings 折叠区: QListWidget
│           ├── AI Models ──→ AddProviderDialog
│           ├── MCP ──→ AddMcpDialog
│           ├── Skills ──→ AddSkillDialog
│           ├── Workflows ──→ AddWorkflowDialog
│           ├── Prompts ──→ AddPromptDialog
│           ├── Memory ──→ AddMemoryDialog
│           └── Knowledge
│
├── [中] WorkspaceHost (QStackedWidget)
│   ├── ChatWorkspaceItem    (chat)    — ChatScene + QGraphicsView
│   ├── TraceWorkspaceItem   (trace)   — 执行轨迹日志
│   ├── GenericWorkspaceItem (generic) — 通用内容展示
│   └── WelcomeWorkspaceItem (welcome) — Home 页面
│
├── [右] InspectorHost (WorkbenchAreaHost)
│   └── Inspector — 选中模块的 Property/Action/Statistic 面板
│
├── [底部] ToolBarHost ──→ 动态生成工具栏按钮
├── [底部] ControlBar ──→ Agent / Provider / Model 选择器
├── [底部] StatusBarHost ──→ Runtime 状态
└── [底部] CommandBarHost ──→ 命令输入
```

**关键外部依赖**：`WorkbenchUIController` 通过 Host API（`navigator`, `workspace`, `inspector` 等属性）驱动 Workbench。Workbench 本身**不持有 Runtime**。

---

## 2. v6/ui Pure UI 组件树（现有）

```
v6/ui/ (包：from v6.ui import LeftPanel, ChatArea, RightPanel, ...)
│
├── LeftPanel (QWidget) — 左栏
│   ├── TabButton ×3: 会话 / 文件 / 功能
│   ├── QLineEdit: 搜索
│   ├── QStackedWidget
│   │   ├── 会话页: SessionGroup[] + QScrollArea
│   │   ├── 文件页: RecentFiles
│   │   └── 功能页: FunctionPage
│   │       ├── FunctionRow: tool (Web搜索/代码解释器/文件阅读器)
│   │       ├── FunctionRow: mcp (文件系统MCP/浏览器MCP)
│   │       ├── FunctionRow: skill (重构/测试生成)
│   │       └── FunctionRow: automation (自动提交/同步文档)
│   ├── + 新会话 按钮
│   └── 主题 按钮
│
├── ChatArea (QWidget) — 中区
│   ├── HeaderBar: 标题、搜索、更多、折叠按钮
│   ├── SearchBar: 搜索条（可折叠）
│   ├── ChatScene (QGraphicsScene) + QGraphicsView
│   │   ├── 用户消息
│   │   ├── AI 消息
│   │   ├── 流式输出
│   │   ├── 工具结果
│   │   ├── 系统卡片
│   │   └── 步骤/折叠块
│   ├── 分析按钮行
│   └── InputArea: 输入框 + Mode/Model 标签 + Send/Stop
│
└── RightPanel (QWidget) — 右栏
    ├── 会话信息
    ├── 工具/MCP/技能/自动化开关
    └── 设置入口
```

**设计来源**：`experiments/ui_template.py`（Git 标签 `v0.6-alpha`），是 Workbench OS **第一个 Shell Reference Implementation**。

---

## 3. 组件映射关系

### 3.1 区域级映射

```
Workbench OS Shell          │  v6/ui Pure UI              │  映射关系
─────────────────────────────┼─────────────────────────────┼────────────────
NavigatorHost (左)           │  LeftPanel                   │  功能区域重叠
WorkspaceHost (中)           │  ChatArea                    │  核心功能匹配
InspectorHost (右)           │  RightPanel                  │  功能高度重叠
StatusBarHost (底)           │  (无对等组件)                │  v6/ui 无状态栏
CommandBarHost (底)          │  InputArea.send_clicked      │  输入—命令映射
ControlBar (底)              │  InputArea.mode/model tag    │  控制—模型映射
ToolBarHost (底)             │  (无对等组件)                │  v6/ui 无工具栏
```

### 3.2 详细功能映射

| Workbench OS 功能 | v6/ui 对应组件 | 数据流方向 |
|------------------|---------------|-----------|
| Navigator 会话列表 | LeftPanel.session_selected | WorkbenchUIController ← LeftPanel 信号 |
| ChatWorkspace 消息渲染 | ChatArea._scene (ChatScene) | API 调用 → ChatRoomItem.render_msg |
| 流式输出 | ChatArea.stream_chunk / stream_end | WorkbenchStreamRenderer → ChatArea |
| 用户输入 | ChatArea._input / CommandBarHost | 双向：ChatArea.send_msg / CommandBar.submit |
| 工具执行结果 | ChatArea.tool_executed | Runtime → UIController → ChatArea |
| 确认请求 | ChatArea.confirm_required | Runtime → UIController → ChatArea |
| 模型切换 | ChatArea._cycle_model / ControlBar | 双向 |
| Agent 选择 | ControlBar.agent_changed | UIController → WorkbenchController |
| Inspector 属性编辑 | RightPanel (无直接对应) | 当前只存在于 Workbench OS Shell |
| 功能页工具开关 | LeftPanel._func_page (FunctionPage) | 硬编码列表，无 Runtime 数据源 |
| 主题切换 | LeftPanel._theme_btn | theme.changed 信号全局广播 |

---

## 4. 现有可用的 Presentation Layer

已完成的 Presentation 基础设施（可直接使用）：

```
presentation/
├── view_models/
│   ├── agent.py        — AgentViewModel + AgentRuntimeViewModel   ✅
│   ├── conversation.py — ConversationViewModel                   ✅
│   ├── capability.py   — CapabilityViewModel                     ✅
│   ├── memory.py       — MemoryViewModel                         ✅
│   ├── settings.py     — SettingsViewModel                       ✅
│   └── session.py      — SessionViewModel + MessageViewModel     ✅ (v6.14 新增)
│
├── adapters/
│   ├── agent_adapter.py        — Runtime Agent → AgentViewModel           ✅
│   ├── conversation_adapter.py — Runtime Session → ConversationViewModel   ✅
│   ├── capability_adapter.py   — Runtime Capability → CapabilityViewModel  ✅
│   ├── memory_adapter.py       — Runtime Memory → MemoryViewModel          ✅
│   └── settings_adapter.py     — Runtime Config → SettingsViewModel        ✅
```

**v6/ui 已有数据注入方法**（在 workspace 副本中）：

```
v6/ui/left_panel.py:
├── load_sessions(sessions: list[SessionViewModel]) — 注入会话列表
└── load_agents(agents: list[AgentViewModel])       — 注入 Agent 列表

v6/ui/chat_area.py:
├── load_messages(messages: list[MessageViewModel]) — 注入消息流
└── load_models(models: list[str])                  — 注入模型列表
```

---

## 5. 断裂点清单

以下是需要桥接的具体断点：

### 5.1 左侧区域断裂

| 断点 | Workbench OS Shell | v6/ui | 缺失层 |
|------|-------------------|-------|--------|
| 会话渲染 | Navigator QListWidget | LeftPanel SessionGroup | SessionViewModel → SessionGroup adapter |
| Agent 渲染 | Navigator 功能 Tab | LeftPanel load_agents() | AgentViewModel → LeftPanel 数据路径 |
| 功能页 | (无) | FunctionPage 硬编码 | CapabilityViewModel → FunctionPage.bind() |
| 搜索 | (无，使用 Navigator tab) | LeftPanel._search | SearchViewModel → LeftPanel |
| 新建会话 | UIController.on_new_session | LeftPanel.new_session_requested | 直接信号桥接 |

### 5.2 中间区域断裂

| 断点 | Workbench OS Shell | v6/ui | 缺失层 |
|------|-------------------|-------|--------|
| 消息历史 | ChatWorkspaceItem (被动渲染) | ChatArea append_/stream_ API | ConversationViewModel → ChatArea |
| 标题栏 | WorkspaceHost 无标题 | ChatArea HeaderBar | Metadata → HeaderBar.set_title |
| 模型选择 | ControlBar (底栏) | ChatArea InputArea tag | WorkbenchController → InputArea |
| 输入发送 | CommandBarHost | ChatArea InputArea | 命令路由：CommandBar vs InputArea |
| 工具渲染 | ChatWorkspaceItem.tool_executed | ChatArea.tool_executed | 已有直接映射 |

### 5.3 右侧区域断裂

| 断点 | Workbench OS Shell | v6/ui | 缺失层 |
|------|-------------------|-------|--------|
| 属性编辑 | Inspector (Property/Action) | RightPanel 信息 | ModulePresentation → RightPanel |
| 工具开关 | Inspector | RightPanel toggle | CapabilityViewModel → RightPanel |

### 5.4 底部区域断裂

| 断点 | Workbench OS Shell | v6/ui | 缺失层 |
|------|-------------------|-------|--------|
| 状态栏 | StatusBarHost | (无) | N/A (v6/ui 无此概念) |
| 工具栏 | ToolBarHost | (无) | N/A (v6/ui 无此概念) |

---

## 6. Shell Adapter 设计

### 6.1 设计原则

1. **Workbench 不直接依赖具体 UI 组件**（LeftPanel, ChatArea, RightPanel）
2. **Shell Adapter 是 Presentation Layer 的一部分**，位于 `presentation/shell/`
3. **Shell Adapter 负责数据模型转换**：ViewModel → v6/ui 组件可消费的格式
4. **Shell Adapter 不创建新的 ViewModel**，只做适配
5. **Hardcoded demo data → bind(data_source)**：v6/ui 中的硬编码列表（如 FunctionPage._SECTIONS）通过 bind() 方法从外部注入

### 6.2 目录结构

```
presentation/
├── view_models/       (现有, 不变) — 数据契约
├── adapters/          (现有, 不变) — Runtime → ViewModel
└── shell/             (新增)        — ViewModel → v6/ui 适配
    ├── __init__.py
    ├── left_panel_adapter.py   — ViewModel → LeftPanel
    ├── chat_adapter.py         — ViewModel → ChatArea
    └── function_page_adapter.py — CapabilityViewModel → FunctionPage
```

### 6.3 Adapter 接口定义

```python
# presentation/shell/left_panel_adapter.py
class LeftPanelAdapter:
    """将 ViewModel 列表注入 v6/ui/LeftPanel。

    不创建新的 LeftPanel，只操作已有实例。
    """

    def __init__(self, left_panel: LeftPanel) -> None:
        self._panel = left_panel

    def bind_sessions(self, sessions: list[SessionViewModel]) -> None:
        """从 SessionViewModel 列表刷新会话分组。"""
        # 内部调用 self._panel.load_sessions(sessions)

    def bind_agents(self, agents: list[AgentViewModel]) -> None:
        """从 AgentViewModel 列表刷新 Agent 分组。"""
        # 内部调用 self._panel.load_agents(agents)

    def bind_capabilities(self, capabilities: list[CapabilityViewModel]) -> None:
        """从 CapabilityViewModel 刷新功能页。"""
        # 内部调用 self._panel.load_capabilities(capabilities)


# presentation/shell/chat_adapter.py
class ChatAdapter:
    """将 ViewModel 列表注入 ChatWorkspaceItem 或 ChatArea。

    不创建新的 ChatArea，只操作已有实例。
    """

    def __init__(self, chat: ChatWorkspaceItem | ChatArea) -> None:
        self._chat = chat

    def bind_messages(self, messages: list[MessageViewModel]) -> None:
        """从 MessageViewModel 刷新聊天内容。"""

    def bind_models(self, models: list[str]) -> None:
        """从 Runtime 获取模型列表注入。"""

    def set_title(self, title: str, subtitle: str) -> None:
        """设置 HeaderBar 标题。"""
```

### 6.4 集成方式

```
WorkbenchUIController
    │
    │ 在 startup() 中创建 ShellAdapter
    │
    ├── LeftPanelAdapter(left_panel_instance)
    ├── ChatAdapter(chat_workspace_instance)
    └── FunctionPageAdapter(function_page_instance)

数据刷新流程：
    Runtime state changed
        │
        ▼
    WorkbenchUIController._on_selection_changed()
        │
        ├── Adapter.to_view_models()  (已有, 不变)
        │
        ▼
    ShellAdapter.bind_xxx(view_models)  (新增)
        │
        ▼
    v6/ui component (LeftPanel / ChatArea)
```

---

## 7. Phase 分步建议

### Phase 1-A: FunctionPage 去硬编码（最小、最安全起点）

**目标**：消除 v6/ui/function_page.py 中的硬编码 `_SECTIONS`，改为 bind() 注入。

**影响范围**：仅 `v6/ui/function_page.py`

**操作**：
- 在 FunctionPage 添加 `bind_capabilities(capabilities: list[dict])` 方法
- 保留 `_SECTIONS` 作为 fallback demo 数据

### Phase 1-B: Shell Adapter 层建立

**目标**：创建 `presentation/shell/` 并实现三个 adapter。

**影响范围**：新增目录，不修改现有文件

### Phase 1-C: LeftPanel 数据接通

**目标**：SessionViewModel → LeftPanelAdapter → LeftPanel.load_sessions() 链路跑通。

**影响范围**：`WorkbenchUIController` 的 `_setup_workbench_ui()` 和 `_refresh_navigator()` 增加 LeftPanel 实例化和绑定

### Phase 1-D: ChatArea 数据接通

**目标**：MessageViewModel → ChatAdapter → ChatArea.load_messages() 链路跑通。

---

## 8. 明确禁止事项

- ❌ 删除 Navigator / NavigatorHost
- ❌ 将 LeftPanel 作为 Workbench 的直接子组件
- ❌ 修改 Runtime / Core / Capability / Module Lifecycle
- ❌ 修改 metadata() 接口
- ❌ 给 v6/ui 组件添加 UI 配置参数
- ❌ 创建新 ViewModel 大全
- ❌ 重做 UI 设计

---

## 9. 边界确认

```
              Runtime (FROZEN)
                  │
                  │ Metadata + InteractionEvent
                  ▼
        Presentation Boundary
        ├── view_models/     (数据契约, 稳定)
        ├── adapters/        (Runtime→ViewModel, 稳定)
        └── shell/           (ViewModel→v6/ui, 新增)
                  │
                  ▼
            UI Shell
        ├── v6/ui/           (Pure UI, 视觉源)
        └── ui/workbench/    (OS Shell 框架)
```

**Workbench 不 import v6/ui；Shell Adapter 做中间层。**

---

> 审核状态：等待用户审核。审核通过后进入 Phase 1-A 实施。
