# AI Agent Workbench

> 基于 PySide6 的桌面端 AI 助手，支持 Ask / Plan / Craft 三种手动模式，
> 集成 LLM 推理、系统命令、量化分析、MT5 交易、网页抓取及剪贴板管理。

## 技术栈

`Python 3.11+` `PySide6 6.21` `LangChain` `DeepSeek V4` `Ollama` `SQLite` `YAML` `PyInstaller`

---

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key（需要 .env 文件，含 DEEPSEEK_API_KEY 和 DEEPSEEK_PRO_API_KEY）
cp .env.example .env

# 启动应用
python main.py
```

## 运行测试

```bash
python -m pytest tests/ -v
```

目前全部 **209 个单元/集成测试** 通过。

---

## 文件地图

| 文件 / 目录 | 用途 | 优先级 |
|---|---|---|
| `main.py` | 程序入口，全局异常钩子，AppContext 初始化 | ★★★★★ |
| `config.yaml` | 全局配置：模式、模型、工具、记忆、终端、UI | ★★★★★ |
| `core/` | 事件总线 (MessageBus) + 强类型事件定义 | ★★★★★ |
| `services/` | 服务层：会话、配置、主题、上下文、任务、解释器 | ★★★★ |
| `agent_engine/` | 引擎层：编排器、Phase 管理、意图分类、记忆管理 | ★★★★ |
| `workers/` | 后台线程：Agent 推理、终端捕获、验证、任务调度 | ★★★★ |
| `ui/` | PySide6 界面层：主窗口、对话框、组件、事件驱动管理器 | ★★★★ |
| `ui/managers/` | v3 事件驱动管理器：UIRenderer、PhaseCoordinator、QueueManager、WorkerManager | ★★★★ |
| `tools/` | 工具层：系统命令、量化分析、MT5 交易、外部 API | ★★★ |
| `tests/` | 209 个单元/集成测试 | ★★★ |
| `resources/themes/` | QSS 暗黑主题（Trae Dark / GitHub Dark） | ★★ |
| `ARCHITECTURE.md` | 架构概览（Mermaid 组件图 + 核心概念 + 设计决策） | ★★★ |
| `blueprints/index.md` | 蓝图索引入口（设计决策历史） | ★★ |
| `docs/getting-started.md` | 5 分钟上手指南 | ★★ |
| `CHANGELOG.md` | 版本变更日志（v0.1 → v3.11.0） | ★★ |
| `PROJECT_BLUEPRINT.md` | 项目蓝图（完整目录树、技术栈、变更记录） | ★★★ |

---

## 当前状态

| 指标 | 详情 |
|---|---|
| 版本 | v3.11.0 |
| 测试 | 209/209 通过 |
| 架构 | 事件总线 + SessionRuntime + SessionOrchestrator |
| 打包 | PyInstaller 单文件 ≈ 17.6 MB |

---

## 导航

| 想了解... | 看这里 |
|---|---|
| 系统架构 | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 设计决策历史 | [blueprints/index.md](./blueprints/index.md) |
| 5 分钟上手 | [docs/getting-started.md](./docs/getting-started.md) |
| 完整目录结构 | [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) |
| 版本变更 | [CHANGELOG.md](./CHANGELOG.md) |

---

## AI 认知加载路径

任何 AI 进入本工作区后，建议按以下顺序阅读：

```
1. README.md           (1-2 分钟) → 知道是什么、怎么跑
2. ARCHITECTURE.md     (3-5 分钟) → 理解系统全貌
3. blueprints/index.md (1 分钟)   → 找到相关设计文档
4. CHANGELOG.md        (1 分钟)   → 了解最近变更
5. 具体蓝图文件        (按需)     → 深入某个模块的设计
```

总计约 10 分钟，AI 即可达到"可以参与开发"的水平。
