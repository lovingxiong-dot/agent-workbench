# Phase 3.14 — Agent Runtime Insight Boundary

> **Status**: DESIGN DRAFT v0.1
> **Date**: 2026-07-25
> **Phase**: 3.14
> **Depends on**: Phase 3.12 Frozen (ADR-016), Phase 3.13 Frozen (ADR-017)
> **Output**: ADR-018 Agent Runtime Insight Boundary

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Phase 3.14 Scope Definition |

---

## 1. Purpose

按 Phase 3.13 Completion Review Recommendation：

> 当前最大的价值是：Runtime 已经稳定，Observation 已经形成，下一阶段应该增加系统理解能力，而不是增加系统控制能力。

Phase 3.14 定位：

```
Phase 3.14 = Agent Runtime Insight Boundary

不是：

❌ Runtime Intelligence Layer（Insight → Runtime Action）
❌ Monitoring Engine（Metric → Insight → Policy）
❌ Adaptive Runtime（Runtime self-modify）
```

---

## 2. 三方向 Ownership 选择

Review 列出 Insight 三个可能方向：

| 方向 | 含义 | 风险 |
|------|------|------|
| A: Presentation Intelligence | Insight 作为 UI 智能增强 | 易演变成 Dashboard Intelligence |
| B: Agent Cognitive Layer | Insight 作为 Agent 输入 | 易演变成 Agent Decision Override Runtime |
| C: Runtime Governance Layer | Insight 作为 Runtime 治理依据 | 易演变成 Monitoring Engine / Runtime Feedback |

**本 ADR 决策**：B（Agent Cognitive Layer），但严格 Read-only 消费。

理由：

- Phase 3.13 已确立 Observation Presentation 路径（Human 可见）
- Phase 3.14 需增加 Agent 可见能力
- 严禁 Runtime 自我治理（Runtime 不自修改）

---

## 3. Phase 3.14 Insight 定义

### 3.1 Insight 是什么

```
Insight Artifact
    =
frozen dataclass
+
仅消费 ObservationReport / ObservationViewModel（Phase 3.12/3.13 产出）
+
不修改 ObservationReport / ObservationViewModel
+
不持有 Runtime lifecycle 引用
+
不订阅 EventBus 写事件
+
不调用 Runtime any method
```

**本质**：Insight 是 Observation 数据之上的**派生分析**（更高阶），但**不触达 Runtime**。

### 3.2 Insight 不是什么

| 不是 | 原因 |
|------|------|
| Decision | 决策属 Phase 3.15+ Agent Decision Support |
| Policy | Policy 属 Phase 4+ Adaptive Runtime |
| Alert | Alert 已被 ADR-016/017 禁止 |
| Action | Action 触达 Runtime，越界 |
| Self-Modification | Runtime 不自修改 |

### 3.3 Insight 边界

```
ObservationReport (Phase 3.12 ADR-016)
        |
        | read-only
        v
ObservationViewModel (Phase 3.13 ADR-017)
        |
        | read-only
        v
InsightArtifact (Phase 3.14 ADR-018)
        |
        | read-only
        v
Agent (Phase 3.15+) / Human (Phase 3.13 UI)

Insight 不进入 Runtime。
Insight 不修改 Runtime。
Insight 不订阅 EventBus 写事件。
```

---

## 4. Scope (In/Out)

### 4.1 In-Scope

| 类别 | 内容 |
|------|------|
| Insight 定义 | `InsightArtifact` (frozen dataclass) |
| Insight 派生 | 从 ObservationReport/ObservationViewModel 派生 |
| Insight Adapter | 单向数据流 `Observation → Insight` |
| Insight 序列化 | 遵守 `observation.v0.x` 演进 |
| Insight 测试 | Primitive + Integration + Boundary |

### 4.2 Out-of-Scope（严格禁止）

| 类别 | 状态 | 何时可加入 |
|------|------|-----------|
| Agent Decision Support | 🚫 Phase 3.15+ 需新 ADR | Phase 3.15 ADR-019 |
| Alert Engine | 🚫 ADR-016 禁止 | 永不 |
| Monitoring Engine | 🚫 ADR-016/017 禁止 | 永不 |
| Runtime Feedback Loop | 🚫 ADR-017 禁止 | 永不 |
| Auto Optimization | 🚫 ADR-016 禁止 | 永不 |
| Persistent Memory | 🚫 Phase 3.15+ 需新 ADR | Phase 3.15 ADR-019 |
| Policy Adjustment | 🚫 ADR-017 禁止 | 永不 |
| Scheduler Tuning | 🚫 ADR-017 禁止 | 永不 |
| Runtime self-modify | 🚫 ADR-016 禁止 | 永不 |

---

## 5. Architecture Boundary Review

### 5.1 继承 ADR-016 + ADR-017 Forbidden Imports

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

### 5.2 Phase 3.14 允许 import

```python
PHASE_3_14_ALLOWED = {
    "tools.observation",             # Phase 3.12 Frozen
    "tools.presentation",            # Phase 3.13 Frozen
    "v6.presentation.observation",   # Phase 3.13 UI
    "v6.runtime.event_bus",          # Frozen Types (read-only)
    "v6.runtime.execution_metadata", # Frozen Types
    "v6.runtime.execution_registry", # Frozen Public API
    "v6.runtime.trace",              # Frozen Types
}
```

### 5.3 不变量

| 不变量 | 验证 |
|--------|------|
| InsightArtifact frozen dataclass | `@dataclass(frozen=True)` |
| Adapter 单向数据流 | Observation → Insight |
| 不订阅 EventBus | 静态 import 检查 |
| 不持有 Runtime 引用 | `__dataclass_fields__` 检查 |
| 不修改 ObservationReport | 单元测试 |
| 不修改 ObservationViewModel | 单元测试 |

---

## 6. Insight 类型（Phase 3.14 范围）

### 6.1 三类 Insight（Phase 3.14 仅生成这些）

| Insight Type | 派生 | 输出 |
|--------------|------|------|
| `ExecutionHealthInsight` | 任务成功率 / 失败率 / 异常率 | 健康评分（0-100）|
| `PerformanceTrendInsight` | latency trend / throughput trend | 趋势标签（improving/stable/degrading）|
| `ResourcePressureInsight` | footprint + depth + memory | 压力评分（low/medium/high）|

### 6.2 Insight 不做什么

- ❌ 不建议 Runtime 调整
- ❌ 不触发 Alert
- ❌ 不修改 Execution
- ❌ 不保存历史（属 Persistent Memory）
- ❌ 不写 EventBus

---

## 7. Re-Entry Triggers（继承 + 新增）

### 继承 ADR-016 8 项 + ADR-017 6 项 = 14 项

### Phase 3.14 新增 6 项

| # | Trigger | 类型 |
|---|---------|------|
| 15 | Insight 派生算法触发 Runtime 调用 | 越界 |
| 16 | Insight 写入 ObservationReport | 违反 Schema Stability |
| 17 | Insight 订阅 EventBus publish | 越界 |
| 18 | Insight 修改 ExecutionMetadata | 越界 |
| 19 | Insight 修改 Registry | 越界 |
| 20 | Agent Insight Layer 直接执行 Runtime Action | 越界 |

**Total Phase 3.14**: 14 + 6 = **20 项 Re-Entry Triggers**

---

## 8. Phase 3.14 演进路线

```
Phase 3.13 (Frozen)
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

---

## 9. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Insight → Runtime Action（破坏 Runtime 不自修改） | R1 | ADR-018 禁止 + Re-Entry Trigger |
| Insight → Policy（演变成 Monitoring Engine） | R1 | ADR-016/017 禁止 + ADR-018 强化 |
| Insight 拥有 Runtime 引用 | R0 | Static import check |
| Insight 修改 ObservationReport | R0 | Schema Stability Rule |
| 范围膨胀到 Decision Support | R1 | ADR-018 + Review Re-Entry Triggers |

---

## 10. Review Gate（待 Architecture Review）

- [ ] Phase 3.14 命名与定位正确
- [ ] Scope 严格遵守 ADR-016/017 边界
- [ ] 不包含 Decision / Alert / Runtime Action
- [ ] Insight Ownership 明确（Agent Cognitive Layer, Read-only）
- [ ] 跨 Phase 边界（3.13 → 3.14 → 3.15）正确

---

## 11. References

- [Phase 3.13 Completion Report](phase3-13-completion-report.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)
- [OD-G0-001 Architecture Evolution Rule](../../.project/observations/OD-G0-001-architecture-evolution-rule.md)