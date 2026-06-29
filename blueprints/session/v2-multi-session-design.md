# v2 多会话管理系统设计

> **状态**：✅ 已完成（v3.9.0，已被 [v3 事件总线架构](./v3-event-bus-architecture.md) 取代）
> **日期**：2026-06-27
> **源文档**：.trae/documents/multi-session-rewrite-v2.md

## 1. 问题背景

MainWindow（约 1450 行）是 God Object，直接管理会话、队列、Worker、Phase 全部逻辑，累积 **8 个结构性缺陷**：

| # | 缺陷 | 根因 | 影响 |
|---|------|------|------|
| 1 | 信号级联无限窗口 | `add_conversation(active=True)` → `setCurrentItem` → `itemClicked` → `_switch_conversation` | 点击新增会话产生多余切换 |
| 2 | 排队任务被吞 | `_on_archive_required` 中 `on_archive_complete` 同步触发 `flow_finished`，返回后又调一次 | 队列 slot[1] 任务被错误清除 |
| 3 | 队列 UI 不更新 | `_on_queue_changed` 被 `_switching` 守卫拦截 | 状态条不显示双槽位 |
| 4 | 全局对话环境误判 | 切换全局会话时 `context_service.project_root` 未清除 | AI 误以为在项目目录中 |
| 5 | 输入框在队列满时被清空 | `_send` 中先清空再入队 | 用户输入丢失 |
| 6 | 回车卡死 | 信号槽同步重入 | UI 冻结 |
| 7 | Phase 错误残留 | 任务失败后状态未更新为终态 | 下次请求报 PHASE_BUSY |
| 8 | 接替上下文冗余 | 无活跃任务也显示接替 | 空白会话显示误导信息 |

**核心架构缺陷**：**切换会话 = 销毁 Worker**，切换时所有后台工作被中断、状态丢失、队列清空。

## 2. 最终方案

### 2.1 前后台分离架构

```
┌──────────────────────────────────────────────────────────┐
│                      MainWindow                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                  UI 层 (前台)                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │ 会话 A   │  │ 会话 B   │  │ 会话 C   │        │  │
│  │  │ (当前)   │  │ (切换中) │  │ (闲置)   │        │  │
│  │  └──────────┘  └──────────┘  └──────────┘        │  │
│  └────────────────────────────────────────────────────┘  │
│                            │                             │
│                            ▼                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │            SessionRegistry (后台)                  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  session_A: Worker(RUNNING) + Queue + Phase  │  │  │
│  │  │  session_B: Worker(PAUSED)  + Queue + Phase  │  │  │
│  │  │  session_C: Worker(STOPPED) + Queue + Phase  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 关键原则

| 原则 | 说明 |
|------|------|
| Worker 独立 | 每个会话拥有自己的 AgentWorker，生命周期独立于 UI |
| 队列隔离 | 每个会话拥有独立的 PendingQueue，互不干扰 |
| 状态持久化 | 切换会话时 Phase 状态保留在 SessionRegistry，恢复时直接续用 |
| 切换不解绑 | 切换会话仅断开 UI 信号，Worker 不停止（PAUSED 状态） |

### 2.3 5 个 Manager 类

| Manager | 职责 |
|---------|------|
| `SessionManager` | 管理会话列表、CRUD、激活/停用 |
| `QueueManager` | 双槽位队列状态机：IDLE → STREAMING → QUEUED_1 |
| `SessionRegistry` | 后台数据容器，持有所有会话的 Worker/Queue/Phase 状态 |
| `WorkerManager` | Worker 生命周期管理（RUNNING / PAUSED / STOPPED） |
| `PhaseCoordinator` | Phase 流程协调（Analyze → Confirm → Execute → Verify → Archive） |

### 2.4 状态机

```
会话生命周期：IDLE → SWITCHING → ACTIVE
队列生命周期：IDLE → STREAMING → QUEUED_1
Worker 状态：  RUNNING → PAUSED / STOPPED
```

### 2.5 切换行为对比

| 操作 | 旧行为 | 新行为 |
|------|--------|--------|
| 切换会话 | 停止 Worker → 清空队列 → 重建状态 | 断开 UI 信号 → Worker 继续（PAUSED）→ 切换显示 |
| 切回会话 | 重新加载 DB → 重建 Worker | 重新连接 UI 信号 → 恢复已有状态 |
| 队列 | 全局单例，切换时清空 | 每会话独立，切换不影响 |
| 任务执行 | 只能在前台会话执行 | 后台会话可继续执行 |

## 3. 排除的替代方案

- 继续在 MainWindow 打补丁 → 8 个缺陷已是补丁累积结果，需结构性重构
- 单线程非并发 → 无法满足后台会话继续执行的需求

## 4. 影响范围

| 影响 | 范围 |
|---|---|
| 新增 | `ui/managers/` 下 SessionManager、QueueManager、SessionRegistry、WorkerManager、PhaseCoordinator + 对应测试 |
| 重写 | `ui/main_window.py` 1450 行 → 约 400 行（仅保留 UI 构建） |
| 不变 | `services/`、`agent_engine/`、`workers/`、`tools/` |

## 5. 后续演变

v2 方案在 v3 中被事件总线架构取代：

| v2 | v3 |
|----|-----|
| SessionRegistry（数据容器） | SessionRuntime（完整聚合根） |
| Manager 间直接信号连接 | MessageBus 事件驱动 |
| Manager 间互相调用 | 全部事件驱动，无直接依赖 |
| Worker 基于实例 guard 保护 | 按 session_id 路由，天然隔离 |
