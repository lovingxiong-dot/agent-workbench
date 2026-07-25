# Phase 3.12-A — Runtime Observation & Performance Intelligence Foundation

> **Status**: DESIGN REVISED — APPROVED with calibration
> **Date**: 2026-07-25
> **Phase**: 3.12-A
> **Depends on**: Phase 3.11 Frozen Baseline ✅ + v6.9.6 Foundation Freeze ✅
> **Governance**: OD-G0-001 (Existing Capability First)
> **Supersedes**: v0.1 (Runtime Stabilization formulation — refocused to Observation)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Phase 3.12-A proposal（命名 Runtime Stabilization） |
| v0.2 | 2026-07-25 | Architecture Review calibration：重命名为 Runtime Observation & Performance Intelligence；明确 Derived Metrics Only；调整 Registry 指标为 Footprint Observation（仅观察，不扩展 Registry） |

---

## 1. Purpose

按 Architecture Review 决议，Phase 3.11 Frozen Execution Kernel 已经 **Stabilized**。Phase 3.12 准确定位：

```
Phase 3.12 Runtime Observation & Performance Intelligence Foundation

目标：
Kernel Frozen
    ↓
Observe Reality
    ↓
Build Optimization Evidence
    ↓
Future Ecosystem Evolution
```

不修改 Runtime Contract，仅建立 Observation 能力派生现有 Runtime 数据为 Optimization Evidence。

---

## 2. Design Goals

| 目标 | 优先级 | 来源 |
|------|--------|------|
| Execution latency metrics | P0 | Architecture Review Recommendation 1 |
| Cancellation propagation latency | P0 | Architecture Review Recommendation 2 |
| **Runtime Registry Footprint**（调整） | P1 | Architecture Review（仅观察 footprint，不扩展 Registry） |
| Deadline accuracy | P1 | Architecture Review Recommendation 4 |
| Runtime event throughput | P2 | Architecture Review Recommendation 5 |

### 2.1 Derived Metrics Only 原则（Architecture Review）

Phase 3.12-A 仅允许：

```
Existing Runtime Data
       ↓
Derived Observation
       ↓
Report
```

**禁止**：
- ❌ 新增 `MetricsCollector` / `PerformanceService` / `MonitoringEngine` 等 Runtime Component
- ❌ 修改 EventBus 增加 metrics 逻辑（EventBus 是 communication backbone，已冻结）
- ❌ 修改 Trace Schema 增加 `latency` / `duration` / `cost` 字段（Trace Contract 已成熟）
- ❌ 修改 CapabilityRegistry 增加 `metrics` / `history` / `performance` 字段（v6.9.6 已冻结）

Metric Layer / Monitoring Layer / Audit Protocol 属于 Phase 3.13+。

---

## 3. Frozen Boundary Reminder（不可触碰）

| 契约 | 状态 |
|------|------|
| RuntimeEvent schema | ✅ Frozen（Phase 3.11-E） |
| RuntimeState ABI | ✅ Frozen |
| Task Contract | ✅ Frozen |
| RuntimeContext 一级字段集合 | ✅ Frozen |
| TracePresentationModel | ✅ Frozen |
| Capability / Decision / UI / Provider | ✅ Frozen |
| ADR-013 / ADR-014 / ADR-015 | ✅ Accepted |

**修改任何 Frozen Contract 必须**：新 ADR 替代 + 重新 Freeze Validation。

---

## 4. 现有 Capability 清单（OD-G0-001 Discovery）

### 4.1 RuntimeEvent timestamp

```python
# 已有 Frozen 字段
class RuntimeEvent:
    timestamp: float = field(default_factory=time.time)
```

✅ 已支持 latency 计算（事件时间差 = latency）

### 4.2 RuntimeTrace / TraceStep

```python
class TraceStep:
    timestamp: float  # 已有
```

✅ 已支持 Execution step 级别的 timestamp。

### 4.3 CancellationPropagationContext.payload

```json
{
  "propagation_type": "user_request",
  "origin_execution_id": "exec-001",
  "chain": ["exec-001", "exec-002"],
  "reason": "user_request",
  "initiated_at": "2026-07-25T10:30:00+00:00"
}
```

✅ TASK_CANCELLED payload 已包含 `initiated_at`（ISO 8601 UTC），可计算 propagation latency。

### 4.4 ExecutionRegistry 内部状态

- `_nodes: Dict[str, ExecutionNode]` — 节点数量可观测
- `ExecutionNode.terminated_at` / `cleanup_eligible_at` — 终态时间可观测
- `get_descendants(execution_id)` — 拓扑深度可观测

✅ Memory profile 可基于现有结构。

### 4.5 Deadline 模型

- `ExecutionMetadata.deadline_at` — 绝对时间点
- `_start_deadline_timer` 触发 cancel 时间偏差可观测

✅ Deadline accuracy 可基于现有结构。

---

## 5. 不需要新 Contract 的指标采集策略

按 OD-G0-001：**不需要新抽象**。所有指标从现有数据派生。

### 5.1 Execution latency metrics

```python
# 来源：RuntimeEvent 流（不修改 contract）
def execution_latency(task_id: str) -> Optional[float]:
    started = first_event_time(task_id, RuntimeEventType.TASK_STARTED)
    completed = first_event_time(task_id, RuntimeEventType.TASK_COMPLETED)
    if started and completed:
        return completed - started
    return None
```

### 5.2 Cancellation propagation latency

```python
# 来源：TASK_CANCELLED payload（已有 initiated_at）
def cancel_propagation_latency(execution_id: str) -> Optional[float]:
    cancel_event = first_event(execution_id, RuntimeEventType.TASK_CANCELLED)
    if cancel_event:
        initiated_at = datetime.fromisoformat(cancel_event.payload["initiated_at"])
        return time.time() - initiated_at.timestamp()
    return None
```

### 5.3 Registry memory profile

```python
# 来源：ExecutionRegistry 内部状态（已有）
def registry_memory_profile(registry: ExecutionRegistry) -> dict:
    return {
        "active_nodes": len([n for n in registry._nodes.values() if n.terminated_at is None]),
        "terminal_nodes": len([n for n in registry._nodes.values() if n.terminated_at is not None]),
        "total_nodes": len(registry._nodes),
        "depth_distribution": ...,
    }
```

### 5.4 Deadline accuracy

```python
# 来源：cancel_with_propagation payload + context.deadline_at
def deadline_accuracy(task_id: str, ctx: RuntimeContext) -> Optional[float]:
    cancel_event = first_event(task_id, RuntimeEventType.TASK_CANCELLED)
    if cancel_event:
        return cancel_event.timestamp - ctx.execution.deadline_at.timestamp()
    return None
```

### 5.5 Runtime event throughput

```python
# 来源：EventBus 订阅频率
class EventBusMetrics:
    events_published: int
    subscribers_count: Dict[RuntimeEventType, int]
    # 通过现有 subscribe / publish 路径收集
```

---

## 6. 测试策略

按 Phase 3.11-D v0.3 Review 的 60/40 分层：

### 60% Primitive Tests（指标算法）

- `test_execution_latency_calculate`
- `test_cancel_propagation_latency_calculate`
- `test_registry_memory_profile_shape`
- `test_deadline_accuracy_calculate`
- `test_event_throughput_collect`

### 40% Integration Tests（Runtime 流）

- `test_end_to_end_task_lifecycle_latency`
- `test_cancel_propagation_chain_latency`
- `test_registry_growth_and_cleanup_balance`

---

## 7. Do Not Touch（继承 Phase 3.11-E 边界）

| 项 | 原因 |
|-----|------|
| RuntimeEvent schema | Frozen |
| RuntimeState ABI | Frozen |
| Task Contract | Frozen |
| RuntimeContext 一级字段集合 | Frozen |
| TracePresentationModel | Frozen |
| Capability / Decision / UI / Provider | Frozen |
| ExecutionMetadata schema（已 additive） | Frozen |
| ExecutionRegistry public API | Frozen |

---

## 8. 不在 Phase 3.12-A 范围

按 Review Recommendation："不建议立即增加 Runtime feature"。

❌ **不做**：
- 新增 Monitoring/Audit Protocol
- 新增 Performance Optimization
- 新增 Persistent Metrics Storage
- 新增 Production Deployment 流程

✅ **可做**：
- 现有数据派生指标采集
- 现有 Observation Document 体系（OD-* 文档）
- 不修改 contract 的 integration tests

---

## 9. Phase 3.12-A 拆解（按 Review 调整）

| 阶段 | 内容 | 状态 |
|------|------|------|
| **3.12-A.1** | Design Document（v0.2 Architecture Review Approved） | ✅ APPROVED |
| **3.12-A.2** | **Observation Contract Design**（下一步） | 🟡 Pending Review |
| **3.12-A.3** | Evidence Collection（被动消费 RuntimeEvent / RuntimeTrace） | ⏳ Pending |
| **3.12-A.4** | Derived Metrics（5 类指标实现） | ⏳ Pending |
| **3.12-A.5** | Validation Report | ⏳ Pending |

---

## 10. Review Gate（待 Architecture Review）

- [ ] 是否遵守 OD-G0-001（不创造空层）
- [ ] 是否触碰 Frozen Contract
- [ ] 是否复用现有 capability
- [ ] 测试分层 60/40 是否合理