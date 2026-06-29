# AI Agent Workbench

> 基于 PySide6 的桌面端 AI 助手，v3 事件总线架构 + Phase-Driven Workflow Engine，
> 三种手动模式（Ask / Plan / Craft），多会话运行时隔离，支持 LLM 推理、系统命令、文件操作、网页抓取、终端解释器及量化工具。

## 技术栈

`Python 3.14` `PySide6 6.21` `LangChain` `DeepSeek V4` `Ollama` `SQLite` `YAML` `PyInstaller`

---

## 工作区环境

- **项目根目录**：`F:\Agent\agent_workbench`
- **虚拟环境**：`venv/`（已有完整依赖，通过 `start.bat` 或手动 `venv\Scripts\Activate.ps1` 激活）
- **配置入口**：`config.yaml`（模式 / 模型 / 工具 / 记忆 / UI）

### 首次安装（从 Git 克隆后）

```bash
cd F:\Agent\agent_workbench
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 和 DEEPSEEK_PRO_API_KEY
```

### 日常启动

```bash
cd F:\Agent\agent_workbench
venv\Scripts\Activate.ps1
python main.py
```

或直接双击 `start.bat`。

---

## 运行测试

```bash
venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

全部 **209 个单元 / 集成测试** 通过。

---

## 打包部署

```powershell
.\rebuild.ps1
```

脚本自动：激活 venv → 清理旧构建 → PyInstaller 打包 → 刷新桌面快捷方式。
产物：`dist\AgentWorkbench\AgentWorkbench.exe`（≈ 17.6 MB）。

---

## 文件地图

| 文件 / 目录 | 用途 | 优先级 |
|---|---|---|
| `main.py` / `config.yaml` | 程序入口 + 全局配置 | ★★★★★ |
| `core/event_bus.py` / `core/events.py` | 事件总线（MessageBus）+ 强类型事件 | ★★★★★ |
| `services/session_orchestrator.py` | v3 统一协调器（唯一调度权威） | ★★★★★ |
| `services/session_runtime.py` | 会话运行时聚合根（每会话独立） | ★★★★★ |
| `services/task_service.py` | 任务调度中心（终态保护） | ★★★★ |
| `agent_engine/` | 编排器 / Phase 管理 / 意图分类 / 记忆管理 | ★★★★ |
| `workers/` | 后台线程：Agent 推理 / 终端捕获 / 验证 | ★★★★ |
| `ui/main_window.py` | 主窗口（绞杀者模式，新旧路径并存） | ★★★★ |
| `ui/managers/` | v3 事件驱动管理器（UIRenderer / PhaseCoordinator / WorkerManager / QueueManager） | ★★★★ |
| `ui/widgets/` | 视图组件（侧栏 / 对话 / 终端 / 工作区 / 编辑器 / 活动面板） | ★★★ |
| `tools/` | 工具层：系统命令 / 量化分析 / Web / MT5 / 屏幕 | ★★★ |
| `tests/` | 209 个单元 / 集成测试 | ★★★ |
| `resources/themes/` | QSS 主题（GitHub Dark / Trae Dark） | ★★ |
| `start.bat` | 一键启动脚本 | ★★ |
| `rebuild.ps1` | 打包 + 桌面快捷方式刷新 | ★★ |
| `ARCHITECTURE.md` | 架构全景（Mermaid 图 + 核心概念 + 设计决策） | ★★★ |
| `blueprints/index.md` | 蓝图索引入口 | ★★ |
| `docs/getting-started.md` | 开发上手（模式 / Phase / 核心概念） | ★★ |
| `CHANGELOG.md` | 版本变更日志（v0.1 → v3.11.1） | ★★ |
| `PROJECT_BLUEPRINT.md` | 项目蓝图（完整目录树 + 技术栈 + 存档记录） | ★★★ |

---

## 当前状态

| 指标 | 详情 |
|---|---|
| 版本 | v3.11.1 |
| 测试 | 209/209 通过 |
| 架构 | 事件总线 + SessionRuntime + SessionOrchestrator（v3） |
| 打包 | PyInstaller 单文件 ≈ 17.6 MB |
| 分支 | master |

---

## 导航

| 想了解... | 看这里 |
|---|---|
| 系统架构 | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 设计决策历史 | [blueprints/index.md](./blueprints/index.md) |
| 开发上手 | [docs/getting-started.md](./docs/getting-started.md) |
| 完整目录结构 | [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) |
| 版本变更 | [CHANGELOG.md](./CHANGELOG.md) |

---

## AI 进入本工作区须知

1. **不得盲目运行系统 Python 或 pip install** — 项目已有完整 venv，通过 `venv\Scripts\Activate.ps1` 激活后直接使用。
2. **启动走标准入口**：`start.bat`（日常运行）或 `python main.py`（手动）。
3. **打包走 `rebuild.ps1`**：一键激活 venv → PyInstaller → 桌面快捷方式，产物路径为 `dist\AgentWorkbench\`。
4. **文档由存档流程统一维护**：README / ARCHITECTURE / CHANGELOG / PROJECT_BLUEPRINT / blueprints / docs 均在「请存档」时由 AI 自动更新，禁止私自修改。
5. **逻辑入口**：`main.py` → `AppContext` → `SessionOrchestrator`，UI 通过 `MainWindow` 转发事件到 MessageBus。
6. **认知加载路径**：README（1-2 分钟）→ ARCHITECTURE（3-5 分钟）→ blueprints/index（1 分钟）→ CHANGELOG（1 分钟），总计约 10 分钟即可参与开发。
