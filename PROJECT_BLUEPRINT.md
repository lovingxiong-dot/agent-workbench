---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v3.3 | 存档次数 | 8 |

## 项目概要
AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、MT5 交易、网页抓取、剪贴板管理等能力。v3.1 完成右侧工作区重构；v3.2 引入项目目录上下文；v3.3 对文件预览、对话分栏、活动面板、文档编辑进行精细化打磨，并修复模型持久化等细节问题。

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
│   ├── llm_registry.py     # LLM 提供商注册与持久化
│   ├── memory_manager.py   # 会话记忆管理
│   ├── mode_manager.py     # 手动模式管理
│   ├── orchestrator.py     # 编排器
│   └── proactive_engine.py # 主动引擎
├── tools/                  # 工具层
│   ├── __init__.py
│   ├── system.py           # 系统命令 / 文件读写 / 网络 / 剪贴板 / 通知 / 进程
│   ├── quant.py            # 股票数据 + 回测
│   ├── mt5.py              # MT5 报价 + 下单
│   ├── external_apis.py    # 财经新闻 / 宏观数据
│   └── screen.py           # 屏幕相关工具
├── services/               # 服务层
│   ├── __init__.py
│   ├── config_service.py   # 配置读取与持久化
│   ├── session_service.py  # SQLite 对话 + Token 用量持久化
│   ├── theme_service.py    # QSS 主题加载
│   ├── project_service.py  # 项目目录与会话关联管理
│   └── activity_service.py # 结构化活动记录与持久化
├── workers/                # 后台线程
│   ├── __init__.py
│   ├── agent_worker.py     # 流式 Agent 推理 + 工具调用
│   ├── base_worker.py      # Worker 基类
│   └── terminal_worker.py  # 终端命令输出捕获
├── ui/                     # 界面层
│   ├── __init__.py
│   ├── main_window.py      # 主窗口全局状态与信号协调
│   ├── chat_view.py        # 聊天视图（简约气泡、模型下拉、快捷按钮）
│   ├── overlay.py          # 覆盖层组件
│   ├── settings.py         # 设置相关 UI
│   ├── tools_panel.py      # 工具面板
│   ├── widgets/            # 可复用组件
│   │   ├── __init__.py
│   │   ├── sidebar.py      # 图标栏 + 文件树
│   │   ├── conversation.py # 分栏对话列表（当前项目 / 全局）
│   │   ├── tasks.py        # 任务面板
│   │   ├── terminal.py     # 终端控制台
│   │   ├── status_indicator.py # 状态指示器
│   │   ├── workspace.py    # 右侧工作区（终端/活动/文档标签）
│   │   ├── document_editor.py  # 文档查看与编辑器
│   │   └── activity_panel.py   # 结构化活动面板
│   └── dialogs/            # 对话框
│       ├── __init__.py
│       └── settings.py     # 模型设置 / 规则设置
├── resources/              # 静态资源
│   └── themes/
│       └── dark_github.qss # GitHub Dark 主题
├── tests/                  # 单元测试
│   ├── __init__.py
│   └── test_agent_worker.py
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
├── CHANGELOG.md            # AI 维护的变更日志
└── PROJECT_BLUEPRINT.md    # 本文件
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v3.3 | 2026-06-25 | 精细化打磨：任意格式文件预览、对话/活动分栏、文档编辑快捷键、修复模型持久化与活动重复记录 | feat/fix | ui/widgets/document_editor.py, ui/widgets/conversation.py, ui/widgets/activity_panel.py, services/activity_service.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3.2 | 2026-06-25 | 项目目录与对话上下文：资源管理器切换/打开文件夹、按目录组织会话、目录下开启新对话 | feat/refactor | services/project_service.py, services/session_service.py, ui/widgets/sidebar.py, ui/widgets/conversation.py, ui/main_window.py, config.yaml, resources/themes/dark_github.qss |
| v3.1 | 2026-06-25 | 重建右侧工作区：终端/日志/文档标签页、左侧文件树联动文档编辑器、文本文件编辑模式 | feat/refactor | ui/widgets/workspace.py, ui/widgets/document_editor.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3 | 2026-06-25 | 工具分层编排、AI身份系统、17工具库、UI全栈修复 | feat/fix | agent_worker, config, main_window, tools/* |
| v0.3 | 2026-06-25 | v2生产级重构：模块化架构、8工具、流式UI | feat/refactor | 全部模块 |
| v0.2 | 2026-06-25 | DeepSeek密钥修复与模型选择下拉功能 | feat/fix | config.yaml, llm_registry.py, main.py |
| v0.1 | 2026-06-24 | 初始提交AI工作台项目 | feat | main.py, config.yaml, agent_engine/, tools/ |

## 存档流程
1. 更新 CHANGELOG.md + PROJECT_BLUEPRINT.md
2. git add <源码> + CHANGELOG.md + PROJECT_BLUEPRINT.md
3. git commit + git tag vX.Y
4. git push + git push --tags

_更新于 2026-06-25 21:50:36 by AI-Kimi-K2.7-Code_
---
