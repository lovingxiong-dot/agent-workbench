---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v5.0.19-alpha | 存档次数 | 19 |

## 项目概要
AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、网页抓取、剪贴板管理等能力。

v5-dev 为独立开发线路（与 v3/main、v4/v4-refactor 并行），目标是在保留核心基座（agent_engine 八引擎、v4 MessageBus 事件通道、WorkerManager 异步调度、SessionOrchestrator 会话编排）100% 稳定的前提下，将外层 UI 完整替换为新三栏 UI（ui_template 设计稿）。

v5.0.0-alpha 为 v5-dev 线路起点：从 v4-refactor 切出独立分支，将零业务逻辑的纯 UI 模板注入后端核心，完成 MainWindow 与 ConfigService、SessionRepository、MessageBus、八引擎、WorkerManager、SessionOrchestrator、UIRenderer 的初始化对接。

## 技术栈
| 类别 | 技术 | 版本 | 用途 |
| 语言 | Python | 3.14 | 主语言 |
| UI 框架 | PySide6 | 6.21.0 | 桌面界面 |
| LLM 框架 | LangChain + langchain-openai | latest | 工具调用与多模型对话 |
| 本地模型 | Ollama (OpenAI compatible) | latest | 本地推理 |
| 云端模型 | DeepSeek API | V4 | 云端推理 |
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
├── AgentWorkbench.spec     # PyInstaller 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore              # Git 忽略规则
│
├── config/                 # 配置分组
│   ├── config.yaml         # 全局配置
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
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── PROJECT_BLUEPRINT.md
│   └── getting-started.md
│
├── blueprints/             # 工程蓝图
│   └── index.md
│
├── agent_engine/           # 引擎层（核心基座，禁止改动）
│   ├── __init__.py
│   ├── agent_session.py
│   ├── llm_registry.py
│   ├── memory_manager.py
│   ├── orchestrator.py     # 绞杀者编排器
│   ├── phase_manager.py
│   └── engines/            # 八引擎模块
│       ├── __init__.py
│       ├── interfaces.py       # 8 引擎接口
│       ├── context_engine.py
│       ├── prompt_engine.py
│       ├── inference_engine.py
│       ├── tool_engine.py
│       ├── phase_engine.py
│       ├── memory_engine.py
│       ├── metrics_engine.py
│       └── policy_engine.py
│
├── tools/                  # 工具层
│   ├── __init__.py
│   ├── system.py
│   ├── quant.py
│   ├── mt5.py
│   ├── external_apis.py
│   └── screen.py
│
├── core/                   # v3 核心基础设施
│   ├── __init__.py
│   ├── event_bus.py
│   └── events.py
│
├── v4/                     # v4/v5 单轨事件总线架构
│   ├── __init__.py
│   ├── models.py
│   ├── event_bus.py        # MessageBus
│   ├── events.py           # v4/v5 事件协议
│   ├── repository.py       # SQLite 会话/消息仓库
│   ├── queue.py
│   ├── runtime.py
│   ├── worker.py           # V4Worker（asyncio ReAct）
│   ├── worker_manager.py   # Worker 并发管理
│   ├── orchestrator.py     # SessionOrchestrator
│   ├── ui_renderer.py      # UI 渲染器
│   ├── main_window.py      # v5 新 UI 外壳（门面：仅组合子系统 + 信号桥接）
│   ├── widgets/            # v5 UI 组件库（从 main_window.py 拆分）
│   │   ├── __init__.py
│   │   ├── base.py         # 主题、字体、辅助函数
│   │   ├── window_frame.py # AppleMenu、EdgeResizeWidget
│   │   ├── left_panel.py   # LeftPanel、SessionItem/Group、FunctionPage
│   │   ├── chat_items.py   # ChatItem 及 8 个子类
│   │   ├── chat_scene.py   # ChatScene
│   │   ├── chat_area.py    # ChatArea、HeaderBar、InputArea、MoreDropdown
│   │   ├── right_panel.py  # RightPanel、TabButton
│   │   ├── dropdown_selector.py  # 通用内嵌下拉选择器
│   │   └── settings_dialog.py    # 设置对话框
│   ├── legacy/             # v4 旧 UI 组件备份（v5-dev 线路保留，P10 后清理）
│   │   ├── main_window_legacy.py
│   │   ├── conversation_list.py
│   │   ├── input_area.py
│   │   ├── right_panel.py
│   │   ├── chat_scene.py
│   │   ├── chat_items.py
│   │   └── icons.py
│   └── tests/
│
├── services/               # 服务层
│   ├── __init__.py
│   ├── config_service.py
│   ├── session_service.py
│   ├── theme_service.py
│   ├── project_service.py
│   ├── activity_service.py
│   ├── context_service.py
│   ├── path_resolver.py
│   ├── python_resolver.py
│   ├── metrics_collector.py
│   ├── interpreter_service.py
│   ├── pending_queue.py
│   └── task_service.py
│
├── workers/                # v3 Worker（保留）
├── ui/                     # v3 界面层（保留）
├── resources/              # 静态资源
├── tests/                  # 测试分组
└── storage/                # 运行时数据（不提交）
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v5.0.9-alpha | 2026-07-06 | P10 清理旧 UI 与打包验证：删除 v4 根目录重复旧 UI 文件（已备份至 v4/legacy/），旧测试迁移到 legacy 导入；更新 AgentWorkbench.spec hiddenimports 为新 widgets 模块；PyInstaller 打包成功，exe 独立启动正常 | chore/build/test | AgentWorkbench.spec, v4/*.py, v4/legacy/right_panel.py, tests/test_v4_input_area.py, tests/test_v4_right_panel.py |
| v5.0.5-alpha | 2026-07-06 | P5 会话数据持久化与列表同步：启动恢复 `app.last_session_id`、会话切换/创建/删除时同步持久化、无效会话清理、左栏空状态显示 | feat/session-sync | v4/main_window.py, v4/widgets/left_panel.py, v4/repository.py, v4/models.py, tests/test_v4_integration.py |
| v5.0.3-alpha | 2026-07-06 | 按审查报告执行模块化骨架拆分：将 `v4/main_window.py` 拆分为 `v4/widgets/` 7 个模块，主窗口降至 357 行；修复 `_session_idx_map` 致命 Bug，统一使用 `LeftPanel._idx_to_sid` | refactor/modular | v4/main_window.py, v4/widgets/* |
| v5.0.2-alpha | 2026-07-06 | 完成 P3 UIRenderer 与新 UI 桥接：ChatArea 真实消息渲染/流式/确认条/阶段状态，LeftPanel 会话列表按项目分组刷新与 badge 更新，SessionGroup 右键动作信号修复 | feat/bridge/ui | v4/main_window.py, tests/test_v4_gui_smoke.py |
| v5.0.1-alpha | 2026-07-05 | 备份 v4 旧 UI 组件至 `v4/legacy/`，标记 v5-dev 独立线路；原始组件保留待 P10 清理 | chore/backup | v4/legacy/*, PROJECT_BLUEPRINT.md |

## 历史归档
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v5.0.8-alpha | 2026-07-06 | P8 完整功能回填：真实 GUI 冒烟测试修复 `chat_area.py` 缺失 `QPen` 导入导致的 `paintEvent` 崩溃；验证三栏加载、会话创建、ui 事件分发正常，全量 225/225 通过 | fix/ui/test | v4/widgets/chat_area.py |
| v5.0.7-alpha | 2026-07-06 | P7 右栏真实功能回填：集成 TerminalWidget / FileReaderWidget / BrowserWidget，实现最近文件列表、点击打开、项目路径同步终端工作目录；新增 13 个右栏组件测试，全量 225/225 通过 | feat/ui/test | v4/widgets/right_panel.py, v4/widgets/terminal_widget.py, v4/widgets/file_reader_widget.py, v4/widgets/browser_widget.py, v4/main_window.py, workers/terminal_worker.py, tests/test_v4_widgets_right_panel.py |
| v5.0.6-alpha | 2026-07-06 | P5/P6 完全整改：SettingsDialog 配置与 UI 同步修复，MainWindow 启动与设置应用时校验主题/模式/模型有效性并回退无效值，修复 GUI 冒烟测试状态隔离，补充旧 UI 主题兼容键，全量 212 个测试通过 | fix/robustness/test | v4/main_window.py, v4/widgets/base.py, tests/test_v4_integration.py, tests/test_v4_gui_smoke.py |
| v5.0.0-alpha | 2026-07-05 | v5-dev 线路起点：从 v4-refactor 切出独立分支；将新 UI 模板注入后端核心（ConfigService/SessionRepository/MessageBus/八引擎/WorkerManager/SessionOrchestrator/UIRenderer），保留核心基座不变 | feat/refactor | v4/main_window.py |
| v4.0.8-alpha | 2026-07-01 | v4 全量 UI 三位一体对齐 SVG 设计稿 | feat/refactor/test | v4/main_window.py, v4/input_area.py, v4/right_panel.py, v4/icons.py, v4/conversation_list.py, tests/test_v4_input_area.py |
| v4.0.7-alpha | 2026-07-01 | 标题栏三键 + execute 步骤条自动解析 | feat/docs/fix | v4/main_window.py, v4/ui_renderer.py, AgentWorkbench.spec, docs/ui/* |
| v4.0.6-alpha | 2026-07-01 | 补齐目录标准化遗漏 | fix/build | AgentWorkbench.spec, services/project_service.py |

## 存档流程
1. 更新 CHANGELOG.md + PROJECT_BLUEPRINT.md（根目录两个维护文件）。
2. `git add -u && git add CHANGELOG.md PROJECT_BLUEPRINT.md`
3. `git commit -m "..."` + `git tag vX.Y.Z`
4. `git push origin <当前分支>` + `git push origin vX.Y.Z`（禁 `--tags`）

_更新于 2026-07-06 by AI-Kimi-K2.7-Code_

## Agent 交接记录
| 时间 | 方向 | 从 | 到 | 交接点 | 备注 |
|---|---|---|---|---|---|
| 2026-07-05T00:00 | 起点 | — | Kimi-K2.7-Code | v5.0.0-alpha | v5-dev 独立线路启动，新 UI 外壳接入后端核心 |

---
