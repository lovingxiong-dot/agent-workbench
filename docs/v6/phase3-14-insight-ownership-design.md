# Phase 3.14 — Insight Ownership Design

> **Status**: DESIGN v0.1
> **Date**: 2026-07-25
> **Phase**: 3.14
> **Depends on**: ADR-018 Agent Runtime Insight Boundary
> **Output**: Insight Consumption Matrix

---

## 1. Purpose

按 Phase 3.13 Completion Review 提出的 3 方向 Ownership 选择：

| 方向 | 含义 | 风险 |
|------|------|------|
| A: Presentation Intelligence | UI 智能增强 | 易演变成 Dashboard Intelligence |
| B: Agent Cognitive Layer | Agent 输入 | **本 ADR 选择** |
| C: Runtime Governance Layer | Runtime 治理 | 易演变成 Monitoring Engine |

本设计文档明确选择 **B**，并细化各 Consumer 的权限与禁止项。

---

## 2. Insight Ownership Matrix

| Consumer | 权限 | 禁止 |
|----------|------|------|
| **Agent** (Phase 3.15+) | Read InsightArtifact；用于 Decision Support | 不得直接修改 Runtime；不得修改 Insight |
| **Human** (Phase 3.13+) | 通过 Phase 3.13 Panel 间接消费 Insight | 不得触发 Insight → Runtime |
| **Workspace** (Future ADR) | TBD 后续 ADR 决定 | TBD |
| **Runtime** | **🚫 严禁消费** | 破坏 Runtime 不自修改原则 |

---

## 3. Insight → Runtime 数据流（明确禁止）

### 3.1 禁止方向

```
InsightArtifact
        |
        | ✗ Runtime Action Trigger
        v
Runtime Kernel  (🚫 Prohibited)
```

### 3.2 允许方向

```
InsightArtifact
        |
        | ✓ Read-only 消费
        v
Agent / Human / Workspace
```

**关键**：Insight 仅可被 **Runtime 外部** 消费；Runtime 自身**绝不读取** Insight。

理由：
- Runtime 自读取 Insight → 形成 Runtime Feedback Loop
- Runtime 自读取 Insight → 演变成 Runtime Governance
- Runtime 自读取 Insight → 破坏 Phase 3.11 Frozen 边界

---

## 4. Agent Consumer 设计（Phase 3.15+）

### 4.1 Agent 消费 Insight 的边界

| Agent 操作 | 状态 |
|------------|------|
| Read InsightArtifact | ✅ Phase 3.15+ |
| Use Insight for Decision Support | ✅ Phase 3.15+ ADR-019 |
| Modify InsightArtifact | 🚫 Phase 3.14+ |
| Publish Insight back to Runtime | 🚫 ADR-018 |
| Override Runtime Decision | 🚫 ADR-018 |
| Force Runtime Action | 🚫 ADR-018 |

### 4.2 Agent 决策流程（Phase 3.15+ 需 ADR-019 详细定义）

```
InsightArtifact
        |
        | Agent reads
        v
Agent Decision Support
        |
        | Agent decides
        v
User Confirmation Required (Human in the loop)
        |
        | User confirms
        v
Runtime Submit (新 Execution, 不修改现有 Execution)
```

**关键**：Agent Insight → Runtime 必须经过 Human 确认，不直接触发 Runtime Action。

---

## 5. Human Consumer 设计（Phase 3.13 已实现）

### 5.1 间接消费

Phase 3.13 Panel 显示 Observation + Insight Summary（可选）：

```
Runtime Observation Panel
├── Runtime Status (ObservationReport)
├── Performance (ObservationReport)
├── Resource (ObservationReport)
├── Lifecycle (ObservationReport)
└── Insight Summary (InsightArtifact) ← Phase 3.14 扩展
```

### 5.2 Phase 3.14 扩展

Phase 3.14 不修改 v6/presentation/models.py（frozen）；通过 v6/presentation/observation/ 子目录新增 InsightSection（不修改现有 Frozen Panel）。

**或**：保持 Phase 3.13 Panel 不变，Insight 由 Human 通过 Export / Future UI 消费。

---

## 6. Workspace Consumer 设计（Future ADR）

Phase 3.14 不实现 Workspace Consumer；标记为 **Future RFC**。

未来 ADR 应明确：
- Workspace 如何消费 Insight
- Workspace 是否持久化 Insight
- Workspace 如何与 Agent 协作

---

## 7. Runtime Consumer 设计（明确禁止）

| 操作 | 状态 | 原因 |
|------|------|------|
| Runtime 自读取 Insight | 🚫 | 破坏 Runtime 不自修改 |
| Runtime 自基于 Insight 调整 | 🚫 | 形成 Feedback Loop |
| Runtime 自监控 Insight | 🚫 | 演变成 Monitoring Engine |
| Runtime 暴露 Insight 给上层 | ✅ Phase 3.12 通过 ObservationReport | 但 Runtime 不读 Insight |

**核心原则**：Runtime 仅 **生产** Observation（Phase 3.12）；不 **消费** Insight（Phase 3.14）。

---

## 8. Insight Consumption Matrix（最终决策）

|  | Read | Write | Trigger Runtime | Modify Runtime |
|--|------|-------|----------------|----------------|
| **Agent** | ✅ | 🚫 | 🚫 | 🚫 |
| **Human** | ✅ (via Panel) | 🚫 | 🚫 | 🚫 |
| **Workspace** | ⏳ Future | ⏳ Future | ⏳ Future | ⏳ Future |
| **Runtime** | 🚫 | 🚫 | 🚫 | 🚫 |

**4 Consumer 中：**
- Agent：Read-only
- Human：Read-only
- Workspace：TBD
- Runtime：**全禁**

---

## 9. Insight Lifecycle

```
Phase 3.12 (Frozen ADR-016)
Runtime Event → ObservationReport
        |
        v
Phase 3.13 (Frozen ADR-017)
ObservationReport → ObservationViewModel
        |
        v
Phase 3.14 (本文)
ObservationViewModel → InsightArtifact
        |
        v
Phase 3.15+ (Future ADR-019)
InsightArtifact → Agent Decision Support
        |
        v
Phase 4 (Future)
Human → New Runtime Submit
```

**Insight 生命周期终止点**：被 Agent / Human 消费后，不回流 Runtime。

---

## 10. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Agent 消费 Insight 后直接 Runtime Action | R0 | Human in the loop（Phase 3.15+） |
| Runtime 自读取 Insight | R0 | ADR-018 禁止 + 静态 import 检查 |
| Insight 持久化为 Runtime Memory | R0 | Phase 3.14 不引入持久化 |
| Insight → Policy 形成 Monitoring | R0 | ADR-018 禁止 |
| Workspace 消费 Insight 后越界 | R0 | Future ADR 严格 Review |

---

## 11. Phase 3.14 边界确认

| 边界 | 状态 |
|------|------|
| Insight 不进入 Runtime | ✅ ADR-018 禁止 |
| Insight 不修改 Runtime | ✅ ADR-018 禁止 |
| Insight 不订阅 EventBus 写事件 | ✅ ADR-018 禁止 |
| Insight 不订阅 EventBus 读事件（仅消费 ObservationReport） | ✅ Allowed |
| Insight 不持久化 | ✅ Phase 3.15+ 需新 ADR |
| Insight 不触发 Runtime Action | ✅ ADR-018 禁止 |

---

## 12. References

- [Phase 3.14 Scope Definition](phase3-14-agent-insight-design.md)
- [ADR-018 Agent Runtime Insight Boundary](../decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)