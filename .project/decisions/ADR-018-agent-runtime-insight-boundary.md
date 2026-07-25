# ADR-018 — Agent Runtime Insight Boundary

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Scope**: Phase 3.14 — Agent Runtime Insight Boundary
> **Depends on**: ADR-016 (Observation Layer Contract), ADR-017 (Observation Presentation Boundary)
> **Supersedes**: None

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial ADR-018: Agent Runtime Insight Boundary |

---

## 1. Purpose

按 Phase 3.13 Completion Review Recommendation：

> 当前最大的价值是：Runtime 已经稳定，Observation 已经形成，下一阶段应该增加系统理解能力，而不是增加系统控制能力。

本 ADR 冻结 **Insight Layer Boundary**，确认为：
- **Insight = System Understanding（系统理解）**
- **Insight ≠ System Control（系统控制）**

**关键判断**：Runtime 不自修改。Insight 是 Read-only Consumer，不触发 Runtime Action。

---

## 2. Context

### 2.1 当前 Frozen 状态

- Phase 3.11 Frozen：Execution Kernel
- Phase 3.12 Frozen（ADR-016）：Observation Foundation
- Phase 3.13 Frozen（ADR-017）：Presentation & Consumption

### 2.2 下一阶段方向

按 Review 三方向选择：

| 方向 | 含义 | 风险 |
|------|------|------|
| A: Presentation Intelligence | UI 智能增强 | 易演变成 Dashboard Intelligence |
| B: Agent Cognitive Layer | Agent 输入 | **本 ADR 选择** |
| C: Runtime Governance Layer | Runtime 治理 | 易演变成 Monitoring Engine |

**本 ADR 决策**：B（Agent Cognitive Layer），**严格 Read-only**。

### 2.3 三大 Risk

1. Insight → Decision → Runtime Action（破坏 Runtime 不自修改）
2. Metric → Insight → Policy（演变成 Monitoring Engine）
3. Insight Ownership 模糊

本 ADR 显式禁止以上 Risk。

---

## 3. Decision

### Decision 1 — Phase 3.14 命名与定位

**规则**：Phase 3.14 正式名称为 **"Agent Runtime Insight Boundary"**。

**目标**：生成 Insight Artifact，提供给 Agent / Human / Workspace 消费。

**禁止**：Runtime Action / Decision / Alert / Policy / Scheduler Tuning。

### Decision 2 — Insight Ownership = Agent Cognitive Layer

**规则**：Insight 由 **Agent** 消费（Phase 3.15+），**Human** 通过 Phase 3.13 UI 间接消费，**Workspace** 未来 ADR 决定，**Runtime** **严禁消费**。

```
Insight Ownership:
  Agent       → Phase 3.15+ 消费 (Decision Support, ADR-019)
  Human       → Phase 3.13 UI 间接消费 (Panel/Export)
  Workspace   → Future ADR
  Runtime     → 🚫 严禁消费（破坏 Runtime 不自修改）
```

### Decision 3 — Insight 定义

**规则**：Insight 是 **frozen dataclass**，仅消费 Observation 数据，不触达 Runtime。

```python
@dataclass(frozen=True)
class InsightArtifact:
    """Phase 3.14 Insight 产物（Read-only）。"""
    insight_type: str
    insight_value: dict  # 派生分析结果
    source_observation: dict  # 引用源 ObservationViewModel 快照
    derived_at: float
    schema_version: str = "insight.v0.1"
```

**禁止**：
- Insight 是 mutable 或带 setter
- Insight 引用 Orchestrator / EngineManager / PlannerLoop
- Insight 修改 ObservationReport / ObservationViewModel

### Decision 4 — Insight 派生单向数据流

**规则**：Adapter 仅 `Observation → Insight` 单向转换。

```
ObservationReport (Phase 3.12 Frozen)
        |
ObservationViewModel (Phase 3.13 Frozen)
        |
        | InsightAdapter.read(view_model)
        v
InsightArtifact (Phase 3.14 frozen)
        |
        v
Agent / Human / Workspace (Future)
```

**禁止**：
- Adapter 反向修改 Observation
- Adapter 触发 Runtime Action
- Adapter 订阅 EventBus 写事件
- Adapter 启动 Worker

### Decision 5 — Insight 不做什么

| 禁止项 | 原因 |
|--------|------|
| Decision | 决策属 Phase 3.15+ Agent Decision Support |
| Policy | Policy 属 Phase 4+ Adaptive Runtime |
| Alert | ADR-016/017 禁止 |
| Action | 触达 Runtime，越界 |
| Self-Modification | Runtime 不自修改 |
| Persistent Memory | Phase 3.15+ 需新 ADR |

### Decision 6 — 位置约束

```
允许路径:
  - tools/insight/              # Phase 3.14 主位置
  - tests/tools/insight/        # 测试位置
  - docs/v6/phase3-14-*         # 设计与报告

禁止路径:
  - v6/runtime/*                # Runtime Kernel Frozen
  - v6/presentation/models.py   # Frozen Phase 3.10
  - v6/presentation/contracts/  # Frozen
  - agent_workbench/runtime/    # v6.9.6 Frozen
  - tools/observation/*         # Phase 3.12 Frozen ADR-016
  - tools/presentation/*        # Phase 3.13 Frozen ADR-017
```

### Decision 7 — Forbidden Import 集合（继承 ADR-016/017）

```python
PHASE_3_14_FORBIDDEN = (
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

### Decision 8 — Insight 类型（Phase 3.14 范围）

**规则**：Phase 3.14 仅生成 3 类 Insight：

| Insight Type | 派生 | 输出 |
|--------------|------|------|
| `ExecutionHealthInsight` | 任务成功率 / 失败率 / 异常率 | 健康评分（0-100）|
| `PerformanceTrendInsight` | latency trend / throughput trend | 趋势标签（improving/stable/degrading）|
| `ResourcePressureInsight` | footprint + depth + memory | 压力评分（low/medium/high）|

**禁止扩展**：
- DecisionRecommendation（属 Phase 3.15+）
- AutoTuningSuggestion（属 Phase 4+）
- AlertTrigger（永远禁止）

### Decision 9 — Schema Stability Rule

**规则**：Insight Schema 遵守 semver。

| 规则 | 操作 |
|------|------|
| minor version（`insight.v0.x → v0.x+1`） | Additive Optional 字段 |
| major version（`insight.v0.x → v1.x`） | 字段重命名或语义变化，必须新 ADR |

**当前 schema**：`insight.v0.1`

### Decision 10 — Re-Entry Triggers（继承 + 新增）

**继承 14 项**：
- ADR-016 8 项（Runtime 修改触发）
- ADR-017 6 项（Presentation 边界触发）

**Phase 3.14 新增 6 项**：

| # | Trigger | 类型 |
|---|---------|------|
| 15 | Insight 派生算法触发 Runtime 调用 | 越界 |
| 16 | Insight 写入 ObservationReport | 违反 Schema Stability |
| 17 | Insight 订阅 EventBus publish | 越界 |
| 18 | Insight 修改 ExecutionMetadata | 越界 |
| 19 | Insight 修改 Registry | 越界 |
| 20 | Agent Insight Layer 直接执行 Runtime Action | 越界 |

**Total**: 14 + 6 = **20 项 Re-Entry Triggers**

---

## 4. 跨 Phase 边界

```
Phase 3.12 (Frozen ADR-016)
Runtime Observation Foundation
    |
    | ObservationReport (frozen)
    v
Phase 3.13 (Frozen ADR-017)
Observation Presentation & Consumption Layer
    |
    | ObservationViewModel (frozen)
    v
Phase 3.14 (本文)
Agent Runtime Insight Boundary
    |
    | InsightArtifact (frozen)
    v
Phase 3.15 (Future ADR-019)
Agent Decision Support
    |
    v
Phase 4 (Future)
Adaptive Runtime (if ever)
```

**禁止跨 Phase 越界**：
- 3.14 不得做 3.15 的事（Decision Support）
- 3.14 不得直接进入 3.15+
- 任何 Adaptive Runtime 越界 → 新 ADR

---

## 5. 与现有 ADR 关系

| 现有 ADR | 与 ADR-018 关系 |
|---------|---------------|
| ADR-013 Runtime Lifecycle Event Extension | Phase 3.14 消费其 TASK_CANCELLED 事件（间接） |
| ADR-014 Cancellation Precedence Rule | Phase 3.14 仅观察结果 |
| ADR-015 Parent-Child Execution Propagation v0.3 | Phase 3.14 消费其 CancellationPropagationContext |
| ADR-016 Observation Layer Contract | Phase 3.14 消费 ObservationReport |
| ADR-017 Observation Presentation Boundary | Phase 3.14 消费 ObservationViewModel |
| **ADR-018 Agent Runtime Insight Boundary** | **NEW: Phase 3.14 Insight 边界冻结（本 ADR）** |

---

## 6. 未来扩展

按 Review Recommendation 路线：

- **Phase 3.15+**: Agent Decision Support（需新 ADR-019+）
- **Phase 3.15+**: Persistent Memory（需新 ADR-019+）
- **Phase 4**: Adaptive Runtime（需独立 ADR 流程 + Runtime Re-Validation）

**未来 ADR 必须**：
- 不得违反 ADR-016/017/018 边界
- 触发 Re-Entry Trigger 时重新 Review
- Phase 3.14 当前 **不预创建** 任何 Decision / Action / Policy 模块

---

## 7. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | Boundary Strict + Insight ≠ Runtime Control | ✅ |
| Implementation Lead | Phase 3.14 Scope Defined | ✅ |
| QA Lead | Plan 可执行 | ✅ |
| Boundary Guardian | 14+6 Re-Entry Triggers | ✅ |
| Frozen Contract Maintainer | Zero modification | ✅ |
| OD-G0-001 Maintainer | No Speculative Abstraction | ✅ |

---

## 8. References

- [Phase 3.14 Scope Definition](../../docs/v6/phase3-14-agent-insight-design.md)
- [Phase 3.13 Completion Report](../../docs/v6/phase3-13-completion-report.md)
- [ADR-017 Observation Presentation Boundary](ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](../../docs/v6/phase3-11-e-freeze-validation-report.md)
- [OD-G0-001 Architecture Evolution Rule](../../.project/observations/OD-G0-001-architecture-evolution-rule.md)