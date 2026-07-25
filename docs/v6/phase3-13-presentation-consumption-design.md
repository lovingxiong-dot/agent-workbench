# Phase 3.13 — Observation Presentation & Consumption Layer

> **Status**: DESIGN DRAFT v0.1
> **Date**: 2026-07-25
> **Phase**: 3.13
> **Depends on**: Phase 3.11-E Frozen, Phase 3.12-B Frozen (ADR-016)
> **Output**: ADR-017 (Observation Presentation Boundary)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Phase 3.13 Scope Definition |

---

## 1. Purpose

按 Architecture Review Recommendation：

> **不要定义为 "Performance Intelligence"**（易导致范围膨胀）
>
> **改为 "Observation Presentation & Consumption Layer"**（聚焦消费能力）

定位：
- 不是：智能优化 Runtime
- 而是：让系统产生可见能力（Visible Capability）
- 下一阶段方向：从"证明架构正确"转向"让系统产生可见能力"

---

## 2. Phase 3.13 目标

```
Goal: 建立 Observation 消费能力（不是控制）

包含:
1. Presentation Adapter (ObservationReport → ViewModel → UI)
2. Runtime Observation Panel (Read-only)
3. Export (JSON / Markdown / Snapshot)

排除 (ADR-016 守卫):
❌ Alert
❌ Auto Optimization
❌ Runtime Feedback Loop
❌ Policy Adjustment
❌ Scheduler Tuning
```

---

## 3. 演进路线

```
Phase 3.12
Runtime Observation Foundation (Frozen ADR-016)
        |
        v
Phase 3.13 ← 当前
Observation Presentation Layer
        |
        v
Phase 3.14
Agent Runtime Insight Layer
        |
        v
Future
Performance Intelligence
```

**关键判断**：

- 3.12 阶段：**生成** Observation
- 3.13 阶段：**消费** Observation（人可见）
- 3.14 阶段：**Agent 消费** Observation（Agent 可见）
- 未来：**Performance Intelligence**（多消费者生态）

---

## 4. Phase 3.13 Scope

### 4.1 包含（In-Scope）

#### A. Presentation Adapter

```python
# tools/presentation/observation_view_model.py

@dataclass
class ObservationViewModel:
    """Phase 3.13 Presentation 视图模型（不进 Runtime Contract）。

    输入: ObservationReport
    输出: UI 可消费的 ViewModel
    """
    execution_id: str
    task_id: str
    runtime_status: RuntimeStatusView    # active / completed / failed
    performance: PerformanceView          # duration / throughput
    resource: ResourceView                # registry footprint
    lifecycle: LifecycleView              # cancellation / deadline
    raw_report: dict                       # for export
```

#### B. Runtime Observation Panel

**Read-only Panel**（Workbench UI 集成）：

| Panel Section | 内容 | 数据源 |
|---------------|------|--------|
| Runtime Status | active / completed / failed | ObservationReport.data_sources + 事件流 |
| Performance | duration_ms / throughput | ObservationReport.metrics |
| Resource | registry footprint | ObservationReport.registry_footprint |
| Lifecycle | cancellation_delay_ms / deadline_error_ms | ObservationReport.metrics |

#### C. Export

| Format | 用途 |
|--------|------|
| JSON | 程序化消费 / Agent 分析 |
| Markdown | 人工阅读 / Debug |
| Snapshot | 持久化（属 Phase 3.13+，但 Phase 3.13 仅做 file write） |

### 4.2 排除（Out-of-Scope）

按 ADR-016 Decision 8 + 本阶段 Scope：

| 排除项 | 原因 |
|--------|------|
| ❌ Alert Engine | 属 Monitoring（ADR-016 禁止） |
| ❌ Auto Optimization | 属 Control（ADR-016 禁止） |
| ❌ Runtime Feedback Loop | 属 Runtime Intelligence（ADR-016 禁止） |
| ❌ Policy Adjustment | 属 Control（ADR-016 禁止） |
| ❌ Scheduler Tuning | 属 Runtime 演进（ADR-016 禁止） |
| ❌ Persistent Storage Layer | 属 Phase 3.14+ |
| ❌ Dashboard / Chart | 属 Phase 3.14+ |
| ❌ Multi-Observation Aggregation | 属 Phase 3.14+ |

### 4.3 跨 Phase 边界

- **Phase 3.12 → 3.13**: Observation 工具 → ViewModel 转换
- **Phase 3.13 → 3.14**: ViewModel → Agent 消费
- **Phase 3.14+**: 多消费者生态

---

## 5. Architecture Boundary Review

### 5.1 允许 import 集合（继承 ADR-016）

```python
# tools/presentation/__init__.py 允许：
ALLOWED_IMPORTS = {
    "tools.observation",          # Phase 3.12 消费
    "v6.presentation.contracts",  # Presentation 边界
    "v6.presentation.models",     # ViewModel 基类
    "v6.presentation.adapters",   # UI Adapter
}

# 禁止 import 集合（继承 ADR-016）
FORBIDDEN = (
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

### 5.2 不变量

| 不变量 | 验证 |
|--------|------|
| ViewModel 不可变 | `@dataclass(frozen=True)` |
| Adapter 不可修改 ObservationReport | input 是 read-only |
| UI 仅消费 ViewModel | 不直接读 RuntimeEvent |
| Export 序列化稳定 | `observation.v0.1` schema |

### 5.3 Re-Entry Triggers（继承 ADR-016 + 新增）

ADR-016 已包含 8 项 Re-Entry Triggers。Phase 3.13 新增：

| # | Trigger | 说明 |
|---|---------|------|
| 9 | ViewModel 需要直接 import RuntimeEvent | 违反 Presentation 边界 |
| 10 | Panel 需要 subscribe EventBus | 违反 Read-only 约束 |
| 11 | Export 写入 Runtime Contract 字段 | 违反 Schema Stability |

---

## 6. Execution Batch Plan（Agent 批量执行）

### 6.1 阶段拆分

```
Phase 3.13-A — Architecture Gate
├── A.1 Phase 3.13 Scope Definition (本文) 🟡 Pending Review
├── A.2 ADR-017 Proposal (Observation Presentation Boundary) 🟡 Next
├── A.3 UI Boundary Design 🟡 Next
└── A.4 Execution Batch Plan (本文) ✅

Phase 3.13-B — Execution Batch (Agent)
├── B.1 Presentation Adapter (ObservationViewModel)
├── B.2 Runtime Observation Panel (UI Component)
├── B.3 Export (JSON / Markdown / Snapshot)
├── B.4 Integration Tests + Boundary Compliance
└── B.5 Implementation Report

Phase 3.13-C — Architecture Review
├── C.1 Boundary Compliance Verification
├── C.2 ADR-017 Acceptance
└── C.3 Phase 3.13 Freeze Validation Report
```

### 6.2 文件位置

```
tools/
├── observation/        # Phase 3.12 (Frozen ADR-016)
└── presentation/       # Phase 3.13 (NEW)
    ├── __init__.py
    ├── observation_view_model.py
    ├── view_models/    # 子 ViewModel
    ├── adapters/       # Observation → ViewModel Adapter
    ├── exports/        # JSON / Markdown / Snapshot
    └── README.md

v6/presentation/       # 已有 (Frozen)
└── observation/       # NEW: UI 集成点（仅消费 ViewModel）
    ├── __init__.py
    ├── runtime_observation_panel.py
    └── README.md

tests/tools/presentation/  # NEW
├── test_view_model.py
├── test_export.py
├── test_panel.py
└── test_boundary_compliance.py

docs/v6/phase3-13-*
├── phase3-13-presentation-consumption-design.md (本文)
├── phase3-13-adr-017-proposal.md
├── phase3-13-ui-boundary-design.md
└── phase3-13-completion-report.md
```

### 6.3 测试分层（60% Primitive + 40% Integration）

| 类别 | 数量 | 状态 |
|------|------|------|
| ViewModel Primitive | 10+ | 计划 |
| Export Primitive | 5+ | 计划 |
| Panel UI Component | 5+ | 计划 |
| Integration Tests | 8+ | 计划 |
| Boundary Compliance | 4+ | 计划 |

---

## 7. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| ViewModel 反向依赖 Runtime | R0 | Static import check（继承 ADR-016） |
| Panel 启动 Runtime Worker | R0 | 不 subscribe 写事件 / 不持有 lifecycle |
| Export 改变 Schema | R0 | version tag + 继承 ADR-016 Schema Stability |
| UI 越界进入 Runtime | R0 | v6/presentation/observation/ 边界严格 |
| 范围膨胀到 Performance Intelligence | R1 | ADR-017 + Review Re-Entry Triggers |

---

## 8. Review Gate（待 Architecture Review）

- [ ] Phase 3.13 命名与定位正确
- [ ] Scope 严格遵守 ADR-016 5 项核心规则
- [ ] 不包含 Alert / Auto Optimization / Runtime Feedback Loop
- [ ] 跨 Phase 边界（3.12 → 3.13 → 3.14）正确
- [ ] Execution Batch Plan 可执行

---

## 9. References

- [Phase 3.12-B Completion Report](phase3-12-b-completion-report.md)
- [ADR-016 Observation Layer Contract](../../.project/decisions/ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)
- [OD-G0-001 Architecture Evolution Rule](../../.project/observations/OD-G0-001-architecture-evolution-rule.md)
- v6 Presentation Layer (Frozen)