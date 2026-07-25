# ADR-012 — Runtime Execution Isolation Strategy

> **Status**: PROPOSAL
> **Date**: 2026-07-25
> **Supersedes**: None
> **Scope**: Runtime Execution Layer — Orchestrator / TaskScheduler / ExecutionPool boundary

---

## 1. Purpose

定义从当前 `Orchestrator` 内联 `threading.Thread` 执行模型演进到独立 `TaskScheduler` + `ExecutionPool` 的长期策略。当前不实现，仅记录方向。

---

## 2. Context

Phase 3.10 修复了 EventBus Dispatch Loop 被同步 Task Execution 阻塞的 Blocking Callback Problem。修复方案为最小侵入：在 `Orchestrator._on_task_started()` 中使用 `threading.Thread(daemon=True)` 异步执行任务。

当前方案在 Single Runtime Process + Lightweight Execution Model 阶段是合理的，但长期不具备以下能力：

| 需求 | 当前 Thread 方案 | 未来 TaskScheduler |
|------|-----------------|-------------------|
| Task cancellation | 不支持 | 必须 |
| Task priority | 不支持 | 必须 |
| Resource quota | 不支持 | 必须 |
| Agent isolation | 不支持 | 必须 |
| Parallel workflow | 部分支持 | 必须 |
| Retry policy | 不支持 | 必须 |
| Execution trace | 隐式 | 显式 |

这些能力是 Multi-Agent、Workflow、Skill Chain、Agent OS 的基础。

---

## 3. Decision (Proposal)

### 3.1 当前架构（Phase 3.10）

```
Orchestrator
    |
    v
task.started callback
    |
    v
threading.Thread(daemon=True)
    |
    v
_execute_task()
    |
    v
EngineManager
```

### 3.2 目标架构（Future）

```
Orchestrator
    |
    v
TaskScheduler
    |
    v
ExecutionPool
    |
    v
Worker Runtime
    |
    v
EngineManager
```

### 3.3 新增组件

| Component | Responsibility |
|-----------|---------------|
| `TaskScheduler` | 任务队列管理、优先级排序、取消传播 |
| `ExecutionPool` | Worker 池管理、资源配额、并发控制 |
| `Worker Runtime` | 独立执行上下文、Agent 隔离、Trace 作用域 |
| `CancellationToken` | 取消信号传播、超时控制 |
| `ExecutionMetadata` | 执行元数据（retry_count、priority、quota、deadline） |

### 3.4 演进路径

1. **Phase 3.11**：Task Lifecycle State Machine 显式化（CREATED → PLANNING → EXECUTING → STREAMING → COMPLETED → FAILED → CANCELLED）
2. **Phase 4.x**：引入 `TaskScheduler`，替代直接 `threading.Thread` 调用
3. **Phase 5.x**：`ExecutionPool` + `Worker Runtime`，支持多 Agent 并发隔离

---

## 4. Consequences

### Positive
- 事件系统与执行系统彻底解耦
- 为 Multi-Agent / Workflow / Skill Chain 提供执行基础设施
- 取消、超时、重试等控制能力可统一实现

### Negative
- 增加运行时复杂度（Scheduler + Pool + Worker 三层）
- 当前 `threading.Thread` 方案在 Single Runtime 阶段足够，过早引入会扩大变更面

### Risk
- 如果 Phase 3.11 的 Task Lifecycle 状态机设计不充分，后续 TaskScheduler 需要重新设计状态转换

---

## 5. References

- Phase 3.10 Runtime Presentation Integration (Blocking Callback Problem fix)
- `v6/runtime/orchestrator.py` — `_on_task_started()` threading.Thread implementation
- `v6/runtime/event_bus.py` — Event notification separation
- `docs/v6/runtime-kernel-spec.md` — Frozen Runtime Kernel Contracts