# ADR-013 — Runtime Lifecycle Event Extension

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Supersedes**: None
> **Scope**: RuntimeEventType — TASK_CANCELLED 事件类型新增

---

## 1. Purpose

定义 `TASK_CANCELLED` 事件类型的 Protocol Extension 边界，作为 Phase 3.11 取消能力的正式 Protocol 记录。

---

## 2. Context

Phase 3.11 引入 Cancellation 能力。任务取消是一个需要 Presentation Layer 感知的生命周期事件，因此需要发布 RuntimeEvent。

当前 `RuntimeEventType` 枚举包含 `TASK_STARTED` / `TASK_COMPLETED` / `TASK_FAILED`，但缺少 `TASK_CANCELLED`。

### 约束

- `RuntimeEvent` dataclass schema **冻结**，不新增字段
- 不新增 `task.queued` / `task.streaming` 等内部状态事件（内部状态迁移仅通过 `RuntimeContext.lifecycle` / `RuntimeContext.activity` 暴露）
- `TASK_CANCELLED` 是唯一需要 Presentation Layer 感知的新增生命周期事件

---

## 3. Decision

### 3.1 新增事件类型

```python
# v6/runtime/event_bus.py — RuntimeEventType（additive only）
TASK_CANCELLED = "task.cancelled"
```

### 3.2 Payload 契约

```python
{
    "reason": str,       # 取消原因（"user_request" / "timeout after 30s" / "parent_cancelled"）
    "task_id": str,      # 与 RuntimeEvent.task_id 相同，冗余用于消费端便利
}
```

**禁止**：payload 中不包含 `execution_metadata`、`execution_id`、`parent_execution_id` 等 Execution 层字段。

### 3.3 发布时机

```
cancel(task_id)
     │
     ▼
control.cancel()
     │
     ▼
publish(TASK_CANCELLED, {"reason": reason})
     │
     ▼
lifecycle → CANCELLED
activity → IDLE
```

事件在状态迁移**之前**发布，确保 Presentation Layer 在状态变为 CANCELLED 前收到通知。

### 3.4 订阅方

| 订阅方 | 用途 |
|--------|------|
| Presentation Layer (EventAdapter) | 展示取消状态 |
| Trace Hook | 写入 RuntimeTrace（TASK_CANCELLED 映射到 TraceEvent.TASK_ERROR） |
| Orchestrator | 不订阅（Orchestrator 是发布者） |

### 3.5 Trace 映射

```python
_RUNTIME_EVENT_TO_TRACE[RuntimeEventType.TASK_CANCELLED] = TraceEvent.TASK_ERROR
```

TASK_CANCELLED 映射到 `TraceEvent.TASK_ERROR`（与 TASK_FAILED 相同），因为从 Trace 视角，取消和失败都是非正常终止。

---

## 4. Consequences

### Positive
- Presentation Layer 可感知取消事件，展示取消状态
- 事件 schema 零修改，符合 Frozen Contract 原则
- 仅新增 1 个事件类型，最小化 Protocol Extension

### Negative
- 引入新的生命周期事件类型，消费端需要处理（但 EventAdapter 已有 `_on_unknown_event` 兜底，不会崩溃）

### Risk
- 如果未来需要更多生命周期事件（如 `task.paused` / `task.resumed`），需要新 ADR 而非直接扩展现有枚举

---

## 5. References

- Phase 3.11-A Execution Identity Model Design v0.2
- `v6/runtime/event_bus.py` — RuntimeEventType / RuntimeEvent / EventBus
- `v6/runtime/enums.py` — TraceEvent / TRACE_EVENT_LEVEL
- ADR-012 — Runtime Execution Isolation Strategy (PROPOSAL)