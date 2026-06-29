# 5 分钟上手指南

## 前提条件

- **Python 3.11+**（推荐 3.13+）
- **Git**（可选，用于版本管理）
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

# 安装依赖
pip install -r requirements.txt
```

主要依赖：PySide6、LangChain、requests、yaml、pandas、numpy 等。

---

## 2. 配置 API Key

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env，填入你的 API Key
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
# DEEPSEEK_PRO_API_KEY=sk-xxxxxxxxxxxxxxxx
```

如果使用本地 Ollama，确保 Ollama 服务已启动（默认 `http://localhost:11434`），无需配置 API Key。

---

## 3. 启动

```bash
python main.py
```

首次启动会自动加载 `config.yaml` 配置，初始化 AppContext（全局状态容器）。

---

## 4. 三种模式

| 模式 | 用途 | 工具数 | Phase 流程 | 最大工具轮次 |
|------|------|--------|------------|-------------|
| **Ask** | 问答、信息查询、数据获取 | 11 | Analyze → Archive | 5 |
| **Plan** | 方案规划、策略设计 | 13 | Analyze → Confirm → Archive | 8 |
| **Craft** | 完整执行、命令运行、交易 | 17 | Analyze → Confirm → Execute → Verify → Archive | 12 |

- **Ask** 模式不能执行写文件、运行管理员命令、MT5 交易等危险操作
- **Plan** 模式比 Ask 多了 `run_backtest` 和 `write_file`
- **Craft** 模式拥有全部工具（含 MT5 交易、管理员命令、进程管理），在敏感操作前会请求确认
- 模式切换通过 UI 顶部的下拉菜单完成，切换后立即生效

---

## 5. 核心概念速览

### 项目目录
左侧资源管理器选择一个文件夹作为工作目录。Agent 能感知当前目录路径、打开的文件、选中的项目，工具中的相对路径基于此目录解析。

### 会话
每个对话是一个独立会话，支持按项目组织和纯对话两种类型。会话可新建、切换、删除，切换时不中断后台运行的任务。

### Phase 流程
每个任务经过固定的阶段流转。UIRenderer 订阅 Phase 事件自动刷新界面（进度条、状态标签、按钮状态）。

### 事件总线
v3 架构的核心。所有 UI 事件、Worker 结果、Phase 状态变更都经过 MessageBus 路由，按 `session_id` 隔离，保证多会话安全。

---

## 6. 运行测试

```bash
python -m pytest tests/ -v
```

全部 **209 个单元/集成测试** 通过。测试覆盖：
- 事件总线分发 / 过滤 / 多 handler
- SessionRuntime 生命周期
- SessionOrchestrator 事件路由
- PhaseCoordinator 流转控制
- UIRenderer 按 session_id 过滤
- TaskService 终态保护
- 集成测试：完整 Ask / Plan / Craft 流程

---

## 7. 打包

```bash
python rebuild.ps1
```

使用 PyInstaller 打包为独立可执行文件，产物在 `dist/AgentWorkbench/`，约 **17.6 MB**。

---

## 8. 常见问题

### Q: 启动报错 "ModuleNotFoundError: PySide6"
A: 确保已运行 `pip install -r requirements.txt`，且 Python 版本 ≥ 3.11。

### Q: DeepSeek API 返回 401 错误
A: 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确，是否有多余的引号或空格。

### Q: 切换会话后 UI 不更新
A: 检查 UIRenderer 是否正确订阅了当前 session 的事件。查看 `ui/managers/ui_renderer.py` 确认 `_active_session_id` 已更新。

---

## 下一步

- 了解系统架构：[ARCHITECTURE.md](../ARCHITECTURE.md)
- 查看设计决策历史：[blueprints/index.md](../blueprints/index.md)
- 完整目录结构：[PROJECT_BLUEPRINT.md](../PROJECT_BLUEPRINT.md)
- 版本变更记录：[CHANGELOG.md](../CHANGELOG.md)
