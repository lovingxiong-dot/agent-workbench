# Phase 3.12-A — Observation Contract Design

> **Status**: DESIGN — PENDING REVIEW
> **Date**: 2026-07-25
> **Phase**: 3.12-A.2
> **Depends on**: Phase 3.12-A.1 Design (APPROVED), Phase 3.11 Frozen Baseline, v6.9.6 Foundation Freeze
> **Governance**: OD-G0-001 (Existing Capability First)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Observation Contract Design |

---

## 1. Purpose

冻结 Phase 3.12-A 的 **Observation Contract** 边界：

- Input Sources（允许消费）
- Output Schema（ObservationReport）
- Derived Metrics 集合
- Do Not Touch 边界
- Future Extension Boundary

**关键原则**：Observaiton 仅消费，不修改，不增加 Runtime Contract。

---

## 2. Contract Layer 定位

```
┌─────────────────────────────────────────────┐
│ Contract Layer (Frozen)                      │
│   - RuntimeEvent / RuntimeState / Task       │
│   - RuntimeContext ABI                       │
│   - TracePresentationModel                   │
└─────────────────────────────────────────────┘
                    ↑
                    │ 消费（read-only）
                    │
┌─────────────────────────────────────────────┐
│ Observation Layer (Phase 3.12 NEW)          │
│   - ObservationReport                        │
│   - DerivedMetrics                            │
│   - FootprintSnapshot                         │
└─────────────────────────────────────────────┘
                    ↑
                    │ 消费
                    │
┌─────────────────────────────────────────────┐
│ Runtime Layer (Frozen)                       │
│   - ExecutionEvent stream                    │
│   - RuntimeTrace                             │
│   - ExecutionMetadata                        │
│   - ExecutionRegistry snapshot               │
└─────────────────────────────────────────────┘
```

**禁止**：Observation Layer 不向下写入 Runtime Layer，不向上修改 Contract Layer。

---

## 3. Input Sources（允许消费）

| Input | 来源位置 | Frozen 状态 |
|-------|---------|-----------|
| `RuntimeEvent` | `v6/runtime/event_bus.py:113` | ✅ Frozen |
| `RuntimeEvent.timestamp: float` | `v6/runtime/event_bus.py:132` | ✅ Frozen |
| `RuntimeEvent.payload: dict` | `v6/runtime/event_bus.py:127` | ✅ Frozen |
| `RuntimeEvent.type: RuntimeEventType` | `v6/runtime/event_bus.py:29` | ✅ Frozen |
| `RuntimeTrace` / `TraceStep` | `v6/runtime/trace.py:63/30` | ✅ Frozen |
| `TraceStep.timestamp: float` | `v6/runtime/trace.py:40` | ✅ Frozen |
| `ExecutionMetadata.deadline_at` | `v6/runtime/execution_metadata.py` | ✅ Frozen |
| `ExecutionMetadata.execution_id` | 同上 | ✅ Frozen |
| `ExecutionRegistry.has_node()` | `v6/runtime/execution_registry.py` | ✅ Frozen |
| `ExecutionRegistry.get()` | 同上 | ✅ Frozen |
| `ExecutionRegistry.get_descendants()` | 同上 | ✅ Frozen |
| `CancellationPropagationContext.initiated_at` | `v6/runtime/cancellation_propagation.py` | ✅ Frozen |

**所有 Input 都是 Frozen 数据，Observation 仅读取。**

---

## 4. Output Schema（Observation 内部，不进 Runtime Contract）

### 4.1 ObservationReport

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class ObservationReport:
    """Phase 3.12-A Observation 产物。

    注意：这是 Observation Layer 的内部产物，不是 Runtime Contract。
    可被 Observation 工具消费，但不应进入 v6/runtime/ 模块。
    """
    execution_id: str
    latency_ms: Optional[float]          # Metric 1
    event_count: int                     # 派生
    cancellation_delay_ms: Optional[float]  # Metric 2
    deadline_delta_ms: Optional[float]   # Metric 3
    registry_footprint: FootprintSnapshot  # Metric 5
    observation_window_ms: float         # 观察窗口
```

### 4.2 FootprintSnapshot

```python
@dataclass(frozen=True)
class FootprintSnapshot:
    """Registry 占用快照（仅观察，不修改 Registry）。"""
    entries: int                         # ExecutionRegistry._nodes 数量
    active_entries: int                  # 未 terminated 数量
    terminal_entries: int                # terminated 但未 cleanup 数量
    max_depth: int                       # 最深 Execution Tree 深度
    memory_estimate_bytes: int           # 通过 ExecutionNode 估算
```

### 4.3 DerivedMetrics Primitive 集合

```python
from enum import Enum

class MetricType(str, Enum):
    EXECUTION_LATENCY = "execution.duration_ms"
    CANCELLATION_PROPAGATION = "cancel.propagation_ms"
    DEADLINE_ERROR = "deadline.error_ms"
    EVENT_THROUGHPUT = "event.rate"
    REGISTRY_FOOTPRINT = "registry.footprint"

# Metric 派生规则（已经在 Phase 3.12-A.1 §5 定义）：
# 1. execution.duration_ms = completed.timestamp - started.timestamp
# 2. cancel.propagation_ms = cancelled.timestamp - initiated_at
# 3. deadline.error_ms = actual_finish.timestamp - deadline_at
# 4. event.rate = events_count / window_seconds
# 5. registry.footprint = FootprintSnapshot 派生
```

### 4.4 文件位置约束

```yaml
Observation Layer 文件位置:
  - docs/v6/observations/   ← 设计文档与 ObservationReport 模型
  - tools/observation/      ← 派生计算实现（如果以脚本形式）

禁止:
  - v6/runtime/             ← Runtime Contract 已冻结
  - v6/presentation/        ← Presentation Layer 已冻结
  - agent_workbench/runtime/ ← AgentWorkbench Contract 已冻结
```

---

## 5. Do Not Touch（继承 Phase 3.11-E + 新增 v6.9.6 边界）

### 5.1 Runtime 内部（继承 Phase 3.11-E）

| 文件/契约 | 状态 |
|-----------|------|
| `v6/runtime/event_bus.py` | 🔒 Frozen |
| `v6/runtime/enums.py` | 🔒 Frozen |
| `v6/runtime/orchestrator.py` | 🔒 Frozen |
| `v6/runtime/execution_metadata.py` | 🔒 Frozen（Phase 3.11-D v0.3） |
| `v6/runtime/execution_registry.py` | 🔒 Frozen（Phase 3.11-D v0.3） |
| `v6/runtime/cancellation_propagation.py` | 🔒 Frozen（Phase 3.11-D v0.3） |
| `RuntimeContext`（一级字段集合） | 🔒 Frozen |
| `Task schema` | 🔒 Frozen |
| `Trace schema` | 🔒 Frozen |
| `TracePresentationModel` | 🔒 Frozen |

### 5.2 v6.9.6 Foundation Freeze 新增（Review 指出）

| 契约 | 状态 | 禁止 |
|------|------|------|
| `CapabilityDefinition` | 🔒 Frozen v6.9.6 | 修改 |
| `CapabilityContext` | 🔒 Frozen v6.9.6 | 修改 |
| `CapabilityState` | 🔒 Frozen v6.9.6 | 修改 |
| `CapabilityRegistry` | 🔒 Frozen v6.9.6 | 增加 metrics / history / performance 字段 |

### 5.3 Runtime Component 新增禁令

🚫 **禁止新增**：
- `MetricsCollector`
- `PerformanceService`
- `MonitoringEngine`
- `ObservationRecorder`
- 任何 Runtime Component 携带 metrics 状态

理由：这些属于 Phase 3.13+ 的 Metric Layer / Monitoring Layer。

---

## 6. Architecture Risk Scan

| Risk | 评估 | Mitigation |
|------|------|-----------|
| R1 | 引入 MetricsManager 污染 Kernel | 🚫 禁止 |
| R2 | EventBus 增加 `metrics.increment()` | 🚫 禁止（EventBus 是 communication backbone） |
| R3 | Trace 增加 `latency` / `duration` / `cost` 字段 | 🚫 禁止（Trace Contract 已成熟） |
| R4 | CapabilityRegistry 增加 `metrics={}` 字段 | 🚫 禁止（v6.9.6 冻结） |
| R5 | Observation 持久化（写入文件/DB） | ⚠️ 推迟（属 Phase 3.13+） |

---

## 7. Do Not Touch Verification（入口合约）

Phase 3.12-A 实施前必须确认：

- [ ] 无 Runtime Contract 修改
- [ ] 无新增 Runtime Module 进 `v6/runtime/`
- [ ] 无 Event Schema 修改（RuntimeEvent / RuntimeEventType）
- [ ] 无 Trace Schema 修改（TraceStep / RuntimeTrace）
- [ ] 无 CapabilityRegistry 字段扩展
- [ ] Observation 仅消费现有数据

---

## 8. Evidence Collection（A.3 入口）

按 OD-G0-001，**不引入新 EventBus 订阅机制**。Evidence Collection 通过：

### 8.1 EventBus 现有订阅 API

```python
# 已有 API（不修改 EventBus）
bus.subscribe(RuntimeEventType.TASK_STARTED, callback)
bus.subscribe(RuntimeEventType.TASK_COMPLETED, callback)
# ...

# Observation 仅作为外部 subscriber 注册回调
# 在测试/integration 场景下通过 orchestrator.execution_registry / public API 收集
```

### 8.2 ExecutionRegistry Public Snapshot

```python
# 仅使用 public API
total = len([n for n in orch.execution_registry._nodes.values()])  # ⚠️ 内部访问
# 应该改用:
orch.execution_registry.has_node(eid)  # ✅ public
# 或添加 snapshot 方法？
```

**注意**：当前 ExecutionRegistry 缺少 `_nodes` snapshot 方法。Phase 3.12-A.3 实现时需评估是否需要**新增**一个 snapshot public API（如 `snapshot_active_entries() -> list[ExecutionNode]`）。

但 Registry snapshot 方法**仅查询**，不修改数据结构。如果符合：

- 不修改 `_nodes` 内部
- 不新增 metrics 字段
- 仅 expose 已有数据

则允许新增 snapshot public API。

---

## 9. Phase 3.12-A 拆分（按 Review 调整）

| 阶段 | 内容 | 状态 |
|------|------|------|
| **3.12-A.1** | Design Document | ✅ APPROVED |
| **3.12-A.2** | **Observation Contract（本文档）** | 🟡 Pending Review |
| **3.12-A.3** | Evidence Collection 设计（含 Registry snapshot API 评估） | ⏳ Pending |
| **3.12-A.4** | Derived Metrics 实现（5 类 Primitive） | ⏳ Pending |
| **3.12-A.5** | Validation Report | ⏳ Pending |

---

## 10. Review Gate

待 Architecture Review：

- [ ] Observation Contract 边界清晰
- [ ] Input Sources 全部 Frozen 数据
- [ ] Output 不进 Runtime Contract
- [ ] Do Not Touch 清单完整
- [ ] Future Extension Boundary 明确（Phase 3.13+）