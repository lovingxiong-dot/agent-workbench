# v3 事件总线架构重构

> **状态**：✅ 已完成（v3.11.0）
> **日期**：2026-06-29
> **源文档**：.trae/documents/v3-rewrite-plan.md
> **关联蓝图**：[v2 多会话管理](./v2-multi-session-design.md)（前身）→ v3 事件总线（当前）

## 1. 问题背景

v3 之前，系统存在 **6 个根因问题**：

| # | 问题 | 根因 |
|---|------|------|
| 1 | 状态权威分散 | MainWindow 直接维护 `_pending_queue`、`_worker`、`_workers`、`_phase_manager` |
| 2 | Task 状态可被外部直接写入 | `phase_coordinator.py:181`、`main_window.py:741` 写 `task.status` |
| 3 | Worker 信号串扰 | 路由基于 Worker 实例 guard，跨会话消息可能泄漏 |
| 4 | PhaseCoordinator 直接调用 UI | 持有 `chat_view` 引用，违反分层原则 |
| 5 | 任务完成路径不唯一 | 4 条路径各自更新 TaskService，状态不一致 |
| 6 | WorkerPool / WorkerManager 职责重叠 | 两处各自管理 Worker 生命周期 |

**症状**：会话切换时状态被覆盖、队列槽位不归零、任务状态不回收、Phase 重入错误。

## 2. 最终方案

### 2.1 核心分层

```
┌──────────────────────────────────────┐
│  UI 层 (MainWindow / UIRenderer)     │  表现层，订阅 ui.* 事件
├──────────────────────────────────────┤
│  MessageBus (事件总线)                │  唯一跨组件通信通道
│  namespace/name 订阅 + session_id    │
├──────────────────────────────────────┤
│  协调层                               │
│  SessionOrchestrator → SessionRuntime │  每会话独立聚合根
│  TaskService (终态保护)               │
│  WorkerManager (生命周期管理)         │
├──────────────────────────────────────┤
│  领域层                               │
│  AgentEngine · Workers · Services     │  业务逻辑与外部交互
└──────────────────────────────────────┘
```

### 2.2 四大核心原则

1. **单一权威**：每个概念只有一个地方负责。TaskService（任务状态）、SessionRuntime（会话运行时）、MessageBus（跨组件通信）、SessionOrchestrator（协调调度）、UIRenderer（UI 渲染）、WorkerManager（Worker 生命周期）
2. **事件驱动**：Manager 之间不互相调用，全部通过 MessageBus 通信
3. **会话隔离**：每个 SessionRuntime 独立持有 Queue、Phase、PendingQueue，切换不污染
4. **唯一完成路径**：所有任务结束均经过 `SessionOrchestrator._on_phase_flow_completed()`，无旁路

### 2.3 关键事件流（以 Ask 模式为例）

```
UserSendEvent → MessageBus
  → SessionOrchestrator.on_user_send()
    → SessionRuntime.enqueue()
      → PendingQueue.put()          # 入队
      → QueueStateChangedEvent      # UI 更新队列状态
      → TaskStartedEvent            # PhaseCoordinator 启动 Phase
        → WorkerManager 启动 Worker
          → AgentWorker 流式推理    # 逐 token 回调
            → StreamEvent × N       # UI 实时更新
          → AgentWorker 完成
          → TaskCompletedEvent      # TaskService 标记终态
          → PhaseFlowCompletedEvent # PhaseCoordinator 收尾
            → UIRenderer 刷新        # 状态栏、按钮恢复
```

### 2.4 关键文件

| 文件 | 最终职责 |
|---|---|
| `core/event_bus.py` | 基于 Qt Signal 的全局事件总线，namespace/name 精确订阅 |
| `core/events.py` | user/session/queue/phase/worker/task/ui 命名空间强类型事件 |
| `services/session_runtime.py` | 会话运行时聚合根，每会话独立持有 Queue/Phase/PendingQueue |
| `services/session_orchestrator.py` | v3 统一协调器，事件路由与任务状态机闭环 |
| `services/task_service.py` | 任务调度中心，终态保护（已在 terminal 状态的任务不可写） |
| `ui/managers/ui_renderer.py` | UI 事件统一渲染器，按 session_id 过滤 |
| `ui/managers/phase_coordinator.py` | PhaseManager 信号 → MessageBus 事件桥接 |
| `ui/managers/worker_manager.py` | Worker 生命周期事件驱动管理 |
| `ui/managers/queue_manager.py` | 双槽位队列状态机（会话级），IDLE / STREAMING / QUEUED_1 |
| `ui/managers/signal_adapter.py` | Worker 裸信号 → 强类型 MessageBus 事件转换 |
| `ui/main_window.py` | 绞杀者模式：新旧路径并存，新增 `_send_message_v3` 事件委托 |

## 3. 排除的替代方案

| 替代方案 | 排除原因 |
|---------|----------|
| 继续补丁式修复单一症状 | 每次修复引入新 bug，系统性问题需结构性解决 |
| 全局单例队列与 Worker 池 | 会话切换时互相污染，状态覆盖 |
| Qt Signal 直连 | 难以按 session_id 路由，跨线程边界模糊 |
| 一次性全量替换 MainWindow | 风险过高，缺乏回退路径 |

## 4. 影响范围

| 影响 | 范围 |
|---|---|
| 新增 | `core/event_bus.py`、`core/events.py`、`services/session_runtime.py`、`services/session_orchestrator.py`、`ui/managers/signal_adapter.py`、`ui/managers/ui_renderer.py` |
| 重写 | `ui/managers/phase_coordinator.py`、`ui/managers/worker_manager.py`、`ui/managers/queue_manager.py` |
| 瘦身 | `ui/main_window.py`（删除约 700 行业务逻辑，仅保留 UI 构建与事件转发） |
| 强化 | `services/task_service.py`（终态保护）、`services/pending_queue.py`（session_id 字段） |
| 测试 | `tests/integration/test_v3_flow.py` 及 6 个新增/更新测试文件，全部 209 通过 |
| 打包 | `AgentWorkbench.spec` 补齐 v3 新增模块 hiddenimports |

## 5. 当前状态与后续

- ✅ v3 架构骨架已完整落地，全部 209 测试通过
- ✅ PyInstaller 打包成功（dist/AgentWorkbench/AgentWorkbench.exe ≈ 17.6 MB）
- ⚠️ MainWindow 仍保留旧路径兼容层（绞杀者模式），下一步可考虑彻底迁移到 `_send_message_v3`
- ⚠️ WorkerManager 通过 MessageBus 订阅事件，但真实 LLM 调用链路未完全验证（集成测试使用 mock）
