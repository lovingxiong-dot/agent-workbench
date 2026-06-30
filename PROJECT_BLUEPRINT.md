---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v4.0.3-alpha | 存档次数 | 30 |

## 项目概要
AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、网页抓取、剪贴板管理等能力。v4.0.3-alpha 在原生 V4Worker 中内建 PhaseEngine，支持 craft 模式 analyze→confirm→execute→verify→archive 完整流程；同步完成 PyInstaller 打包适配并清理 27 个零引用 v2/v3 文件，实现 v4 单轨架构闭环。

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
│   ├── agent_session.py    # 跨 Phase 复用会话
│   ├── llm_registry.py     # LLM 提供商注册与持久化
│   ├── memory_manager.py   # 会话记忆管理
│   ├── orchestrator.py     # 编排器（绞杀者：支持八引擎委托）
│   ├── phase_manager.py    # Phase-Driven Workflow Engine
│   ├── engines/            # v3.12 八引擎模块
│   │   ├── __init__.py
│   │   ├── interfaces.py       # 8 引擎接口 + 共享 dataclass
│   │   ├── context_engine.py   # 上下文组装与压缩
│   │   ├── prompt_engine.py    # System prompt 构建
│   │   ├── inference_engine.py # LLM 调用 + 重试/降级
│   │   ├── tool_engine.py      # 工具执行与权限
│   │   ├── phase_engine.py     # Phase 流转管理
│   │   ├── memory_engine.py    # 三层记忆系统
│   │   ├── metrics_engine.py   # 指标采集与聚合
│   │   └── policy_engine.py    # 策略决策驱动
├── tools/                  # 工具层
│   ├── __init__.py
│   ├── system.py           # 系统命令 / 文件读写 / 网络 / 剪贴板 / 通知 / 进程
│   ├── quant.py            # 股票数据 + 回测
│   ├── mt5.py              # MT5 报价 + 下单
│   ├── external_apis.py    # 财经新闻 / 宏观数据
│   └── screen.py           # 屏幕相关工具
├── core/                   # 核心基础设施（v3 兼容）
│   ├── __init__.py
│   ├── event_bus.py        # 基于 Qt Signal 的事件总线
│   └── events.py           # 强类型跨组件事件定义
├── v4/                     # v4 单轨事件总线架构
│   ├── __init__.py
│   ├── models.py           # 不可变数据模型
│   ├── event_bus.py        # v4 MessageBus
│   ├── events.py           # v4 事件协议
│   ├── repository.py       # SQLite 会话/消息/环境/任务状态仓库
│   ├── queue.py            # 会话级双槽位队列
│   ├── runtime.py          # SessionRuntime 聚合根
│   ├── worker_manager.py   # 系统级 Worker 并发管理
│   ├── orchestrator.py     # SessionOrchestrator 统一协调器
│   ├── ui_renderer.py      # UI 渲染器
│   ├── conversation_list.py # 会话列表控件
│   ├── main_window.py      # v4 薄主窗口
│   └── tests/              # v4 内部单元测试
│       └── test_orchestrator.py
├── services/               # 服务层（v3 兼容，v4 核心逻辑已迁移至 v4/）
│   ├── __init__.py
│   ├── config_service.py   # 配置读取与持久化
│   ├── session_service.py  # SQLite 对话 + Token 用量持久化
│   ├── theme_service.py    # QSS 主题加载
│   ├── project_service.py  # 项目目录与会话关联管理
│   ├── activity_service.py # 结构化活动记录与持久化
│   ├── context_service.py  # 当前工作空间上下文维护
│   ├── path_resolver.py    # 基于项目根目录的路径解析
│   ├── python_resolver.py  # 项目 Python 解释器解析
│   ├── metrics_collector.py # 请求级指标收集（token/耗时）
│   ├── interpreter_service.py # 终端解释器发现/选择/持久化
│   ├── pending_queue.py    # 双槽位等待队列（v3 兼容）
│   └── task_service.py     # 任务调度中心（v3 兼容）
├── workers/                # 后台线程（v3 兼容，v4 使用 v4/worker.py）
│   ├── __init__.py
│   ├── agent_worker.py     # 流式 Agent 推理 + 工具调用
│   ├── base_worker.py      # Worker 基类
│   ├── terminal_worker.py  # 终端命令输出捕获
│   ├── session_task.py     # 会话级任务状态
│   ├── task_capacity.py    # 资源容量控制
│   └── task_queue.py       # FIFO 任务排队
├── ui/                     # 界面层（v3 兼容，当前主界面已迁移至 v4/）
│   ├── __init__.py
│   ├── models/             # 数据模型
│   │   └── explorer_model.py   # 资源管理器数据模型
│   ├── widgets/            # 可复用组件（v3 兼容）
│   │   └── __init__.py
├── resources/              # 静态资源
│   └── themes/
│       └── dark_github.qss # GitHub Dark 主题
├── tests/                  # 单元测试 / 集成测试
│   ├── __init__.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── integration_test_deepseek_metrics.py
│   ├── test_v4_basics.py              # v4 数据模型 / 事件总线 / 仓库基础测试
│   ├── test_v4_gui_smoke.py           # v4 GUI 冒烟测试（主题切换、输入框、新任务按钮）
│   ├── test_v4_integration.py         # v4 MainWindow / Orchestrator / Worker 集成测试
│   ├── test_agent_worker.py
│   ├── test_agent_session_integration.py
│   ├── test_agent_session_room.py
│   ├── test_async_tools.py
│   ├── test_context_service.py
│   ├── test_event_bus.py
│   ├── test_explorer_model.py
│   ├── test_explorer_tree_model.py
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
1. 更新 CHANGELOG.md + PROJECT_BLUEPRINT.md + README.md + ARCHITECTURE.md + blueprints/ + docs/（全部项目文档）
2. git add -u && git add ARCHITECTURE.md blueprints/ docs/ README.md（覆盖已跟踪修改 + 新文档）
3. git commit -m "..." + git tag vX.Y.Z
4. git push + git push origin vX.Y.Z（仅当前分支 + 当前标签，禁止 --tags）

_更新于 2026-06-30 22:00:00 by AI-Trae_

## Agent交接记录
| 时间 | 方向 | 从 | 到 | 交接点 | 备注 |
|---|---|---|---|---|---|
| 2026-06-27T19:00 | 移交 | Kimi-K2.7-Code | — | v3.9.0 存档后 | 多任务管理系统+Session-as-Room+Trae暗黑主题已完成，全部单测通过，已推送 |

---
