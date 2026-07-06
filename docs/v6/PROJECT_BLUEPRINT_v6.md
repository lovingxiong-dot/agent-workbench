# V6 项目蓝图

## 元信息
| 项目名称 | AI Agent 工作台 V6 | 当前版本 | v6.5.0-alpha | 状态 | 阶段 5 已验收（Review + Smoke 通过） |
| --- | --- | --- | --- | --- | --- |

## 最近变更（v6.5.0-alpha，2026-07-07）
- 修正架构图为八大引擎：新增 `ContextEngine`、`PromptEngine`，与 `InferenceEngine`、`ToolEngine`、`PhaseEngine`、`MemoryEngine`、`MetricsEngine`、`PolicyEngine` 共同构成核心引擎层。
- 更新 `docs/v6/SPEC.md` 引擎接口契约，明确各引擎输入/输出与闭环反馈关系。
- 在 `v6/runtime/engines/` 下补齐 `context.py`、`prompt.py` 等八大引擎实现，替代原有空文件。

## 最近变更（v6.4.0-alpha，2026-07-07）
- 实现 `v6/runtime/event_bus.py`：独立后台线程 + asyncio 队列的事件总线，支持同步/异步订阅者。
- 实现 `v6/runtime/context.py`：`RuntimeContext` 单次任务上下文，已加 `RLock` 保护。
- 实现 `v6/runtime/scheduler.py`：任务队列、并发控制、取消、wait_all。
- 实现 `v6/runtime/task.py`：`Task` / `ChatTask` / `AnalyzeTask`。
- 实现 `v6/runtime/runtime.py`：`AgentRuntime` 生命周期、任务调度、错误转 `error` 事件。
- 重写 `v6/ui_controller.py`：移除 `EchoRuntime`，创建 `ChatTask` 提交到 `AgentRuntime`，事件转 Qt 信号。
- 新增 `tests/v6/test_v6_event_bus.py`、`test_v6_scheduler.py`、`test_v6_runtime.py`、`test_v6_integration.py`。
- Review Agent 复核后修复：`EventBus._running` 加锁；`RuntimeContext` 加锁；增强取消任务测试。
- V6 阶段 4 全量回归 64 个测试通过。

## 项目目标
基于 V5 失败教训，**从零重写** V6 版本：
1. **V5 完整归档冻结**，不直接修改 V5 任何文件，仅提取可复用的核心经验。
2. **纯 UI 先行**：先完成与业务完全解耦的 UI 层，所有占位区域用真实 Demo 数据填充。
3. **严格分层架构**：
   ```
   MainWindow
      │
      ▼
   UIController
      │
      ├── LayoutManager
      ├── SessionManager
      └── ConfigManager
      │
      ▼
   AgentRuntime
      │
      ├── RuntimeContext
      ├── EventBus
      └── Scheduler
      │
      ├── ContextEngine     # 上下文组装、压缩、token 估算
      ├── PromptEngine      # System Prompt 构建、模板渲染、画像注入
      ├── InferenceEngine   # LLM 调用、流式输出、重试降级
      ├── ToolEngine        # 工具注册、权限校验、执行编排
      ├── PhaseEngine       # Mode-Phase 阶段定义与流转
      ├── MemoryEngine      # 三层记忆管理、检索、画像
      ├── MetricsEngine     # 指标采集、聚合、告警
      └── PolicyEngine      # 配置决策、模型选择、压缩策略
   ```
4. **专业 Agent 分工**：UI Agent、Runtime Agent、Review Agent 并行协作。
5. **每步验证**：每个模块完成后必须经 Review Agent 审查 + 冒烟测试 + Git 存档（commit + tag）。

## 关键原则
- **零业务逻辑侵入 UI**：UI 组件只发信号，不直接调用 Runtime 方法。
- **模块不超重**：单文件尽量控制在 200–400 行，超过必须拆分。
- **接口契约优先**：跨层调用必须先定义接口/信号契约，再写实现。
- **可测试性**：每个模块必须有独立单元测试或 smoke 测试。
- **可解释性**：每个类的职责、每条信号的含义必须在注释或文档中明确。

## 最近变更（v6.1.0-alpha，2026-07-07）
- 完成 V6 纯 UI 层全部组件实现，所有占位已用 Demo 数据填充。
- 实现 `main_window.py`、`layout_manager.py`、`ui_controller.py` 核心装配与信号桥接。
- 新增 `tests/v6/test_v6_ui_contract.py` 契约测试，11/11 通过。
- Review Agent 复核通过，确认 UI 零业务逻辑、信号契约完整、单文件职责单一。
- 历史归档：v6.0.0-alpha 项目启动与架构规格见本文件底部。

## 目录结构
```
agent_workbench/
├── main.py                      # 唯一入口，仅负责初始化 Application 与 AgentRuntime
├── AgentWorkbenchV6.spec        # PyInstaller V6 打包配置
├── scripts/
│   └── rebuild_v6.ps1           # V6 一键打包脚本
│
├── v5/                          # V5 完整归档，禁止修改
├── v6/                          # V6 唯一开发目录
│   ├── __init__.py
│   ├── main_window.py           # 纯 UI 壳：仅创建 Widget、转发事件、管理窗口行为
│   ├── ui_controller.py         # UI 控制层：连接 MainWindow 与 Runtime/Manager
│   ├── layout_manager.py        # 三栏布局、分栏拖拽、折叠/展开管理
│   ├── session_manager.py       # 会话 CRUD、最近会话、持久化接口
│   ├── config_manager.py        # 配置读取、验证、热更新
│   │
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── runtime.py           # AgentRuntime：任务调度、生命周期、错误处理
│   │   ├── context.py           # RuntimeContext：单次任务上下文
│   │   ├── event_bus.py         # EventBus：异步事件总线
│   │   ├── scheduler.py         # Scheduler：任务队列、并发控制
│   │   ├── task.py              # Task / ChatTask / AnalyzeTask 基类
│   │   └── engines/
   │   │       ├── __init__.py
   │   │       ├── interfaces.py    # 八大引擎共享数据类型与抽象接口
   │   │       ├── context.py       # ContextEngine：上下文组装、压缩、token 估算
   │   │       ├── prompt.py        # PromptEngine：System Prompt 构建、模板渲染、画像注入
   │   │       ├── inference.py     # InferenceEngine：LLM 调用与流式输出
   │   │       ├── tool.py          # ToolEngine：工具注册、执行、确认
   │   │       ├── phase.py         # PhaseEngine：阶段规划与推进
   │   │       ├── memory.py        # MemoryEngine：上下文记忆管理
   │   │       ├── metrics.py       # MetricsEngine：Token/耗时/性能统计
   │   │       └── policy.py        # PolicyEngine：策略决策
│   │
│   ├── ui/                      # 纯 UI 组件，完全无业务逻辑
│   │   ├── __init__.py
│   │   ├── base.py              # ThemeManager、颜色表、工具函数
│   │   ├── window_frame.py      # 无边框窗口框架、边缘 resize、AppleMenu
│   │   ├── left_panel.py        # 左栏：Tab 切换、会话分组、功能页、文件管理器
│   │   ├── chat_area.py         # 中区：HeaderBar、ChatScene、SearchBar、InputArea
│   │   ├── right_panel.py       # 右栏：文件/终端/浏览器 Tab
│   │   ├── header_bar.py        # 标题栏
│   │   ├── input_area.py        # 输入区
│   │   ├── chat_items.py        # 聊天图形项
│   │   ├── chat_scene.py        # 聊天场景
│   │   ├── session_item.py      # 会话项
│   │   ├── session_group.py     # 会话分组
│   │   ├── function_page.py     # 功能页
│   │   ├── tab_button.py        # 右栏标签按钮
│   │   ├── recent_files.py      # 最近文件列表
│   │   ├── more_dropdown.py     # 标题栏更多菜单
│   │   ├── terminal_widget.py   # 终端占位组件
│   │   ├── file_reader_widget.py# 文件阅读器占位组件
│   │   ├── browser_widget.py    # 浏览器占位组件
│   │   ├── apple_menu.py        # Apple 风格菜单
│   │   └── settings_dialog.py   # 设置对话框
│   │
│   └── services/                # 与 V5 隔离的服务层
│       ├── __init__.py
│       ├── config_service.py
│       ├── session_service.py
│       └── chat_service.py
│
├── tests/v6/                    # V6 独立测试
│   ├── test_v6_smoke.py
│   ├── test_v6_ui_base.py
│   ├── test_v6_left_panel.py
│   ├── test_v6_chat_area.py
│   ├── test_v6_right_panel.py
│   ├── test_v6_runtime.py
│   └── test_v6_integration.py
│
└── docs/v6/                     # V6 文档
    ├── PROJECT_BLUEPRINT_v6.md  # 本文件
    ├── SPEC.md                  # 接口契约、信号契约、模块职责
    ├── ROADMAP.md               # 阶段计划
    └── CHANGELOG_v6.md          # V6 变更日志
```

## 阶段计划（每阶段结束必须 Review + Smoke + 存档）

### 阶段 0：骨架与规格（v6.0.0-alpha）
- 创建 `v6/` 目录结构。
- 编写本蓝图、`SPEC.md`、`ROADMAP.md`。
- 创建空模块与最小导入测试。
- Review Agent 校验目录与接口契约。
- Smoke：所有模块可 import 不报错。
- Git 存档：`v6.0.0-alpha`。

### 阶段 1：纯 UI 层（v6.1.0-alpha）✅ 已完成
- 实现 `ui/base.py` ThemeManager 与主题色板。
- 实现 `ui/window_frame.py` 无边框框架。
- 实现 `ui/session_item.py`、`ui/session_group.py`、`ui/function_page.py`。
- 实现 `ui/left_panel.py`（会话/功能 Tab、搜索、文件管理器占位）。
- 实现 `ui/header_bar.py`、`ui/input_area.py`、`ui/chat_items.py`、`ui/chat_scene.py`、`ui/chat_area.py`。
- 实现 `ui/tab_button.py`、`ui/recent_files.py`、`ui/right_panel.py`。
- 所有占位用 Demo 数据填充，确保 UI 可独立运行。
- Review Agent 校验：零业务逻辑、信号完整、单文件不过重。
- Smoke：`python v6/main_window.py` 可显示完整三栏 UI；契约测试 11/11 通过。
- Git 存档：`v6-ui-complete`（里程碑标签），版本号推进至 `v6.1.0-alpha`。

### 阶段 2：LayoutManager + MainWindow + UIController（v6.2.0-alpha）
- 实现 `layout_manager.py`：三栏尺寸策略、拖拽热区、折叠/展开。
- 重写 `main_window.py`：仅创建 Widget、转发 UI 事件、管理窗口行为。
- 实现 `ui_controller.py`：连接 UI 信号到 Runtime/Manager。
- Review Agent 校验：MainWindow 无业务逻辑。
- Smoke：窗口可拖拽、分栏可调、折叠/展开正常。
- Git 存档：`v6.2.0-alpha`。

### 阶段 3：SessionManager + ConfigManager（v6.3.0-alpha）✅ 已验收
- 实现 `config_manager.py`：基于 YAML，支持验证与热更新；`get/set/save` 接口 + `changed` 信号。
- 实现 `session_manager.py`：会话 CRUD、最近会话、SQLite 持久化、按时间分组、置顶、激活状态。
- 实现 `services/*`：与 UI 隔离的数据服务；`ChatService` 复用 `SessionManager.db_path`。
- 重写 `ui_controller.py`：移除 `DEMO_SESSIONS`，注入 Service，启动加载真实配置与会话。
- Review Agent 校验：数据层不依赖 Qt；单文件未超重；测试隔离良好。
- Smoke：会话创建/切换/删除/重命名/搜索可持久化；43/43 测试通过。
- Git 存档：`v6.3.0-alpha`。

### 阶段 4：AgentRuntime 骨架（v6.4.0-alpha）✅ 已验收
- 实现 `event_bus.py`：独立后台线程 + asyncio 队列，支持同步/异步订阅者。
- 实现 `context.py`：`RuntimeContext` 单次任务上下文，已加 `RLock` 线程安全保护。
- 实现 `scheduler.py`：任务队列、并发控制（默认 1）、取消、wait_all。
- 实现 `task.py`：`Task` / `ChatTask` / `AnalyzeTask`。
- 实现 `runtime.py`：`AgentRuntime` 生命周期、任务调度、错误转 `error` 事件、handler 注册。
- Runtime 与 UIController 已连接：`on_send_msg` 创建 `ChatTask` 提交到 Runtime，事件转 Qt 信号。
- Review Agent 校验：事件流清晰、Runtime 无 Qt 依赖、线程安全加固。
- Smoke：全量回归 64 个测试通过，集成测试覆盖 happy path。
- Git 存档：`v6.4.0-alpha`。

### 阶段 5：Engines（v6.5.0-alpha）✅ 已验收
- 依次实现八大引擎：`ContextEngine`、`PromptEngine`、`InferenceEngine`、`ToolEngine`、`PhaseEngine`、`MemoryEngine`、`MetricsEngine`、`PolicyEngine`。
- 统一接口：`async def run(ctx: RuntimeContext) -> RuntimeContext`；`RuntimeContext` 是唯一运行时状态对象，Engine 不拥有状态。
- `v6/runtime/engines/interfaces.py` 定义 `Engine` 基类与 `ChatMessage` 共享类型；`RuntimeContext` 可演进，Engine 只访问自身职责字段。
- 每个 Engine 独立测试，覆盖核心方法、异常路径、闭环反馈（MetricsEngine 上报）。
- Review Agent 校验：Engine 职责单一、接口契约一致、模块不超重、无循环导入、无 V5 混入。
- Smoke：全量回归 78 个测试通过，端到端 ChatTask 可运行。
- Git 存档：`v6.5.0-alpha`。

### 阶段 6：业务服务迁移与集成（v6.6.0-alpha）
- 将 V5 中可复用的核心逻辑（工具定义、适配器、持久化模式）提取到 V6 `services/` 和 `runtime/engines/`。
- 禁止直接复制 V5 文件，必须重写。
- Review Agent 校验：无 V5 代码残留、功能完整。
- Smoke：完整端到端流程通过。
- Git 存档：`v6.6.0-alpha`。

### 阶段 7：打包验证与最终存档（v6.7.0-alpha）
- 编写 `AgentWorkbenchV6.spec` 与 `scripts/rebuild_v6.ps1`。
- PyInstaller 打包验证，生成桌面快捷方式「AI Agent Workbench V6」。
- 全量测试通过。
- Review Agent 最终审查。
- Git 存档：`v6.7.0-alpha`。

## 与 V5 的关系
- V5 目录完整保留但冻结，作为反面教材与经验来源。
- 仅允许**人工阅读** V5 代码提取设计经验，不允许直接引用 V5 模块。
- V6 必须能够从 `config/config.yaml` 读取配置，但配置结构可在 V6 内部重新设计。

## 审核与协作流程
1. 每个阶段开始前，由 Plan Agent（或我）输出阶段任务清单。
2. UI Agent / Runtime Agent 并行或串行实现各自模块。
3. Review Agent 检查：
   - 是否遵循接口契约
   - 是否有业务逻辑侵入 UI
   - 单文件行数是否超标
   - 是否有测试覆盖
   - 是否有安全漏洞
4. 修复 Review Agent 提出的问题，直到通过。
5. 运行 Smoke 测试，通过则 Git 存档并打标签。
6. 进入下一阶段。
