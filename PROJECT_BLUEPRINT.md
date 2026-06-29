---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v3.11.2 | 存档次数 | 23 |

## 项目概要
AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、MT5 交易、网页抓取、剪贴板管理等能力。v3.1 完成右侧工作区重构；v3.2 引入项目目录上下文；v3.3 对文件预览、对话分栏、活动面板、文档编辑进行精细化打磨；v3.4 让 Agent 具备工作空间感知能力，能自动识别当前项目目录、右侧打开文件，并基于项目根目录解析工具相对路径。v3.5 引入请求级指标（token/耗时）并在 AI 气泡下方显示。v3.6 引入 Phase-Driven Workflow Engine：将每次请求按 Mode 切分为 Analyze → Confirm → Execute → Verify → Archive 阶段，Mode 与 Phase 正交，硬门控/软提示分离，任务清单驱动执行。v3.7 引入 InterpreterService，支持终端解释器自动发现、手动切换与 AI 上下文感知。v3.7.1 修复启动时解释器检测弹窗、历史会话 AI 回复丢失、终端输入框无法编辑等问题，并增强活动面板交互与窗口标题版本可持续迭代。v3.7.2 修复 v3.7.1 中窗口标题初始化顺序导致的打包启动崩溃。v3.8.1 填充 4 个架构占位文件（screen/overlay/settings/tools_panel），优化对话气泡排版与活动面板多选交互。v3.11.0 进行 v3 架构重构：引入事件总线（MessageBus）作为唯一跨组件通信层，每个会话拥有独立的运行时聚合根（SessionRuntime），由 SessionOrchestrator 统一协调；PhaseCoordinator、WorkerManager、UIRenderer 全部基于事件驱动，TaskService 增加终态保护，彻底解决会话切换状态覆盖、队列槽位不归零、任务状态不回收等历史问题。

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
├── agent_engine/           # 引擎层
│   ├── __init__.py
│   ├── classifier.py       # 意图分类
    ├── llm_registry.py     # LLM 提供商注册与持久化
    ├── memory_manager.py   # 会话记忆管理
    ├── mode_manager.py     # 手动模式管理
    ├── orchestrator.py     # 编排器
    ├── phase_manager.py    # Phase-Driven Workflow Engine
    └── proactive_engine.py # 主动引擎
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
├── services/               # 服务层
│   ├── __init__.py
│   ├── config_service.py   # 配置读取与持久化
│   ├── session_service.py  # SQLite 对话 + Token 用量持久化
│   ├── theme_service.py    # QSS 主题加载
│   ├── project_service.py  # 项目目录与会话关联管理
│   ├── app_context.py      # 服务容器与生命周期管理
│   ├── activity_service.py # 结构化活动记录与持久化
│   ├── context_service.py  # 当前工作空间上下文维护
│   ├── path_resolver.py    # 基于项目根目录的路径解析
│   ├── python_resolver.py  # 项目 Python 解释器解析
│   ├── metrics_collector.py # 请求级指标收集（token/耗时）
│   ├── interpreter_service.py # 终端解释器发现/选择/持久化
│   ├── pending_queue.py    # 双槽位等待队列
│   ├── session_runtime.py  # 会话运行时聚合根
│   ├── session_orchestrator.py # v3 统一协调器
│   └── task_service.py     # 任务调度中心
├── workers/                # 后台线程
│   ├── __init__.py
│   ├── agent_worker.py     # 流式 Agent 推理 + 工具调用
│   ├── base_worker.py      # Worker 基类
│   ├── terminal_worker.py  # 终端命令输出捕获
│   ├── verification_worker.py # 本地验证（语法检查/单元测试）
│   ├── session_task.py     # 会话级任务状态
│   ├── task_capacity.py    # 资源容量控制
│   └── task_queue.py       # FIFO 任务排队
├── ui/                     # 界面层
│   ├── __init__.py
│   ├── main_window.py      # 主窗口全局状态与信号协调
│   ├── chat_view.py        # 聊天视图（简约气泡、模型下拉、快捷按钮）
│   ├── overlay.py          # 覆盖层组件
│   ├── settings.py         # 设置相关 UI
│   ├── tools_panel.py      # 工具面板
│   ├── widgets/            # 可复用组件
│   │   ├── __init__.py
│   │   ├── sidebar.py      # 图标栏 + 文件树 + 最近项目
│   │   ├── conversation.py # 分栏对话列表（当前项目 / 全局）
│   │   ├── tasks.py        # 任务面板
│   │   ├── terminal.py     # 终端控制台
│   │   ├── status_indicator.py # 状态指示器
│   │   ├── workspace.py    # 右侧工作区（终端/活动/文档标签）
│   │   ├── document_editor.py  # 文档查看与编辑器
│   │   ├── activity_panel.py   # 结构化活动面板
│   │   └── shared_output.py    # 共享输出面板
│   │   
│   ├── models/             # 数据模型
│   │   └── explorer_model.py   # 资源管理器数据模型
│   ├── managers/           # v3 事件驱动管理器
│   │   ├── __init__.py
│   │   ├── phase_coordinator.py # PhaseManager → MessageBus 桥接
│   │   ├── queue_manager.py     # 双槽位队列状态机
│   │   ├── signal_adapter.py    # Worker 信号 → MessageBus 事件
│   │   ├── ui_renderer.py       # UI 事件统一渲染器
│   │   └── worker_manager.py    # Worker 生命周期管理
│   ├── dialogs/            # 对话框
│   │   ├── __init__.py
│   │   └── settings.py     # 模型设置 / 规则设置
├── resources/              # 静态资源
│   └── themes/
│       └── dark_github.qss # GitHub Dark 主题
├── tests/                  # 单元测试 / 集成测试
│   ├── __init__.py
│   ├── integration/
│   │   └── test_v3_flow.py       # v3 事件流集成测试
│   ├── test_agent_worker.py
│   ├── test_agent_session_integration.py
│   ├── test_async_tools.py
│   ├── test_context_service.py
│   ├── test_event_bus.py
│   ├── test_explorer_model.py
│   ├── test_main_window_mode_agnostic_result.py
│   ├── test_main_window_session_isolation.py
│   ├── test_metrics_collector.py
│   ├── test_orchestrator_phase.py
│   ├── test_phase_coordinator.py
│   ├── test_phase_manager.py
│   ├── test_pending_queue.py
│   ├── test_self_context.py
│   ├── test_session_orchestrator.py
│   ├── test_session_runtime.py
│   ├── test_task_service_terminal.py
│   ├── test_tool_gateway.py
│   ├── test_ui_renderer.py
│   └── test_interpreter_service.py
├── main.py                 # 程序入口
├── config.yaml             # 全局配置
├── .env                    # 环境变量（API Keys，不提交）
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略规则
├── requirements.txt        # Python 依赖
├── AgentWorkbench.spec     # PyInstaller 打包配置
├── runtime_hook.py         # PyInstaller 运行时钩子
├── rebuild.ps1             # 一键打包脚本
├── start.bat               # 启动脚本
├── app.ico                 # 应用图标
├── README.md               # 项目总入口（定位、启动、文件地图）
├── ARCHITECTURE.md         # 架构概览（Mermaid 图、核心概念、设计决策）
├── blueprints/             # 工程蓝图（从 .trae/documents/ 提炼）
│   ├── index.md            # 蓝图索引（按时间线/模块）
│   ├── session/
│   │   ├── v3-event-bus-architecture.md  # v3 事件总线架构
│   │   └── v2-multi-session-design.md    # v2 多会话管理
│   └── integration/
│       └── workspace-context.md          # 工作空间上下文感知
├── docs/                   # 开发者文档
│   └── getting-started.md  # 5 分钟上手指南
├── CHANGELOG.md            # AI 维护的变更日志
└── PROJECT_BLUEPRINT.md    # 本文件
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v3.11.2 | 2026-06-29 | README 质量修正：补全开发环境指引（cd/venv/start.bat/rebuild.ps1）、去除 MT5 头版定位、同步更新 docs/getting-started、存档流程规则对齐（git add 扩展文档目录、禁 --tags） | docs/fix | README.md, docs/getting-started.md, PROJECT_BLUEPRINT.md |
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
1. 更新 CHANGELOG.md + PROJECT_BLUEPRINT.md + README.md + ARCHITECTURE.md + blueprints/ + docs/（全部项目文档）
2. git add -u && git add ARCHITECTURE.md blueprints/ docs/ README.md（覆盖已跟踪修改 + 新文档）
3. git commit -m "..." + git tag vX.Y.Z
4. git push + git push origin vX.Y.Z（仅当前分支 + 当前标签，禁止 --tags）

_更新于 2026-06-29 16:00:00 by AI-Claude-4.5-Opus_

## Agent交接记录
| 时间 | 方向 | 从 | 到 | 交接点 | 备注 |
|---|---|---|---|---|---|
| 2026-06-27T19:00 | 移交 | Kimi-K2.7-Code | — | v3.9.0 存档后 | 多任务管理系统+Session-as-Room+Trae暗黑主题已完成，全部单测通过，已推送 |

---
