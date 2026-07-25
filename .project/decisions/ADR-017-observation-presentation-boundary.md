# ADR-017 — Observation Presentation & Consumption Boundary

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Scope**: Phase 3.13 — Observation Presentation & Consumption Layer
> **Depends on**: ADR-016 (Observation Layer Contract), Phase 3.11-E Frozen, v6.9.6 Foundation Freeze
> **Supersedes**: None

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial ADR-017: Observation Presentation & Consumption Layer |

---

## 1. Purpose

按 Architecture Review Recommendation：

> 不要直接定义成 "Performance Intelligence"
> 建议 Phase 3.13: Observation Presentation & Consumption Layer
> 解决：如何消费 Observation 数据（不是如何智能优化 Runtime）

本 ADR 冻结 Phase 3.13 的边界，确认为 **Consumption**（消费）而非 **Control**（控制）。

**核心原则**：Observation Presentation Layer = 镜子展示，不是智能大脑。

---

## 2. Context

Phase 3.12-B 已建立 Observation Foundation（ADR-016 Frozen），含：

- ObservationReport（frozen dataclass）
- 5 类 Pure Functions（latency / cancellation / deadline / throughput / footprint）
- EvidenceCollector（被动消费 Frozen Artifact）
- Boundary Compliance（9 个 forbidden imports）

下一阶段面临问题：

- 人类用户如何看到 Observation 数据？
- 是否引入 Dashboard / Chart？
- 是否引入 Agent 消费？
- 是否启动 Performance Intelligence？

**本 ADR 决策**：Phase 3.13 仅做 **消费（Consumption）**，不做 **优化（Optimization）**。

```
3.12: Generation
3.13: Presentation & Consumption (人类可见)
3.14: Agent Consumption (Agent 可见)
Future: Performance Intelligence (多消费者生态)
```

---

## 3. Decision

### Decision 1 — Phase 3.13 命名与定位

**规则**：Phase 3.13 正式名称为 **"Observation Presentation & Consumption Layer"**。

**不命名为** "Performance Intelligence"（避免范围膨胀）。

**目标**：让系统产生可见能力（Visible Capability）—— 人类可读、Agent 可读、Export 可读。

### Decision 2 — 包含（In-Scope）

| 类别 | 内容 |
|------|------|
| Presentation Adapter | `ObservationReport` → `ObservationViewModel` 转换 |
| ViewModel | RuntimeStatus / Performance / Resource / Lifecycle 四组视图数据 |
| Runtime Observation Panel | Read-only UI 集成（v6/presentation/observation/） |
| Export | JSON / Markdown / Snapshot（file write） |
| Boundary Test | 继承 ADR-016 + Phase 3.13 新增 3 项 Re-Entry Trigger |

### Decision 3 — 排除（Out-of-Scope）

按 ADR-016 Decision 8 + 本 ADR 严格禁止：

| 排除项 | 原因 | 何时可加入 |
|--------|------|----------|
| Alert Engine | 属 Monitoring | Phase 3.14+ 需新 ADR |
| Auto Optimization | 属 Control | Phase 3.14+ 需新 ADR |
| Runtime Feedback Loop | 属 Runtime Intelligence | Future ADR |
| Policy Adjustment | 属 Control | Phase 3.14+ 需新 ADR |
| Scheduler Tuning | 属 Runtime 演进 | 需新 ADR + Runtime Re-Validation |
| Persistent Storage Layer | 属 Phase 3.14+ | 需新 ADR |
| Dashboard / Chart | 属 Phase 3.14+ | 需新 ADR |
| Multi-Observation Aggregation | 属 Phase 3.14+ | 需新 ADR |

### Decision 4 — 位置约束

```
允许路径:
  - tools/presentation/        # Phase 3.13 主位置（ViewModel + Adapter + Export）
  - v6/presentation/observation/  # UI 集成点（NEW 子目录；adapters 消费 ViewModel）
  - tests/tools/presentation/  # 测试位置
  - docs/v6/phase3-13-*        # 设计与报告

禁止路径:
  - v6/runtime/*                # Runtime Kernel Frozen
  - v6/presentation/models.py   # Frozen（Phase 3.10）
  - v6/presentation/contracts/  # Frozen
  - agent_workbench/runtime/    # v6.9.6 Frozen
  - tools/observation/*         # Phase 3.12 Frozen ADR-016
```

**关键**：`v6/presentation/models.py` 是 Frozen；Phase 3.13 的 ViewModel 必须在 `tools/presentation/`，通过 `v6/presentation/adapters/` 集成到 UI。**不修改 v6/presentation/models.py**。

### Decision 5 — Forbidden Import 集合（继承 ADR-016）

```python
# Phase 3.13 静态 import 检查
FORBIDDEN = (
    # Runtime 写边界（继承 ADR-016）
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    "agent_workbench.runtime.capability",
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
)
```

### Decision 6 — ViewModel 不可变性

**规则**：所有 ViewModel 必须是 frozen dataclass。

```python
@dataclass(frozen=True)
class ObservationViewModel:
    execution_id: str
    task_id: str
    runtime_status: RuntimeStatusView
    performance: PerformanceView
    resource: ResourceView
    lifecycle: LifecycleView
    raw_report: dict
```

**禁止**：ViewModel 是 mutable 或带 setter。

### Decision 7 — Adapter 单向数据流

**规则**：Adapter 仅 `ObservationReport` → `ObservationViewModel` 单向转换。

```
ObservationReport (frozen, Phase 3.12)
        |
        | Adapter.read(report)
        v
ObservationViewModel (frozen, Phase 3.13)
        |
        v
Workbench UI / Export
```

**禁止**：
- Adapter 修改 ObservationReport
- Adapter 持有 Runtime 引用
- Adapter 启动 EventBus subscribe 写事件
- Adapter 调用 Runtime lifecycle 方法

### Decision 8 — Read-Only Panel 约束

**规则**：`v6/presentation/observation/runtime_observation_panel.py` 是 Read-only UI 组件。

**禁止**：
- Panel 注册 EventBus publish
- Panel 修改 Runtime 状态
- Panel 持有 Orchestrator / EngineManager 引用
- Panel 启动 Worker
- Panel 启动 Polling（属 Monitoring）

**允许**：
- Panel 消费 `ObservationViewModel`（frozen）
- Panel 渲染 Read-only display
- Panel 通过用户点击触发 Export（属 read-only data flow）

### Decision 9 — Export Schema Stability

**规则**：Export 遵守 ADR-016 Schema Stability Rule。

| 格式 | Schema Version | 兼容策略 |
|------|---------------|---------|
| JSON | `observation.v0.1` | 完整保留 schema |
| Markdown | `observation.v0.1` | 完整保留 schema |
| Snapshot | `observation.v0.1` | 完整保留 schema + 加密 metadata |

**禁止**：
- Export 修改 `observation.v0.1` schema
- Export 引入新字段不升级 version
- Export 删除字段不升级 major version

### Decision 10 — Phase 3.13 Re-Entry Triggers（继承 + 新增）

继承 ADR-016 8 项 + Phase 3.13 新增 6 项（3 + 3）：

**继承 ADR-016 8 项**：

| # | Trigger | 类型 |
|---|---------|------|
| 1 | `v6/runtime/*.py` 修改需求 | Runtime 修改 |
| 2 | RuntimeEvent / RuntimeState / Task schema 演进 | Contract 修改 |
| 3 | ExecutionRegistry 需要新增 API | 即使是 read-only |
| 4 | EventBus 需要新增 metrics 字段 | Schema 修改 |
| 5 | Trace 需要扩展字段 | Contract 修改 |
| 6 | CapabilityRegistry 需要演进 | v6.9.6 Frozen |
| 7 | Observation 启动 Runtime Worker | 越界 |
| 8 | Observation 拥有 Runtime 生命周期引用 | 越界 |

**Phase 3.13 新增 6 项**：

| # | Trigger | 类型 |
|---|---------|------|
| 9 | ViewModel 直接 import RuntimeEvent | 违反 Presentation 边界 |
| 10 | Panel subscribe EventBus | 违反 Read-only 约束 |
| 11 | Export 写入 Runtime Contract 字段 | 违反 Schema Stability |
| 12 | UI 直接访问 Runtime Artifact | 违反 Presentation 边界 |
| 13 | ViewModel 保存状态（mutable） | 违反 Read-only |
| 14 | Presentation 层计算 Metrics | 越界到 Derived Layer |

---

## 4. 跨 Phase 边界

```
Phase 3.12 (Frozen ADR-016)
Runtime Observation Foundation
    |
    | ObservationReport (frozen)
    v
Phase 3.13 (本文)
Observation Presentation & Consumption Layer
    |
    | ObservationViewModel (frozen)
    v
Phase 3.14 (Future)
Agent Runtime Insight Layer
    |
    | Agent-readable ViewModel
    v
Future (Multi-Consumer)
Performance Intelligence
```

**禁止跨 Phase 越界**：
- 3.13 不得做 3.14 的事（Agent 消费）
- 3.13 不得直接进入 3.14+
- 任何 Performance Intelligence 越界 → 新 ADR

---

## 5. 与现有 ADR 关系

| 现有 ADR | 与 ADR-017 关系 |
|---------|---------------|
| ADR-013 Runtime Lifecycle Event Extension | Phase 3.13 消费其 TASK_CANCELLED 事件 |
| ADR-014 Cancellation Precedence Rule | Phase 3.13 仅观察结果 |
| ADR-015 Parent-Child Execution Propagation v0.3 | Phase 3.13 消费其 CancellationPropagationContext |
| **ADR-016 Observation Layer Contract** | Phase 3.13 消费 ObservationReport |
| **ADR-017 Observation Presentation Boundary** | **NEW: Phase 3.13 边界冻结（本 ADR）** |

---

## 6. 未来扩展

按 Review Recommendation 路线：

- **Phase 3.14+**: Agent Runtime Insight Layer（需新 ADR-018+）
- **Phase 3.14+**: Persistent Storage Layer（需新 ADR-018+）
- **Future**: Performance Intelligence（Multi-Consumer）—— 需新 ADR 流程

**未来 ADR 必须**：
- 不得违反 ADR-016 + ADR-017 边界
- 触发 Re-Entry Trigger 时重新 Review
- Phase 3.13 当前 **不预创建** 任何上述模块

---

## 7. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | Boundary Strict | ✅ |
| Implementation Lead | Phase 3.13 Scope Defined | ✅ |
| QA Lead | Plan 可执行 | ✅ |
| Boundary Guardian | Forbidden Import 集合完整 | ✅ |
| Frozen Contract Maintainer | Zero modification | ✅ |
| OD-G0-001 Maintainer | No Speculative Abstraction | ✅ |

---

## 8. References

- [Phase 3.13 Scope Definition](../../docs/v6/phase3-13-presentation-consumption-design.md)
- [Phase 3.12-B Completion Report](../../docs/v6/phase3-12-b-completion-report.md)
- [ADR-016 Observation Layer Contract](ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](../../docs/v6/phase3-11-e-freeze-validation-report.md)
- [OD-G0-001 Architecture Evolution Rule](../../.project/observations/OD-G0-001-architecture-evolution-rule.md)
- v6 Presentation Layer (Frozen)