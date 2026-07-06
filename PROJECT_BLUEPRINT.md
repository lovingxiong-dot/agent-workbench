---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v6.5.3-alpha | 存档次数 | 27 |

## 项目概要
v6.5.3-alpha 建立 Runtime Trace 基础能力：`RuntimeContext` 新增 `trace` 与 `result` 字段，每个 Task 自带执行历史；新增 `v6/runtime/trace.py` 定义 `RuntimeTrace`、`TraceStep` 与 `ReplayPlayer`，记录 `Task → Phase → Engine/Service/Tool → Finish` 全过程；`AgentRuntime` 自动记录任务生命周期（task_start / handler_dispatch / task_finish / task_error），`EchoHandler` 与 `LocalRuntimeAdapter` 记录 Engine / Adapter 步骤；`ReplayPlayer` 可按 trace 重放事件，支持调试与审计；`docs/v6/SPEC.md` 新增 Runtime Trace 原则与 RuntimeTask 四对象演进方向；V6 全量测试 99/99 通过。v6.5.2-alpha 完成 UIController 与 RuntimeAdapter 的 Application Boundary 集成：`AgentRuntime` 支持从 `Task.payload` 接收并使用已有的 `RuntimeContext`；`EchoHandler` 优先从 `ctx.messages` 读取输入；`UIController` 移除对 `AgentRuntime` 的直接依赖，改为依赖 `IRuntimeAdapter`，通过 `LocalRuntimeAdapter` 提交 `RuntimeContext`、订阅事件、取消任务；新增 `test_adapter_submit_propagates_context` 验证上下文经 Adapter 透传后状态一致；V6 全量测试 91/91 通过。v6.5.1-alpha 深化 V6 Runtime 协议与 Service 层改造：`RuntimeContext` 新增 `new()` 工厂方法，由 Runtime Task 自动生成 `task_id` 并初始化 Runtime Facts；`ConfigService` / `SessionService` / `ChatService` 统一为 `(ctx)` 输入接口，彻底移除 legacy 方法；`UIController` 全面改用 `RuntimeContext.new()` 构造上下文；`docs/v6/SPEC.md` 补充 Runtime Interface Principle、RuntimeContext 作为唯一 Public Runtime Protocol、Adapter Application Boundary 及 `RuntimeContext.new()` Task 语义等铁律；修复 `test_v6_ui_contract.py` 首行 docstring 语法错误；V6 全量测试 90/90 通过。AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、网页抓取、剪贴板管理等能力。v5.0.23-alpha 修复 `v5/service/chat_worker.py` 中 `AgentWorker.TOOL_DEFINITIONS` 属性错误，为 v4 归档区创建独立打包入口 `v4/v4_main.py` + `v4/AgentWorkbenchV4.spec` + `v4/scripts/rebuild_v4.ps1`，实现 v5 与 v4 并行打包并分别生成桌面快捷方式「AI Agent Workbench V5」和「AI Agent Workbench V4」；验证 `dist/AgentWorkbench/` 与 `dist/AgentWorkbenchV4/` 均可独立启动。v5.0.22-alpha 补充 `.gitignore`，将 `.reference/`、`.scripts/`、`review/` 等本地参考/调试/归档目录排除在版本控制外，保持 `git status` 干净。v5.0.21-alpha 完成工作区整理与文档同步：修正 `config.yaml` 版本号为 v5.0.20-alpha，统一以 `docs/` 为正式文档目录并在根目录新建 `README.md` 指向 docs/；将 `AgentWorkbench.spec` 与旧 `ui/`、`resources/`、`blueprints/`、`tests/test_v4_*.py` 等历史文件归档到 `v4/legacy/`、`v4/tests/`、`docs/archive/blueprints/`；清理 `docs/*.bak` 与空目录，同步根目录和 docs/ 下 `CHANGELOG.md` / `PROJECT_BLUEPRINT.md` 版本与目录树，全量测试 272/272 通过。v5.0.20-alpha 完成 V5 剩余 5% 细节功能闭环：修复 `v5/service/adapter.py` 工具执行回调命名冲突，实现终端日志与 UI 工具卡片同步输出；`ChatArea` 按 phase 渲染 `PhasePanel` 阶段面板，支持 analyze/confirm/execute/verify/archive 五种阶段；新增工具执行、确认回调、阶段渲染、craft 模式端到端流程等 11 个测试用例，全量测试 272/272 通过；修复 `AgentWorkbench.spec` 隐藏导入（移除已删除的 `v5.model.events`，添加 `v5.service.chat_worker`）并重新打包验证 exe 可独立启动。v5.0.19-alpha 修复聊天区模式列表与引擎不一致的核心 Bug，统一由 `WorkController.manual_modes` 动态管理模式列表；新增 V5 ChatArea / Adapter / Integration 测试共 78 个用例，全量测试 319/319 通过；修复 `AgentWorkbenchV5.spec` 隐藏导入并重新打包验证 exe 可独立启动。v5.0.18-alpha 完成 V5 P6/P7 收尾归档：提交 V5 新增测试、独立打包配置与 v4 归档说明，清理调试产物，全量测试 240/240 通过。v5.0.17-alpha 完成 V5 彻底隔离 v4 方案与 P6/P7 主体整改：清理 `v5/` 全部 v4 文字残留并确认无 v4 导入，统一 Widget 层 V5 标准信号契约，修复 `ChatArea`/`RightPanel`/`MainWindow` 信号连接，补齐终端/文件/浏览器用户操作信号转发到 `WorkController`，修正 `InvisibleResizeHandle` 布局问题；新增 `tests/test_v5_service.py`、`test_v5_controller.py`、`test_v5_smoke.py` 共 15 个用例；新增 `AgentWorkbenchV5.spec` 独立打包配置，新增 `v4/README.md` 标注归档废弃。v5.0.13-alpha 修复打包后浏览器标签不可用的问题：在 AgentWorkbench.spec 中显式打包 QtWebEngineProcess.exe、resources、qtwebengine_locales，并恢复 WebChannel/WebSockets/Sql 依赖，exe 内浏览器可正常加载 Bing 页面；v5.0.12-alpha 完成 UI 完全移植工程最终完整性检查与存档：复核 P10 旧 UI 清理与 PyInstaller 打包验证，完成 P11 `v4-refactor` 旧 UI 线路最终归档并推送 `v4.0.11-alpha` 归档标签，真实 GUI 验证三栏完整显示、无旧 UI 残留，全量测试 225/225 通过；v5.0.11-alpha 完成 P9 全量冒烟与集成测试验证及 UI 硬编码清理：清理 'v4 架构升级' 等旧 UI 硬编码文本，实现聊天区标题动态化；v5.0.9-alpha 完成新 UI 完全移植与旧 UI 清理；v5.0.8-alpha 完成 GUI 冒烟修复；v5.0.7-alpha 完成右栏真实功能回填；v5.0.6-alpha 完成持久化校验整改；v5.0.5-alpha 完成会话数据持久化与列表同步；v5.0.4-alpha 完成关键用户动作对接；v5.0.3-alpha 完成模块化骨架拆分；v5.0.2-alpha 完成 UIRenderer 与新 UI 桥接；v5.0.1-alpha 备份旧 UI 组件至 `v4/legacy/` 并标记 v5-dev 线路；v5.0.0-alpha 为 v5-dev 线路起点与新 UI 后端核心注入。v4.x 为旧 UI 完整版线路，已归档至 `v4-refactor` / `ui-template` 分支，不再维护。

## 技术栈
| 类别 | 技术 | 版本 | 用途 |
| 语言 | Python | 3.14 | 主语言 |
| UI 框架 | PySide6 | 6.21.0 | 桌面界面 (Fusion 深色主题) |
| LLM 框架 | LangChain + langchain-openai | latest | 工具调用与多模型对话 |
| 本地模型 | Ollama (OpenAI compatible) | latest | gemma2:2b / qwen3:4b 本地推理 |
| 云端模型 | DeepSeek API | V4 | deepseek-v4-flash / deepseek-v4-pro |
| 量化工具 | akshare + backtrader | latest | 股票数据 + 策略回测 |
| 交易接口 | MetaTrader5 Python API | latest | 实时报价 + 下单 |
| 打包工具 | PyInstaller | 6.21.0 | 一键生成 exe |
| 密钥管理 | python-dotenv | latest | .env 环境变量 |
| 持久化 | SQLite | built-in | 对话 / Token 追踪 |
| 配置格式 | YAML | built-in | 模式 / 工具 / 记忆配置 |

## 目录结构
```
/
├── main.py                 # 程序入口
├── AgentWorkbenchV5.spec   # PyInstaller V5 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore              # Git 忽略规则
│
├── config/                 # 配置分组
│   ├── config.yaml         # 全局配置（打包后可写副本位于 exe 同级 config/）
│   ├── .env                # 环境变量（API Keys，不提交）
│   └── .env.example        # 环境变量模板
│
├── assets/                 # 资源分组
│   └── app.ico             # 应用图标
│
├── scripts/                # 脚本分组
│   ├── rebuild.ps1         # 一键打包脚本
│   ├── runtime_hook.py     # PyInstaller 运行时钩子
│   └── start.bat           # 启动脚本
│
├── docs/                   # 文档分组
│   ├── README.md           # 项目总入口（定位、启动、文件地图）
│   ├── ARCHITECTURE.md     # 架构全景（Mermaid 图 + 核心概念 + 设计决策）
│   ├── CHANGELOG.md        # AI 维护的变更日志
│   ├── PROJECT_BLUEPRINT.md # 本文件
│   └── getting-started.md  # 5 分钟上手指南
│
├── # 源码分组
├── v6/                     # 【全新纯净主线】V6 从零重写
│   ├── __init__.py
│   ├── main_window.py      # 纯 UI 壳（仅创建 Widget + 转发事件 + 窗口行为）
│   ├── ui_controller.py    # UI 与业务唯一桥梁
│   ├── layout_manager.py   # 三栏布局/拖拽/折叠
│   ├── session_manager.py  # 会话 CRUD
│   ├── config_manager.py   # 配置管理
│   ├── runtime/            # AgentRuntime
│   │   ├── runtime.py
│   │   ├── context.py
│   │   ├── event_bus.py
│   │   ├── scheduler.py
│   │   ├── task.py
│   │   └── engines/        # Phase/Inference/Tool/Policy/Memory/Metrics
│   ├── ui/                 # 纯 UI 组件层
│   │   ├── base.py
│   │   ├── window_frame.py
│   │   ├── left_panel.py
│   │   ├── chat_area.py
│   │   ├── right_panel.py
│   │   ├── header_bar.py
│   │   ├── input_area.py
│   │   ├── chat_items.py
│   │   ├── chat_scene.py
│   │   ├── session_item.py
│   │   ├── session_group.py
│   │   ├── function_page.py
│   │   ├── tab_button.py
│   │   ├── recent_files.py
│   │   ├── more_dropdown.py
│   │   ├── terminal_widget.py
│   │   ├── file_reader_widget.py
│   │   ├── browser_widget.py
│   │   ├── apple_menu.py
│   │   └── settings_dialog.py
│   └── services/           # 业务服务
│       ├── config_service.py
│       ├── session_service.py
│       └── chat_service.py
│
├── v5/                     # 【只读归档区】V5 已冻结，不再维护
│   ├── __init__.py
│   ├── main.py             # V5 启动/引导、依赖组装
│   ├── main_window.py      # 轻量化顶层窗口（仅 UI 组装 + 单层信号转发）
│   ├── controller/
│   │   └── work_controller.py   # 全局唯一业务中枢
│   ├── service/            # V5 包装层，隔离根共享底层
│   │   ├── config_service.py
│   │   ├── session_service.py
│   │   ├── chat_service.py
│   │   └── adapter.py
│   ├── model/              # V5 标准化事件与数据模型
│   │   └── events.py
│   └── widgets/            # 纯 UI 层，禁止导入 controller/service
│       ├── base.py         # V5 主题、字体、SVG 工具
│       ├── window_frame.py # 无边框、拖拽、Apple 菜单
│       ├── left_panel.py   # 左侧功能/会话面板
│       ├── chat_items.py   # 聊天项卡片
│       ├── chat_scene.py   # 聊天图形渲染场景
│       ├── chat_area.py    # 中栏聊天区
│       ├── right_panel.py  # 右侧多标签容器
│       ├── terminal_widget.py     # 终端面板
│       ├── file_reader_widget.py  # 文件编辑器面板
│       ├── browser_widget.py      # 浏览器面板
│       ├── dropdown_selector.py   # 通用下拉选择器
│       └── settings_dialog.py     # 设置弹窗
│
├── v4/                     # 【只读归档区】旧 UI 完整版
│   ├── README.md           # 归档说明
│   ├── main_window.py      # 旧 UI 主窗口
│   ├── widgets/            # 旧 UI 控件库
│   ├── legacy/             # 更早版本 UI 备份
│   └── ...                 # 旧后端骨架（repository/orchestrator/worker 等）
│
├── agent_engine/           # 引擎层（v4/v5 共用）
│   ├── __init__.py
│   ├── agent_session.py    # 跨 Phase 复用会话
│   ├── llm_registry.py     # LLM 提供商注册与持久化
│   ├── memory_manager.py   # 会话记忆管理
│   ├── orchestrator.py     # 编排器（支持八引擎委托）
│   ├── phase_manager.py    # Phase-Driven Workflow Engine
│   └── engines/            # 八引擎模块
│       ├── __init__.py
│       ├── interfaces.py
│       ├── context_engine.py
│       ├── prompt_engine.py
│       ├── inference_engine.py
│       ├── tool_engine.py
│       ├── phase_engine.py
│       ├── memory_engine.py
│       ├── metrics_engine.py
│       └── policy_engine.py
├── tools/                  # 工具层
│   ├── __init__.py
│   ├── system.py           # 系统命令 / 文件读写 / 网络 / 剪贴板 / 通知 / 进程
│   ├── quant.py            # 股票数据 + 回测
│   ├── mt5.py              # MT5 报价 + 下单
│   ├── external_apis.py    # 财经新闻 / 宏观数据
│   └── screen.py           # 屏幕相关工具
├── core/                   # 核心基础设施
│   ├── __init__.py
│   ├── event_bus.py        # 基于 Qt Signal 的事件总线
│   └── events.py           # 强类型跨组件事件定义
├── services/               # 根共享服务层
│   ├── __init__.py
│   ├── config_service.py   # 配置读取与持久化
│   ├── session_service.py  # SQLite 对话持久化
│   ├── theme_service.py    # QSS 主题加载
│   ├── project_service.py  # 项目目录与会话关联
│   ├── activity_service.py # 活动记录持久化
│   ├── context_service.py  # 工作空间上下文
│   ├── path_resolver.py    # 路径解析
│   ├── python_resolver.py  # Python 解释器解析
│   ├── metrics_collector.py
│   ├── interpreter_service.py
│   ├── pending_queue.py
│   └── task_service.py
├── workers/                # 后台线程
│   ├── __init__.py
│   ├── agent_worker.py     # 流式 Agent 推理
│   ├── base_worker.py
│   ├── terminal_worker.py  # 终端命令输出捕获
│   ├── session_task.py
│   ├── task_capacity.py
│   └── task_queue.py
├── tests/                  # 测试分组（272 个 V5 单元 / 集成 / UI 测试）
│   ├── __init__.py
│   ├── integration/
│   │   └── integration_test_deepseek_metrics.py
│   ├── test_v5_service.py
│   ├── test_v5_controller.py
│   ├── test_v5_smoke.py
│   ├── test_agent_worker.py
│   ├── test_agent_session_integration.py
│   ├── test_agent_session_room.py
│   ├── test_async_tools.py
│   ├── test_context_service.py
│   ├── test_event_bus.py
│   ├── test_interpreter_service.py
│   ├── test_memory_manager.py
│   ├── test_metrics_collector.py
│   ├── test_mcp_service.py
│   ├── test_mt5_signal.py
│   ├── test_orchestrator_phase.py
│   ├── test_pending_queue.py
│   ├── test_persistence_service.py
│   ├── test_phase_manager.py
│   ├── test_self_context.py
│   ├── test_task_service_terminal.py
│   ├── test_threading_baseline.py
│   └── test_tool_gateway.py
│
└── storage/                # 运行时数据（SQLite / JSON，不提交）
    ├── conversations_v4.db
    ├── conversations.db
    ├── activities.json
    └── vector_store/
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v6.5.3-alpha | 2026-07-07 | Runtime Trace基础能力：RuntimeContext新增trace/result；新增v6/runtime/trace.py与ReplayPlayer；AgentRuntime/EchoHandler/Adapter记录执行步骤；SPEC补充Trace原则与RuntimeTask四对象演进；99/99测试通过 | feat/docs/test | v6/runtime/context.py, v6/runtime/runtime.py, v6/runtime/adapter.py, v6/runtime/trace.py, tests/v6/test_v6_trace.py, docs/v6/SPEC.md |

## 历史归档
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v6.5.2-alpha | 2026-07-07 | UIController↔RuntimeAdapter集成：AgentRuntime支持从Task.payload接收RuntimeContext；UIController改为依赖IRuntimeAdapter；新增Adapter上下文传播测试；91/91测试通过 | refactor/test | v6/runtime/runtime.py, v6/ui_controller.py, tests/v6/test_v6_runtime_adapter.py |
| v6.5.1-alpha | 2026-07-07 | V6 Runtime协议深化：RuntimeContext新增new()工厂自动生成task_id；Service层统一(ctx)接口；UIController全面改用RuntimeContext；SPEC补充Runtime Interface Principle与Task语义；修复测试docstring语法错误；90/90测试通过 | refactor/feat/docs/test | v6/runtime/context.py, v6/services/*.py, v6/ui_controller.py, tests/v6/*.py, docs/v6/SPEC.md |
| v6.0.0-alpha | 2026-07-07 | V6项目启动与架构规格：判定V5失败并归档冻结，启动V6从零重写；建立V6独立目录与架构文档；明确分层架构与专业Agent协作流程；新增模块import smoke测试5/5通过 | feat/docs/chore/test | v6/**, docs/v6/**, tests/v6/test_v6_smoke.py |
| v5.0.23-alpha | 2026-07-06 | 修复chat_worker.py TOOL_DEFINITIONS属性错误；创建v4独立打包入口/配置/脚本，实现v5与v4并行打包及桌面快捷方式；验证dist/AgentWorkbench/与dist/AgentWorkbenchV4/均可独立启动；272/272测试通过 | fix/build/chore | v5/service/chat_worker.py, v4/v4_main.py, v4/AgentWorkbenchV4.spec, v4/scripts/rebuild_v4.ps1, scripts/rebuild.ps1, v4/README.md |
| v5.0.22-alpha | 2026-07-06 | 补充.gitignore：排除.reference/、.scripts/、review/等本地参考/调试/归档目录，保持git status干净 | chore | .gitignore |
| v5.0.21-alpha | 2026-07-06 | 工作区整理与文档同步：修正config.yaml版本号，统一docs/为正式文档目录，根目录新建README.md；归档AgentWorkbench.spec、ui/、resources/、blueprints/、v4测试到v4/legacy/、v4/tests/、docs/archive/blueprints/；清理.bak与空目录，同步根目录与docs/下CHANGELOG/PROJECT_BLUEPRINT，272/272测试通过 | chore/docs/archive/test | README.md, CHANGELOG.md, PROJECT_BLUEPRINT.md, docs/README.md, docs/CHANGELOG.md, docs/PROJECT_BLUEPRINT.md, config/config.yaml, AgentWorkbenchV5.spec, scripts/rebuild.ps1, v4/legacy/, v4/tests/, docs/archive/blueprints/ |
| v5.0.20-alpha | 2026-07-06 | V5剩余5%细节功能闭环：修复adapter.py工具执行回调命名冲突，ChatArea按phase渲染阶段面板，新增工具执行/确认/阶段渲染/craft端到端测试，全量272/272通过；修复AgentWorkbenchV5.spec隐藏导入并重新打包验证exe启动 | fix/feat/test/build | v5/service/adapter.py, v5/widgets/chat_area.py, v5/widgets/chat_items.py, tests/test_v5_*.py, AgentWorkbenchV5.spec |
| v5.0.19-alpha | 2026-07-06 | 修复聊天区模式列表与引擎不一致Bug，WorkController.manual_modes动态管理模式；新增V5 ChatArea/Adapter/Integration测试78用例，319/319通过；修复AgentWorkbenchV5.spec隐藏导入并打包验证 | fix/test/build | v5/widgets/chat_area.py, v5/controller/work_controller.py, tests/test_v5_*.py, AgentWorkbenchV5.spec |
| v5.0.18-alpha | 2026-07-06 | V5 P6/P7收尾归档：提交v5新增测试、独立打包配置与v4归档说明，清理调试产物，README/PROJECT_BLUEPRINT/CHANGELOG版本对齐，240/240测试通过 | docs/archive/test/build | tests/test_v5_*.py, AgentWorkbenchV5.spec, v4/README.md, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.17-alpha | 2026-07-06 | V5彻底隔离v4与P6/P7主体整改：清理v5/全部v4文字残留并确认无v4导入；统一Widget层V5信号契约，修复ChatArea/RightPanel/MainWindow连接，补齐终端/文件/浏览器用户操作信号；修正InvisibleResizeHandle布局；新增15个V5测试，240/240测试通过；新增AgentWorkbenchV5.spec与v4/README.md归档说明 | refactor/test/build/docs | v5/**, tests/test_v5_*.py, AgentWorkbenchV5.spec, v4/README.md, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.12-alpha | 2026-07-06 | UI完全移植工程最终完整性检查与存档：复核P10旧UI清理与PyInstaller打包验证，完成P11 v4-refactor旧UI线路最终归档并推送v4.0.11-alpha标签，真实GUI验证三栏完整显示，225/225测试通过 | docs/archive/test | docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.11-alpha | 2026-07-06 | P9全量冒烟与集成测试验证及UI硬编码清理：真实GUI启动验证三栏完整显示，清理'v4 架构升级'等旧UI硬编码，实现聊天区标题动态化，225/225测试通过 | fix/test/ui | v4/widgets/chat_area.py, v4/widgets/right_panel.py, v4/widgets/left_panel.py, v4/main_window.py, tests/test_v4_gui_smoke.py |
| v5.0.10-alpha | 2026-07-06 | v5项目文档同步：README/PROJECT_BLUEPRINT/CHANGELOG全面更新为v5新UI完整版线路，反映v5.0.0~v5.0.9全部阶段成果，目录结构同步v4/widgets/与v4/legacy/，测试数更新为225 | docs | docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.9-alpha | 2026-07-06 | P10清理旧UI与打包验证：删除v4根目录重复旧UI文件（已备份至v4/legacy/），迁移旧测试导入，更新AgentWorkbench.spec hiddenimports为v4.widgets.*，PyInstaller打包成功并验证exe独立启动 | chore/build/test | AgentWorkbench.spec, v4/legacy/*, tests/test_v4_input_area.py, tests/test_v4_right_panel.py |
| v5.0.8-alpha | 2026-07-06 | P8完整功能回填GUI冒烟修复：修复ChatArea中QPen导入缺失导致的paintEvent崩溃，验证三栏加载/会话创建/UI事件分发正常 | fix/ui/test | v4/widgets/chat_area.py |
| v5.0.7-alpha | 2026-07-06 | P7右栏真实功能回填：实现TerminalWidget/FileReaderWidget/BrowserWidget并集成到RightPanel；最近文件列表及点击打开；同步会话项目路径到终端工作目录 | feat/ui/test | v4/widgets/right_panel.py, v4/widgets/terminal_widget.py, v4/widgets/file_reader_widget.py, v4/widgets/browser_widget.py, workers/terminal_worker.py, tests/test_v4_widgets_right_panel.py |
| v5.0.6-alpha | 2026-07-06 | P5/P6持久化校验与测试整改：增强app.last_mode/last_model启动与设置应用校验，补充主题键backward compatibility，新增边界测试 | fix/test | v4/main_window.py, v4/widgets/base.py, tests/test_v4_integration.py |
| v5.0.5-alpha | 2026-07-06 | P5会话数据持久化与列表同步：实现last_session_id持久化与启动恢复、会话切换/创建/删除配置同步、无效会话清理、左栏空状态显示 | feat/test | v4/main_window.py, v4/widgets/left_panel.py, v4/repository.py |
| v5.0.4-alpha | 2026-07-06 | P4关键用户动作对接：停止/确认/分析按钮、导出会话、设置对话框、搜索过滤、模式模型下拉选择器 | feat/ui | v4/main_window.py, v4/widgets/chat_area.py, v4/widgets/left_panel.py, v4/widgets/dropdown_selector.py, v4/widgets/settings_dialog.py |
| v5.0.3-alpha | 2026-07-06 | 模块化骨架拆分与致命Bug修复：将v4/main_window.py拆分为v4/widgets/9个模块，修复_session_idx_map为空问题 | refactor/fix | v4/widgets/*, v4/main_window.py |
| v5.0.2-alpha | 2026-07-06 | P3 UIRenderer与新UI桥接完成：ChatArea真实消息渲染/流式输出/确认条/阶段状态，LeftPanel会话列表刷新与badge更新 | feat/ui | v4/widgets/chat_area.py, v4/widgets/left_panel.py, v4/ui_renderer.py |
| v5.0.1-alpha | 2026-07-06 | 备份v4旧UI组件至v4/legacy/并标记v5-dev线路 | chore/docs | v4/legacy/*, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.0-alpha | 2026-07-06 | v5-dev线路起点与新UI后端核心注入 | feat/ui | v4/main_window.py, v4/widgets/* |
| v4.0.7-alpha | 2026-07-01 | 标题栏三键（搜索/更多/展开）+ execute步骤条自动解析；三键图标改为SVG path并接入搜索高亮/更多菜单/全局快捷键；docs/ui/归档6 SVG+2 spec | feat/docs/fix | v4/main_window.py, v4/ui_renderer.py, AgentWorkbench.spec, docs/ui/* |
| v4.0.6-alpha | 2026-07-01 | 补齐目录标准化遗漏：`AgentWorkbench.spec` datas加入`assets/app.ico`；`services/project_service.py`改用`_get_app_root()`定位`storage/activities.json`，避免exe在CWD创建storage | fix/build | AgentWorkbench.spec, services/project_service.py |
| v4.0.5-alpha | 2026-06-30 | 工程目录标准化改造：根目录文件按职责分组为config/、assets/、scripts/、docs/，源码目录统一标注为src/分组；同步修正PyInstaller datas、runtime_hook、图标路径、config_service/LLMRegistry路径解析及所有代码中的配置路径引用；README/ARCHITECTURE/PROJECT_BLUEPRINT/getting-started同步更新 | refactor/docs/build | AgentWorkbench.spec, scripts/rebuild.ps1, services/config_service.py, agent_engine/llm_registry.py, v4/main_window.py, v4/worker.py, v4/repository.py, services/activity_service.py, services/session_service.py, docs/README.md, docs/ARCHITECTURE.md, docs/PROJECT_BLUEPRINT.md, docs/getting-started.md |
| v4.0.4-alpha | 2026-06-30 | v4对话UI三层折叠结构：阶段面板始终展开、工具执行与思考过程默认收起、内部命令输出超长折叠；左栏会话列表精简为标题+最后消息预览+时间三字段；新增无LLM依赖的UI折叠验证脚本 | feat/test | v4/main_window.py, v4/ui_renderer.py, v4/conversation_list.py, v4/events.py, v4/orchestrator.py, v4/worker.py, v4/worker_manager.py, tests/test_v4_integration.py, scripts/verify_ui_fold.py |
| v4.0.3-alpha | 2026-06-30 | Phase工作流接入v4：V4Worker内建PhaseEngine支持craft模式analyze→confirm→execute→verify→archive完整流程；analyze/verify阶段解绑工具强制文本输出；PyInstaller spec适配v4单轨架构；清理27个零引用v2/v3文件；修复用户停止任务CANCELLED状态与Worker销毁 | feat/refactor/fix | v4/worker.py, v4/orchestrator.py, v4/worker_manager.py, v4/event_bus.py, v4/events.py, AgentWorkbench.spec, tests/test_v4_integration.py |
| v4.0.2-alpha | 2026-06-30 | v4原生Worker八引擎推理：新建v4/worker.py以V4Worker(QThread+asyncio)直驱ReAct循环，零绞杀者依赖旧AgentWorker/AgentOrchestrator/AgentSession；worker_manager接入V4Worker替代EngineWorker；orchestrator传递user_text到WorkerCreateEvent | feat/refactor | v4/worker.py, v4/worker_manager.py, v4/orchestrator.py, v4/events.py, v4/main_window.py |
| v4.0.1-alpha | 2026-06-30 | v4 Solo极简UI重构：固定两栏布局（左280px/右填充）、主题切换按钮（🌙/☀️ 暗色/浅色持久化到config.yaml）、会话列表极简化（标题+预览+时间）、延迟创建会话（首条消息才写DB） | feat/test | v4/main_window.py, v4/conversation_list.py, config.yaml, tests/test_v4_gui_smoke.py, tests/test_v4_integration.py |
| v3.12.0 | 2026-06-30 | AI Engine 架构升级：八引擎模块化 + System Prompt 增强 + LLM 参数可配 + 记忆路径修正 + 绞杀者集成 | feat/refactor/fix | agent_engine/engines/*.py, agent_engine/orchestrator.py, agent_engine/llm_registry.py, services/self_context.py, config.yaml, ui/main_window.py, tests/test_self_context.py |
| v3.11.4 | 2026-06-29 | MainWindow 架构收敛重构：移除 _pending_queue/_worker/_workers/_phase_manager 等旧全局状态，统一走 v3 MessageBus 路径；修复新会话按钮只能添加一个标签、会话标签名均为"新对话"、Enter 键首次失效（新增 `_focus_input_field` 强制焦点）、切换新会话显示无意义接替上下文；补充 FileTreeWidget.get_root_path 与 SessionManager Qt 导入修复；新增 MainWindow UI 自动化测试 | fix/refactor/test | ui/main_window.py, ui/widgets/sidebar.py, ui/managers/session_manager.py, services/self_context.py, tests/test_main_window_ui_automation.py |
| v3.11.3 | 2026-06-29 | 修复真实运行时 WorkerManager 无法解析 LLM、Phase 错误后未 reset、空对话守卫导致单标签、新建会话后 Orchestrator 当前会话不同步、SessionManager 标题 data role 错误；新增 pytest.ini 排除 scripts 测试噪音 | fix | ui/managers/worker_manager.py, ui/managers/phase_coordinator.py, services/session_orchestrator.py, ui/main_window.py, ui/managers/session_manager.py, pytest.ini |
| v3.11.2 | 2026-06-29 | 修复 v3 Worker 重复创建导致无响应：Orchestrator 移除 worker.created/execute_required/verify_required 重复订阅；新 runtime 创建后同步 UI 队列状态；README 与文档规范化 | fix/docs | services/session_orchestrator.py, tests/integration/test_v3_flow.py, README.md, docs/getting-started.md, PROJECT_BLUEPRINT.md |
| v3.11.1 | 2026-06-29 | 修复 v3 事件流：Worker 创建后立即 analyze、会话切换同步队列 UI、历史会话自动创建 runtime、切换不误杀后台任务 | fix/refactor | core/events.py, ui/managers/worker_manager.py, services/session_orchestrator.py, ui/main_window.py, ui/managers/session_manager.py, README.md |
| v3.11.0 | 2026-06-29 | 工程标准化：新增 README、ARCHITECTURE、blueprints/、docs/getting-started | docs | README.md, ARCHITECTURE.md, blueprints/*.md, docs/*.md |
| v3.9.1 | 2026-06-29 | 修复 Phase 状态机重入与任务状态回收：调整 flow_finished/reset 顺序、统一 TaskService.complete_task 调用、修复会话切换覆盖 completed 状态、补充 completed 绿色图标、修复 SessionManager 标题更新 data role | fix/refactor | agent_engine/phase_manager.py, services/task_service.py, services/pending_queue.py, services/self_context.py, ui/main_window.py, ui/widgets/conversation.py, ui/chat_view.py, workers/agent_worker.py, tests/test_pending_queue.py, tests/test_self_context.py, ui/managers/*.py |
| v3.9.0 | 2026-06-27 | 多任务管理系统（TaskService+WorkerPool）、Session-as-Room 会话隔离、Trae 暗黑主题、底栏容量状态条、会话状态图标、信号调试管道 | feat/fix | services/task_service.py, workers/task_capacity.py, workers/task_queue.py, workers/worker_pool.py, workers/session_task.py, workers/task_worker_adapter.py, resources/themes/trae_dark.qss, services/theme_service.py, ui/main_window.py, ui/widgets/conversation.py, ui/chat_view.py, agent_engine/agent_session.py, workers/agent_worker.py, config.yaml, AgentWorkbench.spec, tests/test_agent_session_integration.py, tests/test_main_window_session_isolation.py |
| v3.8.1 | 2026-06-27 | 填充架构占位文件、对话气泡排版优化、活动面板多选增强、屏幕工具注册 | feat/fix | tools/screen.py, tools/__init__.py, ui/overlay.py, ui/settings.py, ui/tools_panel.py, ui/chat_view.py, ui/widgets/activity_panel.py, workers/agent_worker.py, config.yaml |
| v3.8.0 | 2026-06-27 | MVC资源管理器、PersistenceService持久化、MemoryManager画像schema、工具注册与依赖对齐 | feat/fix | ui/models/explorer_tree_model.py, ui/widgets/explorer_view.py, ui/widgets/explorer.py, services/persistence_service.py, agent_engine/memory_manager.py, config.yaml, workers/agent_worker.py, requirements.txt, AgentWorkbench.spec, tests/* |
| v3.7.4 | 2026-06-27 | Analyze 阶段强制只读工具与结果截断对齐 | fix/feat | agent_engine/orchestrator.py, agent_engine/agent_session.py |
| v3.7.3 | 2026-06-26 | 分级超时与持久化路径修复 | fix/feat | agent_engine/orchestrator.py, agent_engine/memory_manager.py, workers/agent_worker.py, services/config_service.py, tools/system.py, ui/main_window.py, config.yaml |
| v3.7.2 | 2026-06-26 | 修复 v3.7.1 中窗口标题初始化顺序导致的打包启动崩溃 | fix | ui/main_window.py |
| v3.7.1 | 2026-06-26 | 修复启动时解释器检测弹窗、历史会话 AI 回复丢失、终端输入框无法编辑；窗口标题动态读取版本号；活动面板增强说明/全局分类/右键复制 | fix/feat | services/interpreter_service.py, ui/main_window.py, ui/widgets/terminal.py, ui/widgets/activity_panel.py, config.yaml |
| v3.7 | 2026-06-26 | 终端解释器管理：自动发现 Python(venv/系统)/PowerShell/CMD/Git Bash、TerminalWidget 下拉切换、解释器上下文注入 prompt、run_python/run_powershell/run_bash 工具、相关 bug 修复 | feat/fix | services/interpreter_service.py, services/context_service.py, ui/main_window.py, ui/widgets/terminal.py, ui/widgets/workspace.py, workers/terminal_worker.py, tools/system.py, config.yaml, AgentWorkbench.spec, tests/test_interpreter_service.py |
| v3.6 | 2026-06-26 | Phase-Driven Workflow Engine：Mode×Phase 矩阵、Analyze→Confirm→Execute→Verify→Archive 阶段流转、软硬 Checkpoint、任务清单驱动、UI 阶段指示器与确认门控 | feat | agent_engine/phase_manager.py, agent_engine/orchestrator.py, services/context_service.py, ui/main_window.py, ui/chat_view.py, workers/agent_worker.py, AgentWorkbench.spec, tests/test_phase_manager.py |
| v3.5 | 2026-06-26 | 请求级指标：token/耗时收集、AI 气泡下方显示 metrics、日志输出 TTFT 详情 | feat | services/metrics_collector.py, agent_engine/orchestrator.py, workers/agent_worker.py, workers/base_worker.py, ui/main_window.py, ui/chat_view.py |
| v3.4 | 2026-06-26 | 工作空间上下文感知：自动检测项目目录、右侧文件摘要注入 prompt、文件工具相对路径解析、最近项目下拉 | feat | services/context_service.py, services/path_resolver.py, services/project_service.py, agent_engine/orchestrator.py, tools/system.py, ui/main_window.py, ui/widgets/document_editor.py, ui/widgets/workspace.py, ui/widgets/sidebar.py, ui/widgets/status_indicator.py, workers/agent_worker.py, config.yaml, AgentWorkbench.spec, tests/test_context_service.py |
| v3.3 | 2026-06-25 | 精细化打磨：任意格式文件预览、对话/活动分栏、文档编辑快捷键、修复模型持久化与活动重复记录 | feat/fix | ui/widgets/document_editor.py, ui/widgets/conversation.py, ui/widgets/activity_panel.py, services/activity_service.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3.2 | 2026-06-25 | 项目目录与对话上下文：资源管理器切换/打开文件夹、按目录组织会话、目录下开启新对话 | feat/refactor | services/project_service.py, services/session_service.py, ui/widgets/sidebar.py, ui/widgets/conversation.py, ui/main_window.py, config.yaml, resources/themes/dark_github.qss |
| v3.1 | 2026-06-25 | 重建右侧工作区：终端/日志/文档标签页、左侧文件树联动文档编辑器、文本文件编辑模式 | feat/refactor | ui/widgets/workspace.py, ui/widgets/document_editor.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3 | 2026-06-25 | 工具分层编排、AI身份系统、17工具库、UI全栈修复 | feat/fix | agent_worker, config, main_window, tools/* |
| v0.3 | 2026-06-25 | v2生产级重构：模块化架构、8工具、流式UI | feat/refactor | 全部模块 |
| v0.2 | 2026-06-25 | DeepSeek密钥修复与模型选择下拉功能 | feat/fix | config.yaml, llm_registry.py, main.py |
| v0.1 | 2026-06-24 | 初始提交AI工作台项目 | feat | main.py, config.yaml, agent_engine/, tools/ |

## 存档流程
1. 更新 docs/CHANGELOG.md + docs/PROJECT_BLUEPRINT.md + docs/README.md + docs/ARCHITECTURE.md + blueprints/ + docs/（全部项目文档）
2. git add -u && git add docs/CHANGELOG.md docs/PROJECT_BLUEPRINT.md（覆盖已跟踪修改 + 两个维护文件）
3. git commit -m "..." + git tag vX.Y.Z
4. git push + git push origin vX.Y.Z（仅当前分支 + 当前标签，禁 --tags）

_更新于 2026-07-06 by AI-Kimi-K2.7-Code_

## Agent交接记录
| 时间 | 方向 | 从 | 到 | 交接点 | 备注 |
|---|---|---|---|---|---|
| 2026-06-27T19:00 | 移交 | Kimi-K2.7-Code | — | v3.9.0 存档后 | 多任务管理系统+Session-as-Room+Trae暗黑主题已完成，全部单测通过，已推送 |

---
