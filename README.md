# AI Agent Workbench

> **当前活跃主线：V6（`v6-dev` 分支）**。V6 是从零重写的 Agent Runtime 平台，
> 采用 `RuntimeContext` 作为唯一公共协议，八大 Engine 空壳已完成 Runtime 骨架验证。
> V5 及更早版本已冻结归档，不再维护。
>
> 基于 PySide6 的桌面端 AI 助手，V6 目标为可嵌入、可追踪、可回放的 Agent OS Kernel。

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
python -m pytest tests/v6/ -v
```

当前 V6 全量测试 **130/130 通过**；V5 / V4 历史测试已归档，不再执行。

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
| `AgentWorkbenchV5.spec` | PyInstaller V5 打包配置 | ★★★★ |
| `core/event_bus.py` / `core/events.py` | 事件总线（MessageBus）+ 强类型事件 | ★★★★★ |
| `v6/` | **当前活跃主线**：纯 UI + UIController + Service + AgentRuntime + 八大 Engine | ★★★★★ |
| `v6/ui/` | V6 纯 UI 组件库（按 `ui-template v0.6-alpha` 设计稿实现） | ★★★★★ |
| `v6/runtime/` | AgentRuntime 核心：`RuntimeContext` / `EngineManager` / `RuntimeTrace` / 八大 Engine | ★★★★★ |
| `v6/services/` | V6 业务服务层：`ConfigService` / `SessionService` / `ChatService` | ★★★★ |
| `v5/` | V5 只读归档区（已冻结，不再维护） | ★ |
| `v4/` | V4 旧 UI 完整版归档区（只读，已停止维护） | ★ |
| `v4/legacy/` | v3/v4 历史 UI 组件、QSS 主题、旧 spec 归档 | ★ |
| `tests/v6/` | V6 单元 / 集成 / Runtime / UI 契约测试 | ★★★★ |
| `docs/v6/` | V6 架构 SPEC、蓝图、变更日志 | ★★★★ |
| `assets/app.ico` | 应用图标 | ★★ |
| `scripts/start.bat` | 一键启动脚本 | ★★ |
| `scripts/rebuild.ps1` | 打包 + 桌面快捷方式刷新 | ★★★ |
| `docs/ARCHITECTURE.md` | 架构全景（Mermaid 图 + 核心概念 + 设计决策） | ★★★ |
| `docs/CHANGELOG.md` | 版本变更日志 | ★★ |
| `docs/PROJECT_BLUEPRINT.md` | 项目蓝图（完整目录树 + 技术栈 + 存档记录） | ★★★ |
| `docs/getting-started.md` | 开发上手（模式 / Phase / 核心概念） | ★★ |
| `docs/archive/blueprints/index.md` | 历史蓝图索引入口 | ★★ |

---

## 当前状态

| 指标 | 详情 |
|---|---|
| 版本 | v6.5.8-alpha |
| 测试 | `pytest tests/v6/` 130/130 通过 |
| 架构 | **V6 全新主线**：`RuntimeContext` 唯一公共协议 + `EngineManager` + 八大 Engine 空壳 + `RuntimeTrace` Timeline |
| 打包 | 尚未针对 V6 重新配置；V5 打包配置 `AgentWorkbenchV5.spec` 仅用于归档 |
| 分支 | **v6-dev**（当前活跃主线）；`v5-dev` 已冻结归档 |
| 旧线路归档 | `v5/` 目录只读归档，`v5-dev` 分支冻结；`v4/` 及 `v4-refactor` 更早归档 |

---

## 导航

| 想了解... | 看这里 |
|---|---|
| 系统架构 | [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) |
| 设计决策历史 | [docs/archive/blueprints/index.md](./docs/archive/blueprints/index.md) |
| 开发上手 | [docs/getting-started.md](./docs/getting-started.md) |
| 完整目录结构 | [docs/PROJECT_BLUEPRINT.md](./docs/PROJECT_BLUEPRINT.md) |
| 版本变更 | [docs/CHANGELOG.md](./docs/CHANGELOG.md) |

---

## V6 主线声明

- **`v6-dev` 是当前唯一活跃开发分支**，所有新功能、重构、Runtime 演进均在此分支进行。
- **`v5-dev` 已冻结归档**：Step 4（`v6.5.8-alpha`）为 `v5-dev` 上最后一个 V6 相关提交，此后 V6 开发迁移至 `v6-dev`。
- **禁止在 `v5-dev`、`main`、`v4-refactor` 等旧分支上继续提交 V6 代码**，避免版本号、标签、架构文档混淆。
- V6 设计原则：`RuntimeContext` 是 Runtime 唯一公共协议；Adapter 属于 Application Layer；Engine 只接受 `ctx` 输入；所有状态收敛到 `RuntimeContext`。

## AI 进入本工作区须知

1. **不得盲目运行系统 Python 或 pip install** — 项目已有完整 venv，通过 `venv\Scripts\Activate.ps1` 激活后直接使用。
2. **V6 测试入口**：`pytest tests/v6/ -v`；V5 测试仅作归档参考，不再执行。
3. **V6 逻辑入口**：`v6/main_window.py` → `UIController` → `Service` → `AgentRuntime` → `EngineManager` → `Engines`。
4. **文档由存档流程统一维护**：README / CHANGELOG / PROJECT_BLUEPRINT / docs/v6/SPEC.md 均在「请存档」时由 AI 自动更新，禁止私自修改。
5. **认知加载路径**：README（1 分钟）→ `docs/v6/SPEC.md`（5 分钟）→ `docs/CHANGELOG.md`（1 分钟）→ `docs/PROJECT_BLUEPRINT.md`（2 分钟）。
