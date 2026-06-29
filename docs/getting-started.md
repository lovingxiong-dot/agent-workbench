# 5 分钟上手指南

## 前提条件

- **Python 3.14**（项目实际运行版本）
- **Git**（用于版本管理）
- **DeepSeek API Key**（或本地 Ollama）

### API Key 获取

- DeepSeek V4：注册 [DeepSeek 开放平台](https://platform.deepseek.com) 获取 `DEEPSEEK_API_KEY`
- DeepSeek V4 Pro：适用于复杂任务的高级模型，需单独获取 `DEEPSEEK_PRO_API_KEY`
- Ollama（本地）：安装 [Ollama](https://ollama.com)，拉取所需模型（如 `ollama pull qwen2.5`）

---

## 1. 克隆与安装

```bash
git clone <repo-url>
cd agent_workbench

# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

主要依赖：PySide6、LangChain、aiohttp、requests、beautifulsoup4、tiktoken、pyinstaller 等。

> **注意**：不要在没有激活 venv 的情况下运行 pip install，会污染系统全局 Python。

---

## 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入：
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
# DEEPSEEK_PRO_API_KEY=sk-xxxxxxxxxxxxxxxx
```

使用本地 Ollama 则无需配置 API Key，确保 Ollama 服务已启动（默认 `http://localhost:11434`）即可。

---

## 3. 启动

```bash
# 进入项目目录并激活 venv
cd F:\Agent\agent_workbench
venv\Scripts\Activate.ps1

# 启动应用
python main.py
```

或直接双击根目录的 `start.bat`（已内置 cd + activate + 启动）。

首次启动自动加载 `config.yaml`，初始化 `AppContext`（全局服务容器），并探测可用的终端解释器。

---

## 4. 三种模式

| 模式 | 用途 | 工具数 | Phase 流程 | 最大工具轮次 |
|------|------|--------|------------|-------------|
| **Ask** | 问答、信息查询、数据获取 | 11 | Analyze → Archive | 5 |
| **Plan** | 方案规划、策略设计 | 13 | Analyze → Confirm → Archive | 8 |
| **Craft** | 完整执行、命令运行 | 17 | Analyze → Confirm → Execute → Verify → Archive | 12 |

- **Ask** 模式不包含写文件、管理员命令、进程管理等破坏性工具
- **Plan** 模式比 Ask 多了 `run_backtest` 和 `write_file`
- **Craft** 模式拥有全部工具，敏感操作（管理员命令、进程终止）在执行前请求二次确认
- 模式切换通过 UI 顶部下拉菜单完成，切换后立即生效

---

## 5. 核心概念速览

### 项目目录与工作空间
左侧资源管理器选择一个文件夹作为工作目录。Agent 通过 `ContextService` 感知：当前目录路径、打开的文件、选中的项目。工具中的相对路径基于此目录解析。

### 会话（Session）
每个对话是独立会话，支持按项目组织和纯对话两种类型。v3 架构下每个会话拥有独立的 `SessionRuntime`（含 PendingQueue / QueueManager / PhaseManager），切换时不中断后台运行的任务。

### Phase-Driven Workflow
每个请求按固定阶段流转：Analyze（分析意图）→ Confirm（确认方案）→ Execute（执行工具）→ Verify（验证结果）→ Archive（归档记录）。`UIRenderer` 订阅 Phase 事件自动刷新进度条、状态标签、按钮状态。

### 事件总线（MessageBus）
v3 架构核心。所有 UI 事件、Worker 结果、Phase 状态变更都经 `MessageBus` 路由，按 `session_id` 隔离，Qt.QueuedConnection 保证跨线程安全。

---

## 6. 运行测试

```bash
venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

全部 **209 个单元 / 集成测试** 通过。测试覆盖：
- 事件总线：分发 / 过滤 / 多 handler
- SessionRuntime：生命周期 / 聚合根
- SessionOrchestrator：事件路由 / 任务状态机
- PhaseCoordinator：流转控制 / 重入防护
- UIRenderer：按 session_id 过滤
- TaskService：终态保护
- 集成测试：完整 Ask / Plan / Craft 流程

---

## 7. 打包

```powershell
.\rebuild.ps1
```

脚本自动完成：激活 venv → 清理旧构建 → PyInstaller 打包 → 刷新桌面快捷方式。

- 产物：`dist\AgentWorkbench\AgentWorkbench.exe`
- 快捷方式：桌面「AI Agent Workbench.lnk」
- 大小：约 17.6 MB

---

## 8. 常见问题

### Q: 启动报错 "ModuleNotFoundError"
A: 确认已激活 venv 并运行 `pip install -r requirements.txt`。不要在系统全局 Python 环境下操作。

### Q: DeepSeek API 返回 401
A: 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确，是否有多余引号或空格。

### Q: 切换会话后 UI 不更新
A: 检查 `UIRenderer` 的 `_active_session_id` 是否已同步更新。查看 `ui/managers/ui_renderer.py`。

---

## 下一步

- 系统架构：[ARCHITECTURE.md](../ARCHITECTURE.md)
- 设计决策：[blueprints/index.md](../blueprints/index.md)
- 完整目录：[PROJECT_BLUEPRINT.md](../PROJECT_BLUEPRINT.md)
- 版本历史：[CHANGELOG.md](../CHANGELOG.md)
