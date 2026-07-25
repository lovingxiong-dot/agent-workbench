# 全量交叉对比报告：`ui-template` vs `v6-agent` UI 体系

> **审查日期**: 2026-07-21
> **比较分支**: `ui-template`（用户设计 UI） vs `v6-agent`（当前开发分支）
> **真相源**: `github.com/lovingxiong-dot/agent-workbench`
> **用途**: 项目知识资产 — 记录 UI 演进路径和设计差异，支撑 Phase 3 验证

---

## 一、宏观差异总览

| 维度 | ui-template（设计 UI） | v6-agent（实际 UI） |
|------|----------------------|---------------------|
| 总 UI 文件数 | ~18 个源文件 | ~60+ 个源文件 |
| 总代码量 | ~9,900 行（含原型） | ~7,500 行（含 Workbench OS 层） |
| 核心原型 | `experiments/ui_template.py`（2,436 行） | 无独立原型 |
| 生产组件 | `v4/`（17 文件，5,568 行） | `v6/ui/`（20 文件，~2,000 行）+ `agent_workbench/ui/workbench/`（32 文件，~3,564 行） |
| 设计文档 | `v4/DESIGN.md`（179 行）+ `blueprints/`（4 文档） | 无 UI 设计文档 |
| QSS 主题 | 2 套（`dark_github.qss`，`trae_dark.qss`） | 无独立 QSS 文件 |
| SVG 设计稿 | 6 个（`ui-full-dark.svg` 等） | 无 |
| 架构模型 | Chat-as-Authority + SessionRuntime | Workbench OS + Metadata-driven |

---

## 二、逐层交叉对比

### 2.1 入口 / 主窗口

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 文件 | `v4/main_window.py` (909行) | `agent_workbench/ui/main_window.py` (68行) | 设计版 13 倍代码量 |
| 布局方式 | 直接 QSplitter 三栏 | 委托给 WorkbenchHost → Workbench | 代理层多 2 级 |
| 主题系统 | 内联 THEMES 字典（35 色） | 委托 `v6/ui/base.py` | 设计版内联，当前版外部引用 |
| 消息渲染 | UIRenderer + ChatScene | WorkbenchUIController（795 行）+ `v6/ui/chat_scene.py` | 设计版渲染器 301 行，当前版控制器 795 行 |
| 会话管理 | SessionOrchestrator + SessionRepository | SessionService + ConversationService | 架构模型不同 |
| Worker | WorkerManager（186 行） | 无 Worker 层 | 设计版有独立 Worker 线程管理 |

**关键发现**：设计版 `v4/main_window.py` 是一个自包含的完整 UI 入口（909 行），当前版 `agent_workbench/ui/main_window.py` 只是一个薄壳（68 行），所有逻辑分散到了 Workbench OS 层。

---

### 2.2 主题系统

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 文件 | 内联于 `experiments/ui_template.py` | `v6/ui/base.py`（310 行） | 当前版独立文件，但内容完全来自设计版 |
| 颜色数量 | 30 个颜色键 | 30 个颜色键 | 完全一致 |
| 颜色值 | `#1a1a2e` / `#16213e` / `#0f3460` 等 | `#1a1a2e` / `#16213e` / `#0f3460` 等 | 完全一致 |
| ThemeManager | 同文件内定义 | 同文件内定义 | 完全一致 |
| 全局 C 变量 | `theme.C` | `theme.C` | 完全一致 |
| 辅助函数 | `qcolor()`, `font()`, `mono_font()`, `svg_icon()` | `qcolor()`, `font()`, `mono_font()`, `svg_icon()` | 完全一致 |
| InvisibleResizeHandle | 内联（~120 行） | `install_invisible_handles()` 函数 | 功能相同，实现略有差异 |
| AppleMenu | 内联（~100 行） | `v6/ui/apple_menu.py` | 功能相同，实现略有差异 |
| FramelessWindowHelper | 内联（~80 行） | `v6/ui/window_frame.py`（225 行） | 功能相同，当前版更完善 |

**关键发现**：主题系统是 **唯一完全对齐** 的层。`v6/ui/base.py` 文件头注释明确写了 "设计来源：`experiments/ui_template.py`（Git 标签 v0.6-alpha）"。颜色值、主题切换机制、辅助函数全部一致。

---

### 2.3 布局系统

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 文件 | 内联于 `experiments/ui_template.py` | `v6/layout_manager.py`（61 行） | 设计版单文件，当前版独立 |
| 左栏宽度 | 220px | 220px | 一致 |
| 右栏宽度 | 400px | 400px | 一致 |
| 中栏最小宽度 | - | 240px | 当前版有约束 |
| QSplitter handleWidth | 1px | 1px | 一致 |
| 拖拽热区 | InvisibleResizeHandle（4px） | `install_invisible_handles(4)` | 一致 |
| 折叠/展开 | 独立按钮控制 | `toggle_left()` / `toggle_right()` | 一致 |

**关键发现**：布局系统基本对齐，但当前版 LayoutManager 是设计版 QSplitter 逻辑的简化提取。

---

### 2.4 左栏面板

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 文件 | `v4/conversation_list.py`（576 行） | `v6/ui/left_panel.py`（147 行）+ `session_group.py` + `session_item.py` + `function_page.py` + `recent_files.py` + `tab_button.py` + `apple_menu.py` | 设计版单文件，当前版拆成 7 个文件 |
| 会话列表 | SessionItemWidget（标题+预览+时间，hover 高亮，右键菜单） | SessionGroup + SessionItem（继承自 v6 体系） | 设计版更精细 |
| 功能页 | 无独立功能页 | FunctionPage（工具/MCP/Skill/自动化 开关） | 当前版多出功能区 |
| 文件管理器 | 无 | RecentFiles | 当前版多出文件管理 |
| Tab 结构 | 功能 \| 会话 | 会话 \| 文件 \| 功能 | 当前版多一个 Tab |
| 搜索框 | 内联 | 独立 QLineEdit | 一致 |
| 主题切换 | 底部按钮 | 底部按钮 | 一致 |

**关键发现**：设计版左栏是单一、自包含的 ConversationListWidget，当前版拆成了 7 个文件，并新增了 FunctionPage 和 RecentFiles。设计版的 SessionItemWidget 有更精细的 hover 效果和右键菜单。

---

### 2.5 聊天区（核心差异最大）

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 聊天项 | `v4/chat_items.py`（471 行） | `v6/ui/chat_items.py`（218 行） | 设计版 2.2 倍代码量 |
| 渲染方式 | QGraphicsItem 像素级 SVG 对齐 | QGraphicsItem 简化版 | 设计版精确到 SVG 坐标 |
| 坐标系统 | 固定 402px 宽，LEFT_MARGIN=20px，CONTENT_WIDTH=362px | 动态宽度 `set_width()` | 设计版固定，当前版自适应 |
| 颜色常量 | 每个组件独立 QColor 常量 | 通过 C 全局变量 | 设计版显式声明 |
| 用户气泡 | UserBubbleItem（右对齐 `#007acc`，RIGHT_PAD=14px） | UserBubble（简化版） | 设计版精确到像素锚点 |
| 阶段面板 | PhasePanelItem（analyze/confirm/execute/verify/archive 五阶段） | PhasePanel（简化版） | 设计版更完整 |
| 折叠块 | FoldBlockItem（思考过程/工具执行/命令输出 三层折叠） | FoldBlock（简化版） | 设计版三层折叠结构 |
| 工具条目 | ToolEntryItem | ToolEntry（简化版） | 设计版更详细 |
| 场景管理 | `v4/chat_scene.py`（145 行） | `v6/ui/chat_scene.py`（119 行） | 设计版略大 |
| 输入区 | `v4/input_area.py`（281 行） | `v6/ui/input_area.py`（136 行） | 设计版 2.1 倍代码量 |
| 输入区标签 | TagSelectButton（模式/模型 标签+值+chevron ▼） | 简化版下拉 | 设计版有 SVG 图标按钮 |
| 标题栏 | 内联 | `v6/ui/header_bar.py`（118 行） | 一致 |

**关键发现**：聊天区是差异最大的层。设计版 `v4/chat_items.py` 是 SVG 像素级精确实现，每个 Item 的坐标、颜色、间距都直接对应 `ui-chat-area.svg` 设计稿。当前版 `v6/ui/chat_items.py` 是大幅简化版，丢失了：

- 精确的 SVG 坐标锚点
- 三层折叠结构（思考过程/工具执行/命令输出）
- 五阶段面板的完整视觉
- 标签式输入区（TagSelectButton）

---

### 2.6 右栏面板

| 对比项 | ui-template | v6-agent | 差异 |
|--------|------------|----------|------|
| 文件 | `v4/right_panel.py`（609 行） | `v6/ui/right_panel.py`（204 行）+ `terminal_widget.py` + `file_reader_widget.py` + `browser_widget.py` | 设计版单文件，当前版拆成 4 个文件 |
| 终端 | TerminalWidget（集成 TerminalWorker） | TerminalWidget（Demo 占位） | 设计版有真实 Worker 集成 |
| 文件编辑器 | FileReaderWidget | FileReaderWidget | 一致 |
| 浏览器 | BrowserWidget（QWebEngineView） | BrowserWidget | 一致 |
| 标签容器 | QTabWidget（四标签页） | TabButton + QStackedWidget | 实现方式不同 |
| 最近文件 | 无独立列表 | RecentFiles 组件 | 当前版多出 |

**关键发现**：设计版右栏是自包含的 609 行单文件，当前版拆成了 4 个文件。设计版的终端集成了真实的 TerminalWorker，当前版是 Demo 占位。

---

### 2.7 Workbench OS 层（`agent_workbench/ui/workbench/`）— 当前版独有，设计版不存在

| 组件 | 行数 | 说明 |
|------|------|------|
| `workbench.py` | 102 | 三栏组装 + 信号转发 |
| `workbench_host.py` | 39 | Host 容器 |
| `workbench_ui_controller.py` | 795 | 最大的单文件，UI 与 Runtime 的桥梁 |
| `navigator.py` | 193 | 导航树（Provider/MCP/Skill/Workflow 等） |
| `navigator_host.py` | 66 | 导航 Host |
| `inspector.py` | 277 | 属性检查器 |
| `inspector_host.py` | 49 | 检查器 Host |
| `status_bar.py` | 63 | 状态栏 |
| `status_bar_host.py` | 64 | 状态栏 Host |
| `command_bar.py` | 44 | 命令栏 |
| `command_bar_host.py` | 31 | 命令栏 Host |
| `control_bar.py` | 125 | 控制栏（Agent/Provider/Model 选择器） |
| `title_bar.py` | 108 | 标题栏 |
| `tool_bar.py` | 50 | 工具栏 |
| `tool_bar_host.py` | 31 | 工具栏 Host |
| `workspace_host.py` | 31 | 工作区 Host |
| `metadata_adapter.py` | 161 | Metadata → PresentationModel 适配器 |
| `presentation.py` | 70 | 展示模型 |
| `view_schema.py` | 89 | 视图 Schema |
| `view_schema_registry.py` | 244 | Schema 注册表 |
| `view_schema_renderer.py` | 177 | Schema 渲染器 |
| `view_component.py` | 23 | 视图组件 |
| `view_component_registry.py` | 28 | 组件注册表 |
| `binding_context.py` | 92 | 绑定上下文 |
| `chat_workspace.py` | 72 | 聊天工作区 |
| `trace_workspace.py` | 108 | 追踪工作区 |
| `trace_event_registry.py` | 128 | 追踪事件注册表 |
| `welcome_workspace.py` | 178 | 欢迎页面 |
| `generic_workspace.py` | 28 | 通用工作区 |
| `host_base.py` | 40 | Host 基类 |
| `provider_workspace.py` | 211 | Provider 工作区 |
| `agent_profile_workspace.py` | 221 | Agent Profile 工作区 |
| **合计** | **~3,564** | **32 个文件** |

**关键发现**：这 32 个文件、3,564 行代码是 **设计版完全不存在** 的层。这就是为什么 Agent 做的 UI 与设计 UI 不是同一个界面。Workbench OS 层引入了：

- Host 模式（8 个 Host 组件）— 设计版没有这种抽象
- Metadata-driven 渲染（6 个文件，~769 行）— 设计版是直接 paint 渲染
- ViewSchema 系统（4 个文件，~539 行）— 设计版不存在
- 多 Workspace 类型（6 个 Workspace 文件）— 设计版是单一聊天场景

---

### 2.8 设计资产对比

| 资产类型 | ui-template | v6-agent | 状态 |
|----------|------------|----------|------|
| QSS 主题 | `dark_github.qss`（GitHub Dark 风格） | 无 | 缺失 |
| QSS 主题 | `trae_dark.qss`（Trae 暗黑风格） | 无 | 缺失 |
| SVG 设计稿 | `ui-full-dark.svg`（1024x720 完整布局） | 无 | 缺失 |
| SVG 设计稿 | `ui-full-light.svg` | 无 | 缺失 |
| SVG 设计稿 | `ui-chat-area.svg`（聊天区像素级标注） | 无 | 缺失 |
| SVG 设计稿 | `ui-chat-header.svg` | 无 | 缺失 |
| SVG 设计稿 | `ui-fold-expand-demo.svg` | 无 | 缺失 |
| SVG 设计稿 | `ui-left-function.svg` | 无 | 缺失 |
| 设计蓝图 | `blueprints/index.md` | 无 | 缺失 |
| 设计蓝图 | `blueprints/session/v2-multi-session-design.md` | 无 | 缺失 |
| 设计蓝图 | `blueprints/session/v3-event-bus-architecture.md` | 无 | 缺失 |
| 设计蓝图 | `blueprints/integration/workspace-context.md` | 无 | 缺失 |
| 架构设计 | `v4/DESIGN.md`（179 行完整设计文档） | 无 | 缺失 |

**关键发现**：设计版的所有 QSS 主题、SVG 设计稿、设计蓝图、架构设计文档，在当前分支 **全部缺失**。

---

## 三、根因总结

为什么 Agent 做的 UI 与设计 UI 不是同一个界面？

```
ui-template 分支（设计）                    v6-agent 分支（实际）
═══════════════════════                    ═══════════════════════

experiments/ui_template.py                无独立原型
  └── 2436 行纯 UI 原型                     └── 被拆解为 v6/ui/ 各组件
  └── 一手设计，未经拆解                       └── 简化版，丢失精确细节

v4/ 目录（17 文件，5568 行）                v6/ui/ 目录（20 文件，~2000 行）
  └── 像素级 SVG 对齐渲染                    └── 简化版，丢失 SVG 坐标锚点
  └── Chat-as-Authority 架构                └── 无对应架构
  └── 完整 Worker 线程管理                   └── 无 Worker 层

                                            agent_workbench/ui/workbench/（32 文件，3564 行）
                                              └── 设计版不存在的新层
                                              └── Host 模式 + Metadata-driven
                                              └── 改变了整个 UI 交互范式

QSS 主题 + SVG 设计稿 + 设计蓝图             全部缺失
```

### 三层断裂

1. **原型→组件 断裂**：`experiments/ui_template.py`（2,436 行）被拆解到 `v6/ui/` 时，丢失了 SVG 像素级精确坐标、三层折叠结构、五阶段面板细节
2. **架构 断裂**：设计版的 `v4/` 是 Chat-as-Authority + SessionRuntime + Worker 模式，当前版是 Workbench OS + Metadata-driven + Host 模式，是两种完全不同的 UI 架构范式
3. **叠加层 断裂**：`agent_workbench/ui/workbench/`（32 文件，3,564 行）是设计版完全不存在的叠加层，它改变了整个 UI 的交互方式和视觉呈现

---

## 四、修复方向（已记录，非当前 Phase 3 执行范围）

最短路径：以 `ui-template` 为 UI 基线，接入 Runtime。

1. **提取 `v4/` 为 UI 基线**：将 `v4/main_window.py`（909 行）、`v4/chat_items.py`（471 行）、`v4/conversation_list.py`（576 行）等作为 UI 权威源
2. **替换 `v6/ui/` 组件**：用 `v4/` 的精确实现替换当前 `v6/ui/` 的简化版
3. **简化 Workbench OS 层**：将 `agent_workbench/ui/workbench/` 的 32 个文件缩减为必要的信号桥接
4. **恢复设计资产**：将 QSS 主题、SVG 设计稿、设计蓝图合并到当前分支

**预期效果**：
- 删除 `agent_workbench/ui/workbench/` 中约 20+ 个不必要的抽象文件
- 用 `v4/` 精确组件替换 `v6/ui/` 简化组件
- UI 还原为设计版的像素级精确渲染
- 保留 Runtime 能力（ConfigStore、ModuleRegistry、Provider 等）通过信号桥接接入

---

## 五、相关文档

| 文档 | 用途 |
|------|------|
| [phase3-execution-plan.md](./phase3-execution-plan.md) | Phase 3 执行计划 |
| [phase3-validation-plan.md](./phase3-validation-plan.md) | Phase 3 验证计划 |
| [architecture-boundaries.md](./architecture-boundaries.md) | 架构边界定义 |