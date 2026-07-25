# Phase 3.12-A — Observation Tool Prototype Structure

> **Status**: STRUCTURE — v0.1
> **Date**: 2026-07-25
> **Phase**: 3.12-A.3
> **Depends on**: Phase 3.12-A.2 Observation Contract
> **Governance**: OD-G0-001 (Existing Capability First)

---

## 1. Purpose

定义 `tools/observation/` 目录原型与 Frozen Input Adapters 的边界。

**关键原则**：Observation Tool 不拥有 Runtime 生命周期，仅消费 Frozen Artifact。

---

## 2. 目录结构（Prototype v0.1）

```
tools/observation/
├── __init__.py                    # Tool 入口（导出 main entrypoints）
├── README.md                      # 本文档
├── adapters/                       # Frozen Input Adapter 层
│   ├── __init__.py
│   ├── runtime_event_adapter.py   # 消费 RuntimeEvent 流
│   ├── trace_adapter.py           # 消费 RuntimeTrace / TraceStep
│   ├── execution_metadata_adapter.py  # 消费 ExecutionMetadata
│   └── registry_snapshot_adapter.py   # 消费 ExecutionRegistry public API
├── derived/                        # Derived Metrics 算法（pure functions）
│   ├── __init__.py
│   ├── latency.py                 # Metric 1: execution.duration_ms
│   ├── cancellation_propagation.py   # Metric 2: cancel.propagation_ms
│   ├── deadline_accuracy.py       # Metric 3: deadline.error_ms
│   ├── event_throughput.py        # Metric 4: event.rate
│   └── registry_footprint.py      # Metric 5: registry.footprint
├── reports/                        # ObservationReport schema + serializer
│   ├── __init__.py
│   ├── observation_report.py      # ObservationReport dataclass
│   ├── footprint_snapshot.py      # FootprintSnapshot dataclass
│   └── serializer.py              # to_dict / to_json（仅作产物序列化）
└── collectors/                     # Evidence Collection orchestration
    ├── __init__.py
    └── evidence_collector.py      # 拼接 adapters → derived → report
```

---

## 3. Frozen Input Adapters 边界

### 3.1 共同约束

```python
# 共同 import 限制：
# - 可 import: v6.runtime.* (Frozen 数据类型)
# - 禁止 import: v6.runtime.* 中的 Orchestrator / EventBus.publish
# - 禁止: 写 Runtime 状态
# - 允许: 注册 EventBus 订阅者（read-only consumer）
```

每个 Adapter 必须：
- ✅ 仅 **import** `v6.runtime.*` 作为数据类型
- ✅ 仅调用 public methods
- 🚫 **禁止** import Orchestrator / EngineManager（避免反向依赖）
- 🚫 **禁止** 修改 EventBus / Registry 内部状态
- 🚫 **禁止** 启动 Runtime Worker 线程

### 3.2 边界依赖图

```
tools/observation/adapters/runtime_event_adapter.py
    ↓ (read-only)
v6/runtime/event_bus.py (Frozen: RuntimeEvent, RuntimeEventType)
```

禁止：
```
tools/observation/adapters/runtime_event_adapter.py
    ↓ (write)
v6/runtime/event_bus.py
```

---

## 4. Derived Metrics 算法（Pure Functions）

每个 derived 函数必须是 **pure**：
- 输入：Frozen 数据结构 / 列表
- 输出：Metric 数值（或 ObservationReport 字段）
- 无副作用
- 无 I/O（无文件、无网络、无 print）

这使得：
- 单元测试简单（无需 Runtime Fixture）
- 可被其他工具复用
- 可被 future Phase 3.13 持久化层直接调用

---

## 5. Observation Report 文件位置

```yaml
报告输出（运行时动态生成）:
  - 默认: stdout (JSON Lines)
  - 可选: 写入 tools/observation/output/ 目录（不是 Runtime 模块）

禁止:
  - v6/runtime/* 目录写入
  - Phase 3.12 不引入持久化（属 Phase 3.13+）
```

---

## 6. Evidence Collector 协调原则

```python
# pseudocode
class EvidenceCollector:
    def __init__(self):
        self.event_adapter = RuntimeEventAdapter()
        self.trace_adapter = TraceAdapter()
        self.metadata_adapter = ExecutionMetadataAdapter()
        self.registry_adapter = RegistrySnapshotAdapter()

    def collect_observation(
        self,
        execution_id: str,
        window: timedelta,
    ) -> ObservationReport:
        """Consume frozen artifacts → produce ObservationReport.

        不持有 Runtime 引用，不启动 Worker，不修改任何状态。
        """
        events = self.event_adapter.collect(execution_id, window)
        trace = self.trace_adapter.collect(execution_id)
        metadata = self.metadata_adapter.collect(execution_id)
        footprint = self.registry_adapter.collect_footprint()

        return ObservationReport(
            execution_id=execution_id,
            latency_ms=compute_latency(events),
            cancellation_delay_ms=compute_cancellation_delay(events),
            deadline_delta_ms=compute_deadline_delta(events, metadata),
            event_count=len(events),
            registry_footprint=footprint,
            observation_window_ms=window.total_seconds() * 1000,
        )
```

---

## 7. Validation Scenarios（Test 抽象）

按 Phase 3.11-D v0.3 Review 的 60/40 分层：

### 60% Primitive Tests（Pure Functions）

```python
# test_latency.py
def test_latency_normal_task():
    """TASK_STARTED 之后 100ms TASK_COMPLETED → 100ms latency."""

def test_latency_no_completion():
    """无 TASK_COMPLETED → 返回 None."""

def test_latency_multiple_terminal_events():
    """多个 terminal events → 取首个 terminal 计算."""
```

### 40% Integration Tests（Tool 端到端）

```python
# test_evidence_collector_e2e.py
def test_evidence_collector_with_fixtures():
    """使用 existing RuntimeEvents + Registry fixture → 完整 ObservationReport."""
```

---

## 8. Do Not Touch（继承 3.12-A.2）

| 禁止 | 原因 |
|------|------|
| `v6/runtime/*` | Frozen Contracts |
| 新增 Runtime Module | Runtime Kernel Stabilized |
| 修改 EventBus 增加 metrics | 通信 backbone 冻结 |
| 修改 Trace Schema | Trace Contract 已成熟 |
| 修改 CapabilityRegistry | v6.9.6 Frozen |
| Runtime Context ABI | Frozen |

---

## 9. Future Extension Boundary（Phase 3.13+）

Phase 3.12-A 不引入：

- 🚫 Persistence Layer（写入文件 / DB）
- 🚫 Monitoring Engine（持续轮询）
- 🚫 Alerting / Anomaly Detection
- 🚫 Multi-task Aggregation

这些属于 Phase 3.13+ Performance Intelligence Layer。

---

## 10. Status

| 阶段 | 状态 |
|------|------|
| 3.12-A.1 Design | ✅ APPROVED |
| 3.12-A.2 Observation Contract | 🟡 Pending Review |
| 3.12-A.3 Evidence Collection（本文） | 🟡 Pending Review |
| 3.12-A.4 Derived Metrics 算法 | ⏳ Pending |
| 3.12-A.5 Validation Report | ⏳ Pending |