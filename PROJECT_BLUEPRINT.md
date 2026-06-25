---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v0.3 | 存档次数 | 3 |

## 项目概要
AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Act），集成 LLM 推理、系统命令、量化分析、MT5 交易等能力。v3 完成生产级模块化重构。

## 技术栈
| 类别 | 技术 | 版本 | 用途 |
|---|---|---|---|
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
├── agent_engine/           # 引擎层：ModeManager, LLMRegistry, MemoryManager
├── tools/                  # 工具层：system, quant(akshare+backtrader), mt5, external_apis
│   ├── system.py           #   run_command, run_as_admin
│   ├── quant.py            #   fetch_stock_data, run_backtest
│   ├── mt5.py              #   mt5_get_price, mt5_place_order
│   └── external_apis.py    #   fetch_financial_news, fetch_macro_data
├── services/               # 服务层：配置(env→yaml)、对话持久化、主题管理
│   ├── config_service.py   #   统一配置 .env 优先 → config.yaml 回退
│   ├── session_service.py  #   SQLite 对话 + Token 用量持久化
│   └── theme_service.py    #   QSS 主题加载与切换
├── workers/                # 后台线程：流式 Agent 推理、终端命令
│   ├── agent_worker.py     #   流式输出 (astream) + 工具调用 + 敏感确认
│   └── terminal_worker.py  #   subprocess 管道输出捕获
├── ui/                     # 界面层：主窗口、聊天视图、组件库
│   ├── main_window.py      #   MainWindow 全局状态与信号协调
│   ├── chat_view.py        #   ChatView 流式气泡 + 模型下拉 + 快捷键
│   ├── widgets/            #   可复用组件
│   │   ├── sidebar.py      #     图标栏 + 文件树
│   │   ├── conversation.py #     对话列表（CRUD）
│   │   ├── tasks.py        #     任务面板（Checklist）
│   │   ├── terminal.py     #     终端控制台（含命令历史）
│   │   └── status_indicator.py # 状态栏（连接/模式/Token）
│   └── dialogs/            #   对话框
│       └── settings.py     #     模型提供商增删改
├── resources/              # 静态资源
│   └── themes/dark_github.qss  # GitHub Dark 主题
├── main.py                 # 程序入口（45行）
├── config.yaml             # 全局配置（API Key 在 .env）
├── .env.example            # 环境变量模板
├── AgentWorkbench.spec     # PyInstaller 打包配置
├── rebuild.ps1             # 一键打包脚本
├── CHANGELOG.md            # AI 维护的变更日志
└── PROJECT_BLUEPRINT.md    # 本文件
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v0.3 | 2026-06-25 | v2生产级重构：模块化架构、8工具、流式UI | feat/refactor | 全部模块 |
| v0.2 | 2026-06-25 | DeepSeek密钥修复与模型选择下拉功能 | feat/fix | config.yaml, llm_registry.py, main.py |
| v0.1 | 2026-06-24 | 初始提交AI工作台项目 | feat | main.py, config.yaml, agent_engine/, tools/ |

## 存档流程
1. 更新 CHANGELOG.md + PROJECT_BLUEPRINT.md
2. git add <源码> + CHANGELOG.md + PROJECT_BLUEPRINT.md
3. git commit + git tag vX.Y
4. git push + git push --tags

_更新于 2026-06-25 by AI-WorkBuddy_
---
