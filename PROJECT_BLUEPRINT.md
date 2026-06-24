---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v0.1 | 存档次数 | 1 |

## 技术栈
| 类别 | 技术 | 版本 | 用途 |
| 语言 | Python | 3.14 | 主语言 |
| UI 框架 | PySide6 | 6.21.0 | 桌面界面 |
| LLM 框架 | LangChain + langchain-openai | - | 工具调用与对话 |
| 本地模型 | Ollama (OpenAI compatible) | - | 本地 qwen3:4b 推理 |
| 打包工具 | PyInstaller | 6.21.0 | 生成 exe |
| 数据格式 | YAML / SQLite / JSON | - | 配置与记忆存储 |

## 目录结构
/
├── agent_engine/       # 模式管理、LLM 注册、记忆管理
├── tools/              # 系统命令、量化、MT5 等工具实现
├── ui/                 # UI 组件（当前由 main.py 统一维护）
├── storage/            # 运行时数据（SQLite / JSON / 向量存储）
├── tests/              # 测试目录
├── main.py             # 主程序入口
├── config.yaml         # 配置驱动文件
├── AgentWorkbench.spec # PyInstaller 打包配置
├── rebuild.ps1         # 一键重新打包脚本
├── requirements.txt    # Python 依赖
├── CHANGELOG.md        # AI 维护的变更日志
└── PROJECT_BLUEPRINT.md # 本文件

## 最近变更
| 版本 v0.1 | 日期 2026-06-24 | 描述 初始提交AI工作台项目 | 类型 feat | 文件 main.py, config.yaml, agent_engine/, tools/, rebuild.ps1 |

_更新于 2026-06-24 by AI-Kimi-K2.7-Code_
---
