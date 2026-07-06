# 工作空间上下文感知

> **状态**：✅ 已完成（v3.4）
> **日期**：2026-06-26
> **源文档**：.trae/documents/workspace_context_design.md

## 1. 问题背景

Agent 无法感知当前工作空间，导致：
- 用户问"我现在在哪个文件夹下对话"，Agent 回答的是 exe 运行目录
- 用户问"你能看到我打开的文件吗"，Agent 无法回答
- 相对路径指令解析到错误位置

## 2. 最终方案

### 2.1 核心架构

引入 **ContextService** 作为会话上下文的单一真相源，三条链路：

```
┌─────────────────────────────────────────────────┐
│  UI 事件                                        │
│  (目录切换 / 文件选中 / 文档打开)               │
│        │                                        │
│        ▼                                        │
│  ContextService ◄── 单一真相源 ──┐              │
│        │                         │              │
│  ┌─────┴─────┐                   │              │
│  ▼           ▼                   ▼              │
│ Agent      文件工具           ProjectService    │
│ Prompt     (路径解析)        (Root 检测)        │
└─────────────────────────────────────────────────┘
```

三条链路：

1. **收集链路**：UI 事件 → ContextService —— 目录切换、文件选中、文档打开
2. **注入链路**：ContextService → Agent Prompt —— 每次发消息前拼接上下文摘要
3. **解析链路**：ContextService → 文件工具 —— 相对路径基于 Project Root 解析为绝对路径

### 2.2 启动时 Project Root 检测

按以下优先级自动检测：

1. `config/config.yaml` 中 `ui.explorer.project_root`，且目录仍然存在
2. `SessionService` 最近有会话记录的目录
3. `ActivityService` 最近一条 `project_path` 非空的活动目录
4. 回退到应用根目录（保持当前行为）

检测逻辑封装在 `ProjectService.detect_current_project()`。

### 2.3 上下文注入格式

每次用户发消息前，在 user text 前附加结构化摘要：

```text
[当前工作环境]
项目目录: F:/Agent/.workbuddy
活动文件: memory/2026-06-25.md (7.6 KB)
活动文件摘要:
---
# 2026-06-25 工作总结
...
---
打开文件: memory/2026-06-25.md
选中项: memory/

[用户问题]
你能看到我打开的文件吗
```

Token 开销可控（摘要 500 字符 + 元数据）。

### 2.4 MVP 范围控制

- ✅ 上下文感知 + 工具路径解析 + 最近项目快速切换
- ❌ 不做 RAG / 向量索引（项目通常 < 1000 文件，直接读取即可）
- ❌ 不做全项目符号索引
- ❌ 右侧文档仅注入"路径 + 前 500 字符摘要"，不注入全文

## 3. 排除的替代方案

| 替代方案 | 排除原因 |
|---------|----------|
| RAG / 向量索引全文注入 | 小项目直接用文件工具读即可，维护成本远超收益 |
| 全量注入右侧文档全文 | Token 开销过大，Agent 仍应通过 `read_file` 主动读取 |
| 仅基于进程 cwd 解析路径 | 无法感知用户通过 UI 切换的目录 |

## 4. 影响范围

| 影响 | 范围 |
|---|---|
| 新增 | `services/context_service.py`、`services/path_resolver.py` |
| 修改 | `services/project_service.py`、`ui/widgets/sidebar.py`、`ui/widgets/document_editor.py`、`ui/widgets/workspace.py`、`ui/main_window.py`、`workers/agent_worker.py`、`agent_engine/orchestrator.py`、`tools/system.py`、`config/config.yaml` |
| 测试 | `tests/test_context_service.py` |
