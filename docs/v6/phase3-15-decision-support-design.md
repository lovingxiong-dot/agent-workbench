# Phase 3.15 — Agent Decision Support Layer

> **Status**: DESIGN DRAFT v0.1
> **Date**: 2026-07-25
> **Phase**: 3.15
> **Depends on**: Phase 3.14 Frozen (ADR-018)
> **Output**: ADR-019 Agent Decision Support Boundary

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Phase 3.15 Scope Definition |

---

## 1. Purpose

按 Phase 3.14 Completion Review：

> Runtime 是否允许被建议影响？这是 AI Agent OS 架构中最大的分水岭。

Phase 3.15 定位：

```
Phase 3.15 = Agent Decision Support Layer

不是：

❌ Agent Decision Engine（容易误导成自主控制）
❌ Runtime Decision Override
❌ Autonomous Action

是：

✅ Decision Support (建议)
✅ Recommendation (含 reason + confidence)
✅ Human Approval Boundary
✅ Stateless Cognitive Layer
```

**核心原则**：Decision Support = 给人类/Agent 提供**建议**；不替 Runtime 决定。

---

## 2. Phase 3.15 关键判断

### 2.1 命名

| 选择 | 状态 | 原因 |
|------|------|------|
| ❌ Agent Decision Engine | Prohibited | 误导成自主控制 |
| ✅ **Agent Decision Support Layer** | 本 ADR 选择 | 准确反映 support 而非 control |

### 2.2 三大前置问题

按 Review Section 8 的 3 个 Question：

#### Q1: Decision Support 输出形态？

**本 ADR 决策**：**Recommendation** 模式（不是 Action 模式）。

```json
{
  "recommendation": "consider retry",
  "reason": "timeout trend increased 3x in last 5 minutes",
  "confidence": 0.82,
  "context": {
    "execution_id": "exec-1",
    "task_id": "t1",
    "based_on_insights": [
      "performance_trend.degrading",
      "resource_pressure.high"
    ]
  },
  "requires_human_approval": true
}
```

**禁止**：直接 action 模式（如 `{"action": "retry_execution"}`）。

#### Q2: Human Boundary 在哪里？

**本 ADR 决策**：**Approval Boundary 必须冻结**。

```
Decision Support Output
        |
        | requires_human_approval = true
        v
Human / Agent
        |
        | (approve / reject / modify)
        v
Action
```

**禁止**：
- Decision Support → Runtime 直接 Action
- Decision Support → Agent 自动执行
- Decision Support → 后台 Worker 触发

#### Q3: Memory 政策？

**本 ADR 决策**：**不引入 Persistent Memory**。

```
Phase 3.15 = Stateless Cognitive Layer
- Observation (stateless, Phase 3.12)
- Insight (stateless, Phase 3.14)
- Decision Support (stateless, 本文)
= 不持久化任何 state
```

**禁止**：
- Decision Support 写入 DB / File
- Decision Support 缓存历史
- Decision Support 形成 Learning 状态

**未来 Memory** 属独立 Architecture Domain（需新 ADR）。

---

## 3. Phase 3.15 Scope

### 3.1 In-Scope

| 类别 | 内容 |
|------|------|
| Decision Support Artifact | frozen dataclass，含 recommendation + reason + confidence |
| Recommendation Types | retry / cancel / adjust / investigate / no_action |
| Decision Adapter | 从 InsightArtifact 派生 Recommendation |
| Output Schema | `decision_support.v0.1` |
| Human Approval Boundary | frozen runtime check：`requires_human_approval` |
| Test Strategy | Primitive + Integration + Boundary + Approval Boundary Tests |

### 3.2 Out-of-Scope（严格禁止）

| 类别 | 状态 |
|------|------|
| Autonomous Action | 🚫 永久禁止 |
| Decision Engine | 🚫 Phase 3.15 禁止命名 |
| Runtime Decision Override | 🚫 永久禁止 |
| Persistent Memory | 🚫 Phase 3.15 禁止；Future ADR 决定 |
| Learning / Training | 🚫 Phase 3.15 禁止；Future ADR 决定 |
| Auto Retry | 🚫 Phase 3.15 禁止（仅可建议） |
| Policy Adjustment | 🚫 ADR-017 永久禁止 |
| Scheduler Tuning | 🚫 ADR-017 永久禁止 |

---

## 4. Architecture Boundary Review

### 4.1 继承 ADR-016/017/018 Forbidden Imports

```python
PHASE_3_15_FORBIDDEN = (
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

### 4.2 Phase 3.15 允许 import

```python
PHASE_3_15_ALLOWED = {
    "tools.observation",             # Phase 3.12 Frozen
    "tools.presentation",            # Phase 3.13 Frozen
    "tools.insight",                 # Phase 3.14 Frozen
    "v6.presentation.observation",   # Phase 3.13 UI
    "v6.runtime.event_bus",          # Frozen Types (read-only)
    "v6.runtime.execution_metadata", # Frozen Types
    "v6.runtime.execution_registry", # Frozen Public API
    "v6.runtime.trace",              # Frozen Types
}
```

### 4.3 不变量

| 不变量 | 验证 |
|--------|------|
| DecisionSupportArtifact frozen dataclass | `@dataclass(frozen=True)` |
| Adapter 单向数据流 | Insight → Decision |
| `requires_human_approval` 永远 True | 单元测试 |
| 不订阅 EventBus | 静态 import 检查 |
| 不修改 Insight | 单元测试 |
| 不修改 Runtime | 静态 import 检查 |

---

## 5. Decision Support 类型（Phase 3.15 范围）

| Recommendation | 输出 | 来源 |
|----------------|------|------|
| `RETRY` | "consider retry" | PerformanceTrend.degrading + lifecycle.timeout |
| `CANCEL` | "consider cancel" | ResourcePressure.high + multiple failures |
| `INVESTIGATE` | "investigate" | ExecutionHealth.score < 50 |
| `ADJUST` | "consider adjust deadline" | Deadline.deviation > threshold |
| `NO_ACTION` | "no action needed" | All insights stable / healthy |

**禁止扩展**：
- `AUTO_FIX`（永久禁止）
- `AUTO_TUNE`（永久禁止）
- `IMMEDIATE_ACTION`（永久禁止）

---

## 6. Human Approval Boundary（核心）

### 6.1 强制规则

**所有 DecisionSupportArtifact 必须含 `requires_human_approval: True`**。

```python
@dataclass(frozen=True)
class DecisionSupportArtifact:
    """Phase 3.15 Decision Support 产物。
    
    关键：requires_human_approval 永远为 True。
    任何变更 / override 必须重新 Architecture Review。
    """
    recommendation: RecommendationType
    reason: str
    confidence: float  # 0.0-1.0
    context: dict
    requires_human_approval: bool = True  # 强制 True
    
    def __post_init__(self):
        # frozen=True 时, 绕过 setattr 限制
        if not self.requires_human_approval:
            raise ValueError(
                "DecisionSupportArtifact 必须 requires_human_approval=True"
            )
```

### 6.2 Approval Flow

```
DecisionSupportArtifact
        |
        | requires_human_approval = True
        v
Approval Gate
        |
        +-- approved -> User submit new Runtime task (新 Execution)
        +-- rejected -> Archive
        +-- modified -> User update reason, then approve
        |
        v
NEW Execution (不修改 existing Execution)
```

**禁止**：
- 跳过 Approval Gate 直接触发 Runtime
- 内部 Loop 重复 approve 同一 Decision

---

## 7. Re-Entry Triggers（继承 + 新增）

### 继承 20 项

- ADR-016 8 项
- ADR-017 6 项
- ADR-018 6 项

### Phase 3.15 新增 6 项

| # | Trigger | 类型 |
|---|---------|------|
| 21 | Decision Support output bypass Human Approval | 越界 |
| 22 | Decision Support 直接调用 Runtime submit | 越界 |
| 23 | Decision Support 修改 existing Execution | 越界 |
| 24 | Decision Support 持久化（DB / File） | 越界 |
| 25 | Decision Support 形成 Learning state | 越界 |
| 26 | Decision Support `requires_human_approval=False` | 越界 |

**Total Phase 3.15**: 20 + 6 = **26 项 Re-Entry Triggers**

### 重点守护 3 项（按 Review Section 5）

**Trigger A**: Insight 输出变成 Runtime Input
- 允许: Insight → Agent Context
- 禁止: Insight → Runtime Mutation

**Trigger B**: Insight Persistence
- 允许: Insight → Export
- 禁止: Insight → Permanent Memory

**Trigger C**: Decision Coupling（Phase 3.15 风险）
- 允许: Insight → Decision Support → Human Approval → Action
- 禁止: Insight → Decision Engine → Runtime（Adaptive Runtime）

---

## 8. Phase 3.15 演进路线

```
Phase 3.14 (Frozen ADR-018)
Agent Runtime Insight Boundary
        |
        | InsightArtifact (frozen)
        v
Phase 3.15 (本文)
Agent Decision Support Layer
        |
        | DecisionSupportArtifact (frozen)
        v
Phase 3.16+ (Future)
Persistent Memory / Learning
        |
        v
Phase 4 (Future)
Adaptive Runtime (if ever)
```

**禁止**：
- Phase 3.15 不得做 Phase 3.16+ 的事
- Phase 3.15 不得直接进入 Phase 4

---

## 9. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Decision Support → Runtime Action | R1 | Approval Boundary + 26 项 Re-Entry Triggers |
| Decision Support 持久化 | R1 | Stateless Layer 禁止 + Re-Entry Trigger 24 |
| Decision Support 形成 Learning | R1 | 禁止 state mutation + Re-Entry Trigger 25 |
| Decision Support 命名错误演变成 Engine | R0 | 命名 "Support Layer" 而非 "Engine" |
| Approval Boundary 被绕过 | R0 | `requires_human_approval` 永远 True + 单元测试 |
| Output 形态错误（action 而非 recommendation） | R0 | RecommendationType 强制 |
| Memory Domain 越界 | R0 | 禁止持久化 + 独立 ADR |

---

## 10. Review Gate（待 Architecture Review）

- [ ] Phase 3.15 命名（Agent Decision Support Layer，不是 Engine）
- [ ] 严格遵守 ADR-016/017/018 边界
- [ ] Recommendation 模式（非 Action 模式）
- [ ] Human Approval Boundary 冻结
- [ ] Stateless Cognitive Layer
- [ ] 5 类 Recommendation Type（无 AUTO_*）
- [ ] 26 项 Re-Entry Triggers 完整

---

## 11. References

- [Phase 3.14 Completion Report](phase3-14-completion-report.md)
- [ADR-018 Agent Runtime Insight Boundary](../decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)