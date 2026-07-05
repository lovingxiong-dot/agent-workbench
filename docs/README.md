# AI Agent Workbench

> 基于 PySide6 的桌面端 AI 助手，v5 新 UI 完整版 + Phase-Driven Workflow Engine，
> 三种手动模式（Ask / Plan / Craft），多会话运行时隔离，支持 LLM 推理、系统命令、文件操作、网页抓取、终端解释器及量化工具。

## 技术栈

`Python 3.14` `PySide6 6.21` `LangChain` `DeepSeek V4` `Ollama` `SQLite` `YAML` `PyInstaller`

---

## 工作区环境

- **项目根目录**：`F:\Agent\agent_workbench`
- **虚拟环境**：`venv/`（已有完整依赖，通过 `scripts\start.bat` 或手动 `venv\Scripts\Activate.ps1` 激活）
- **配置入口**：`config/config.yaml`（模式 / 模型 / 工具 / 记忆 / UI）

### 首次安装（从 Git 克隆后）

```bash
cd F:\Agent\agent_workbench
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp config/.env.example config/.env
# 编辑 config/.env，填入 DEEPSEEK_API_KEY 和 DEEPSEEK_PRO_API_KEY
```

### 日常启动

```bash
cd F:\Agent\agent_workbench
venv\Scripts\Activate.ps1
python main.py
```

或直接双击 `scripts\start.bat`。

---

## 运行测试

```bash
venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

全部 **225 个单元 / 集成 / UI 测试** 通过。

---

## 打包部署

```powershell
.\scripts\rebuild.ps1
```

脚本自动：激活 venv → 清理旧构建 → PyInstaller 打包 → 刷新桌面快捷方式。
产物：`dist\AgentWorkbench\AgentWorkbench.exe`（≈ 17.9 MB，单目录模式）。

---

## 文件地图

| 文件 / 目录 | 用途 | 优先级 |
|---|---|---|
| `main.py` | 程序入口 | ★★★★★ |
| `config/config.yaml` | 全局配置（打包后可写副本位于 exe 同级 `config/`） | ★★★★★ |
| `AgentWorkbench.spec` | PyInstaller 打包配置 | ★★★★ |
| `core/event_bus.py` / `core/events.py` | 事件总线（MessageBus）+ 强类型事件 | ★★★★★ |
| `v4/` | v5 新 UI 核心：基于 `v4/widgets/` 的模块化主窗口 / Worker / Orchestrator / UI 渲染 | ★★★★★ |
| `v4/widgets/` | 新 UI 控件库：左栏 / 聊天区 / 输入区 / 右栏 / 设置对话框等 | ★★★★★ |
| `v4/legacy/` | 旧 UI 组件备份（已停止维护） | ★ |
| `services/` | 配置服务 / 持久化 / 活动记录 / 主题 / 解释器 | ★★★★ |
| `agent_engine/` | 编排器 / Phase 管理 / 记忆管理 / 八引擎（engines/） | ★★★★ |
| `workers/` | 后台线程：Agent 推理 / 终端捕获 / 验证 | ★★★★ |
| `tools/` | 工具层：系统命令 / 量化分析 / Web / MT5 / 屏幕 | ★★★ |
| `tests/` | 225 个单元 / 集成 / UI 测试 | ★★★ |
| `resources/themes/` | QSS 主题（GitHub Dark / Trae Dark） | ★★ |
| `assets/app.ico` | 应用图标 | ★★ |
| `scripts/start.bat` | 一键启动脚本 | ★★ |
| `scripts/rebuild.ps1` | 打包 + 桌面快捷方式刷新 | ★★★ |
| `docs/ARCHITECTURE.md` | 架构全景（Mermaid 图 + 核心概念 + 设计决策） | ★★★ |
| `docs/CHANGELOG.md` | 版本变更日志 | ★★ |
| `docs/PROJECT_BLUEPRINT.md` | 项目蓝图（完整目录树 + 技术栈 + 存档记录） | ★★★ |
| `docs/getting-started.md` | 开发上手（模式 / Phase / 核心概念） | ★★ |
| `blueprints/index.md` | 蓝图索引入口 | ★★ |

---

## 当前状态

| 指标 | 详情 |
|---|---|
| 版本 | v5.0.9-alpha |
| 测试 | 225/225 通过 |
| 架构 | v5 新 UI 完整版：模块化 `v4/widgets/` + SessionOrchestrator + SessionRuntime + V4Worker + PhaseEngine + 八引擎 |
| 打包 | PyInstaller 单目录 ≈ 17.9 MB |
| 分支 | v5-dev |

---

## 导航

| 想了解... | 看这里 |
|---|---|
| 系统架构 | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 设计决策历史 | [../blueprints/index.md](../blueprints/index.md) |
| 开发上手 | [getting-started.md](./getting-started.md) |
| 完整目录结构 | [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) |
| 版本变更 | [CHANGELOG.md](./CHANGELOG.md) |

---

## AI 进入本工作区须知

1. **不得盲目运行系统 Python 或 pip install** — 项目已有完整 venv，通过 `venv\Scripts\Activate.ps1` 激活后直接使用。
2. **启动走标准入口**：`scripts\start.bat`（日常运行）或 `python main.py`（手动）。
3. **打包走 `scripts\rebuild.ps1`**：一键激活 venv → PyInstaller → 桌面快捷方式，产物路径为 `dist\AgentWorkbench\`。
4. **文档由存档流程统一维护**：README / ARCHITECTURE / CHANGELOG / PROJECT_BLUEPRINT / blueprints / docs 均在「请存档」时由 AI 自动更新，禁止私自修改。
5. **逻辑入口**：`main.py` → `AppContext` → `SessionOrchestrator`，UI 通过 `MainWindow` 转发事件到 MessageBus。
6. **认知加载路径**：README（1-2 分钟）→ ARCHITECTURE（3-5 分钟）→ blueprints/index（1 分钟）→ CHANGELOG（1 分钟），总计约 10 分钟即可参与开发。
