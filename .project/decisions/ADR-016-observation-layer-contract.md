# ADR-016 — Observation Layer Contract & Boundary Freeze

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Scope**: Phase 3.12-B — Observation Foundation Freeze
> **Depends on**: Phase 3.11-E Frozen Baseline, v6.9.6 Foundation Freeze, ADR-013/014/015

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial ADR: Observation Layer Contract & Boundary Freeze |

---

## 1. Purpose

Phase 3.12-A Runtime Observation & Performance Intelligence Foundation 实现已完成（59 tests + 253 regression + Architecture Review Approved）。本 ADR 冻结 Observation Layer 的 5 项核心规则，防止 Phase 3.13+ 演进过程中 Observation 越界进入 Monitoring / Control / Runtime Intelligence Loop 领域。

**关键原则**：Observation 是 Runtime 的"镜子"，不是"器官"。

---

## 2. Context

Phase 3.12-A 完成 Observation Tool（`tools/observation/`）实现后，事实架构已形成：

```
tools/observation/
├── adapters/      (4 files)
├── derived/       (5 Pure Functions)
├── reports/       (ObservationReport / FootprintSnapshot)
└── collectors/    (EvidenceCollector)
```

**风险**：未来 Phase 3.13+ 自然延伸可能导致：

```
Observation
    |
    + Performance Dashboard
    |
    + Alert Engine
    |
    + Auto Optimizer
    |
    + Runtime Intelligence Loop
```

最终演变成 Monitoring Platform，违反 OD-G0-001（Existing Capability First）和 Phase 3.12-A 的定位。

本 ADR 通过冻结 5 项核心规则 + 8 项 Re-Entry Triggers，避免越界。

---

## 3. Decision

### Decision 1 — Observation Layer 位置

**规则**：Observation 工具与数据模型位于 `tools/observation/`。

```
允许路径:
  - tools/observation/        # Phase 3.12-A 主位置
  - tests/tools/observation/  # 测试位置
  - docs/v6/phase3-12-*       # 设计与报告

禁止路径:
  - v6/runtime/                # Runtime Kernel 已冻结
  - v6/presentation/           # Presentation 已冻结
  - agent_workbench/runtime/   # v6.9.6 Frozen
```

### Decision 2 — Forbidden Import 集合（9 个模块）

**规则**：`tools/observation/` 静态禁止 import 下列模块：

```python
REAL_FORBIDDEN = (
    # Runtime 写边界
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    # v6.9.6 Capability Frozen
    "agent_workbench.runtime.capability",
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
)
```

**验证**：`test_boundary_compliance.py` 静态 AST 扫描；CI 必须通过。

**允许的 Runtime 内部 import**（仅作为 read-only 数据类型）：
- `v6.runtime.event_bus`（RuntimeEvent / RuntimeEventType）
- `v6.runtime.execution_metadata`（ExecutionMetadata）
- `v6.runtime.execution_registry`（ExecutionRegistry public API）
- `v6.runtime.trace`（RuntimeTrace / TraceStep）

### Decision 3 — Pure Function Discipline

**规则**：`tools/observation/derived/*.py` 中所有函数必须满足：

| 约束 | 说明 |
|------|------|
| 输入 | 仅 Frozen 数据结构 + 参数 |
| 输出 | 数值（float）/ Snapshot（frozen dataclass）|
| 副作用 | 无 |
| I/O | 无文件 / 无网络 / 无 print |
| Logging | 不调用 RuntimeEventType.publish |
| Error Handling | 不抛异常；返回 None 或默认值 |

**派生函数列表**（Phase 3.12-A）：
- `execution_latency_ms`
- `cancellation_propagation_ms`
- `deadline_error_ms`
- `event_throughput`
- `registry_footprint`

### Decision 4 — Schema Stability Rule

**规则**：`ObservationReport` 序列化 schema 遵守 semver。

| 规则 | 操作 |
|------|------|
| minor version（v0.x → v0.x+1） | Additive Optional 字段 |
| major version（v0.x → v1.x） | 字段重命名或语义变化，必须新 ADR |

**当前 schema**：`observation.v0.1`

**Schema 演进触发条件**：
- 添加 Optional 字段 → minor 升级
- 删除字段 → major 升级 + 新 ADR
- 修改字段名 → major 升级 + 新 ADR
- 修改字段语义 → major 升级 + 新 ADR

### Decision 5 — Windowed Metric Rule

**规则**：Windowed metrics MUST filter events in window。

```
rate = events_in_window / window_seconds
```

**正确示例**：

```
events: [t=0, t=1, t=2]
window: [1.0, 2.0]
in_window: [t=1, t=2]  (2 events)
rate: 2 / 1.0 = 2.0 events/sec
```

**禁止示例**：

```
rate = all_events / requested_window   # 错误
```

**适用范围**：所有 `event.*` 类 metrics。`execution.*` / `cancel.*` / `deadline.*` 类 metric 不适用本规则（它们是 per-event metric）。

### Decision 6 — Adapter Boundary

**规则**：Adapters 仅消费 Frozen Artifact，不持有 Runtime lifecycle 引用。

```
Runtime (Frozen)
    |
    | produces
    v
Frozen Artifact (RuntimeEvent / Trace / Metadata / Registry snapshot)
    |
    | consumed by
    v
Observation Adapter
    |
    | produces
    v
List[RuntimeEvent] / RuntimeTrace snapshot / FootprintSnapshot
```

**禁止**：
- Adapter 持有 `Orchestrator` 引用
- Adapter 调用 Runtime lifecycle 方法
- Adapter 注册 EventBus publish（仅 subscribe）

### Decision 7 — Collect Policy

**规则**：`EvidenceCollector` 不启动 Worker，不修改 Runtime 状态。

```
EvidenceCollector
    |
    +-- Read events (from capture)
    +-- Read trace (from RuntimeTrace)
    +-- Read metadata (from Registry.get)
    +-- Read footprint (from Registry.has_node)
    |
    v
ObservationReport (frozen)
```

**禁止**：
- Collector 启动 Runtime Worker
- Collector 持有 Orchestrator
- Collector 修改 EventBus._subscribers
- Collector 修改 ExecutionRegistry 内部

### Decision 8 — Re-Entry Triggers（8 项）

**规则**：若未来 Phase 3.13+ 触发以下任一情况，**立即暂停并重新 Architecture Review**：

| # | Trigger | 说明 |
|---|---------|------|
| 1 | `v6/runtime/*.py` 修改需求 | 任何 Runtime 模块修改 |
| 2 | RuntimeEvent / RuntimeState / Task schema 演进 | Contract 修改 |
| 3 | ExecutionRegistry 需要新增 API | 即使是 read-only |
| 4 | EventBus 需要新增 metrics 字段 | Schema 修改 |
| 5 | Trace 需要扩展字段 | Contract 修改 |
| 6 | CapabilityRegistry 需要演进 | v6.9.6 Frozen |
| 7 | Observation 启动 Runtime Worker | 越界 |
| 8 | Observation 拥有 Runtime 生命周期引用 | 越界 |

---

## 4. Boundary Discipline（OD-G0-001 治理原则）

Observation Layer 严格遵守 **OD-G0-001 Existing Capability First** 规则：

- ✅ 复用 RuntimeEvent / RuntimeTrace / ExecutionMetadata / ExecutionRegistry public API
- ❌ 禁止为未来需求提前创造空层（Metrics Layer / Monitoring Layer / Audit Protocol）
- ❌ 禁止 Speculative Abstraction

**禁止的演进方向**（Future Phases）：

| 方向 | 状态 |
|------|------|
| Observation + Performance Dashboard | 🚫 Phase 3.13+ Prohibited |
| Observation + Alert Engine | 🚫 Phase 3.13+ Prohibited |
| Observation + Auto Optimizer | 🚫 Phase 3.13+ Prohibited |
| Observation + Runtime Intelligence Loop | 🚫 Phase 3.13+ Prohibited |
| Observation + Adaptive Runtime Tuning | 🚫 Phase 3.13+ Prohibited |

---

## 5. 现有 ADR 关系

| 现有 ADR | 与 ADR-016 关系 |
|---------|---------------|
| ADR-013 Runtime Lifecycle Event Extension | Observation 消费其 TASK_CANCELLED 事件 |
| ADR-014 Cancellation Precedence Rule | Observation 仅观察结果，不参与 |
| ADR-015 Parent-Child Execution Propagation v0.3 | Observation 消费其 `CancellationPropagationContext.payload.initiated_at` |
| **ADR-016 Observation Layer Contract** | **冻结 Observation Layer 边界（本 ADR）** |

ADR-016 不重复 ADR-013/014/015 内容，仅补充 Observation 特定规则。

---

## 6. Future RFC（不阻塞当前）

按 Review Recommendation：

- **Future RFC-1**: Execution Persistence Layer（解决 crash recovery / resume）
- **Future RFC-2**: Centralized DeadlineScheduler（演进 timer-based）
- **Future RFC-3**: Performance Intelligence Layer（持久化 / 监控） — **不与 ADR-016 冲突**

**Phase 3.13+ 必须**：
- 启动新 ADR 流程（ADR-017+）
- 不得违反本 ADR Decision 1-8
- 触发 Re-Entry Trigger 时重新 Review

---

## 7. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | Boundary Strict | ✅ |
| Implementation Lead | Phase 3.12-A Approved | ✅ |
| QA Lead | 59 tests + 253 regression | ✅ |
| Boundary Guardian | 0 forbidden imports | ✅ |
| Frozen Contract Maintainer | Zero modification | ✅ |
| OD-G0-001 Maintainer | No Speculative Abstraction | ✅ |

---

## 8. References

- [Phase 3.12-A Implementation Report](../../docs/v6/phase3-12-a-implementation-report.md) (APPROVED)
- [Phase 3.12-B Freeze Review](../../docs/v6/phase3-12-b-observation-freeze-review.md)
- [Phase 3.12-A Design](../../docs/v6/phase3-12-a-runtime-observation-design.md)
- [Phase 3.11-E Freeze Validation Report](../../docs/v6/phase3-11-e-freeze-validation-report.md)
- [ADR-013 Runtime Lifecycle Event Extension](ADR-013-runtime-lifecycle-event-extension.md)
- [ADR-014 Cancellation Precedence Rule](ADR-014-cancellation-precedence-rule.md)
- [ADR-015 Parent-Child Execution Propagation v0.3](ADR-015-parent-child-execution-propagation.md)
- [OD-G0-001 Architecture Evolution Rule](../observations/OD-G0-001-architecture-evolution-rule.md)
- Tool: [tools/observation/README.md](../../tools/observation/README.md)
- Tests: [tests/tools/observation/](../../tests/tools/observation/)