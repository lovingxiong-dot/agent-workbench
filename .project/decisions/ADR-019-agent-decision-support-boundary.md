# ADR-019 — Agent Decision Support Boundary

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Scope**: Phase 3.15 — Agent Decision Support Layer
> **Depends on**: ADR-016 (Observation Layer Contract), ADR-017 (Observation Presentation Boundary), ADR-018 (Agent Runtime Insight Boundary)
> **Supersedes**: None

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial ADR-019: Agent Decision Support Boundary |

---

## 1. Purpose

按 Phase 3.14 Completion Review：

> Runtime 是否允许被建议影响？这是 AI Agent OS 架构中最大的分水岭。

本 ADR 冻结 **Agent Decision Support Layer Boundary**：
- **Decision Support = 给人类/Agent 提供建议**
- **Decision Support ≠ 替 Runtime 决定**
- **Human Approval Boundary 必须冻结**

**核心原则**：Decision Support 永远 require_human_approval = True。

---

## 2. Context

### 2.1 当前 Frozen 状态

- Phase 3.11 Frozen：Execution Kernel
- Phase 3.12 Frozen（ADR-016）：Observation Foundation
- Phase 3.13 Frozen（ADR-017）：Presentation & Consumption
- Phase 3.14 Frozen（ADR-018）：Agent Runtime Insight

### 2.2 Runtime Cognitive Pipeline v1

```
Runtime Artifact
    |
    v
ObservationReport
    |
    v
ObservationViewModel
    |
    v
InsightArtifact (Understanding)
    |
    v
DecisionSupportArtifact (Recommendation) ← 本文
    |
    | requires_human_approval = True
    v
Human / Agent
    |
    v
Action (新 Execution)
```

### 2.3 三大风险

按 Phase 3.14 Completion Review Section 5：

1. **Trigger A**: Insight → Runtime Mutation（越界）
2. **Trigger B**: Insight → Permanent Memory（越界）
3. **Trigger C**: Decision Coupling（Phase 3.15 风险）
   - 允许: Insight → Decision Support → Human Approval → Action
   - 禁止: Insight → Decision Engine → Runtime（Adaptive Runtime）

本 ADR 显式禁止以上风险。

---

## 3. Decision

### Decision 1 — Phase 3.15 命名

**规则**：Phase 3.15 正式名称为 **"Agent Decision Support Layer"**。

**不命名为** "Agent Decision Engine"（避免误导成自主控制）。

### Decision 2 — Recommendation 模式（非 Action 模式）

**规则**：Decision Support 输出为 **Recommendation**（含 reason + confidence），不是直接 Action。

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

### Decision 3 — Human Approval Boundary（核心）

**规则**：**所有 DecisionSupportArtifact 必须含 `requires_human_approval: True`**。

```python
@dataclass(frozen=True)
class DecisionSupportArtifact:
    """Phase 3.15 Decision Support 产物。
    
    关键：requires_human_approval 永远为 True。
    任何变更 / override 必须重新 Architecture Review。
    """
    recommendation: RecommendationType
    reason: str
    confidence: float
    context: dict
    requires_human_approval: bool = True
    
    def __post_init__(self):
        if not self.requires_human_approval:
            raise ValueError(
                "DecisionSupportArtifact 必须 requires_human_approval=True"
            )
```

**Approval Flow**：
```
DecisionSupportArtifact
        |
        | requires_human_approval = True
        v
Approval Gate
        |
        +-- approved -> User submit NEW Runtime task
        +-- rejected -> Archive
        +-- modified -> User update reason, then approve
        v
NEW Execution (不修改 existing Execution)
```

### Decision 4 — Stateless Cognitive Layer

**规则**：Phase 3.15 **不引入 Persistent Memory**。

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

### Decision 5 — Decision Support 类型（Phase 3.15 范围）

**规则**：Phase 3.15 仅 5 类 Recommendation Type。

| Recommendation | 输出 | 来源 |
|----------------|------|------|
| `RETRY` | "consider retry" | PerformanceTrend.degrading + lifecycle.timeout |
| `CANCEL` | "consider cancel" | ResourcePressure.high + multiple failures |
| `INVESTIGATE` | "investigate" | ExecutionHealth.score < 50 |
| `ADJUST` | "adjust future execution proposal" | Deadline.deviation > threshold |
| `NO_ACTION` | "no action needed" | All insights stable / healthy |

#### 5.1 ADJUST 精确定义（按 Review 要求）

**ADJUST** 表示：

> Adjust future execution proposal, NOT modify current Runtime behavior.

**允许**：
- "下次任务 timeout 增加 30s"
- "下次任务考虑并发数调整"
- "future task proposal: ..."

**禁止**：
- "当前 Runtime timeout += 30s"
- "modify current Execution parameter"
- 任何修改 existing Execution 状态的语句

#### 5.2 ADJUST 严禁行为

| 行为 | 状态 |
|------|------|
| Modify current Execution state | 🚫 永久禁止 |
| Modify Runtime parameters | 🚫 永久禁止 |
| Adjust existing deadline | 🚫 永久禁止 |
| Suggest future task adjustment | ✅ 允许 |
| Provide proposal for next execution | ✅ 允许 |

**禁止扩展**：
- `AUTO_FIX`（永久禁止）
- `AUTO_TUNE`（永久禁止）
- `IMMEDIATE_ACTION`（永久禁止）

### Decision 6 — Decision Support 定义

**规则**：Decision Support 是 **frozen dataclass**，仅消费 InsightArtifact，不触达 Runtime。

```python
@dataclass(frozen=True)
class DecisionSupportArtifact:
    """Phase 3.15 Decision Support 产物。"""
    recommendation: RecommendationType
    reason: str
    confidence: float
    context: Dict[str, Any]
    requires_human_approval: bool = True
    source_insights: Tuple[InsightArtifact, ...]
    derived_at: float
    schema_version: str = "decision_support.v0.1"
    execution_id: str = ""
    task_id: str = ""
```

**禁止**：
- Decision Support 是 mutable 或带 setter
- Decision Support 引用 Orchestrator / EngineManager
- Decision Support 修改 InsightArtifact
- Decision Support 持久化

### Decision 7 — Decision 派生单向数据流

**规则**：Adapter 仅 `InsightArtifact → DecisionSupportArtifact` 单向转换。

```
InsightArtifact (Phase 3.14 Frozen)
        |
        | DecisionAdapter.read(insight)
        v
DecisionSupportArtifact (Phase 3.15 frozen)
        |
        v
Human / Agent (approval required)
```

**禁止**：
- Adapter 反向修改 Insight
- Adapter 触发 Runtime Action
- Adapter 订阅 EventBus 写事件
- Adapter 启动 Worker
- Adapter 持久化

### Decision 8 — Decision Support 不做什么

| 禁止项 | 原因 |
|--------|------|
| Autonomous Action | 永久禁止 |
| Decision Engine | Phase 3.15 禁止命名 |
| Runtime Decision Override | 永久禁止 |
| Persistent Memory | Phase 3.15 禁止 |
| Learning / Training | Phase 3.15 禁止 |
| Auto Retry | Phase 3.15 禁止（仅可建议） |
| Policy Adjustment | ADR-017 永久禁止 |
| Scheduler Tuning | ADR-017 永久禁止 |
| Self-Modification | Runtime 不自修改 |

### Decision 9 — 位置约束

```
允许路径:
  - tools/decision/                 # Phase 3.15 主位置
  - tests/tools/decision/           # 测试位置
  - docs/v6/phase3-15-*             # 设计与报告

禁止路径:
  - v6/runtime/*                    # Runtime Kernel Frozen
  - v6/presentation/models.py       # Frozen Phase 3.10
  - v6/presentation/contracts/      # Frozen
  - agent_workbench/runtime/        # v6.9.6 Frozen
  - tools/observation/*             # Phase 3.12 Frozen ADR-016
  - tools/presentation/*            # Phase 3.13 Frozen ADR-017
  - tools/insight/*                 # Phase 3.14 Frozen ADR-018
```

### Decision 10 — Forbidden Import 集合（继承 ADR-016/017/018）

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

### Decision 11 — Schema Stability Rule

**规则**：Decision Support Schema 遵守 semver。

| 规则 | 操作 |
|------|------|
| minor version | Additive Optional 字段 |
| major version | 字段重命名或语义变化，必须新 ADR |

**当前 schema**：`decision_support.v0.1`

### Decision 12 — Re-Entry Triggers（继承 + 新增）

**继承 20 项**：
- ADR-016 8 项
- ADR-017 6 项
- ADR-018 6 项

**Phase 3.15 新增 6 项**：

| # | Trigger | 类型 |
|---|---------|------|
| 21 | Decision Support output bypass Human Approval | 越界 |
| 22 | Decision Support 直接调用 Runtime submit | 越界 |
| 23 | Decision Support 修改 existing Execution | 越界 |
| 24 | Decision Support 持久化（DB / File） | 越界 |
| 25 | Decision Support 形成 Learning state | 越界 |
| 26 | Decision Support `requires_human_approval=False` | 越界 |

**Total**: 20 + 6 = **26 项 Re-Entry Triggers**

#### 12.1 最高级 Cognitive Authority Escalation Trigger（按 Review）

**定义**：

> **任何模块获得以下权限立即触发 Architecture Re-review**：
> - Runtime Mutation 权限
> - Policy 修改权限
> - Execution Control 权限

**触发原因**：

这是 AI Agent OS 最危险的演化路径：

```
Insight
   |
   v
Decision Support
   |
   v
Decision Engine
   |
   v
Runtime Controller
```

一旦形成，**Human Boundary 消失**。

#### 12.2 Escalation Path 监控

| 阶段 | 权限 | 状态 |
|------|------|------|
| Insight (Phase 3.14) | Read-only | ✅ Safe |
| Decision Support (Phase 3.15) | Recommendation + Approval Required | ✅ Safe |
| Decision Engine (Future) | Auto-Execute | 🚫 **Triggers Re-review** |
| Runtime Controller (Future) | Runtime Mutation | 🚫 **Triggers Re-review** |
| Policy Modifier (Future) | Policy Change | 🚫 **Triggers Re-review** |

#### 12.3 任何 Cognitive Authority Escalation 必须：

1. **立即暂停当前实现**
2. **重新触发 Architecture Review**（独立 ADR）
3. **新增 ADR 显式冻结新权限边界**
4. **更新 Re-Entry Trigger 列表**
5. **回归测试 + 边界验证**

### 重点守护 3 项（按 Review）

**Trigger A**: Insight → Runtime Mutation
- 允许: Insight → Agent Context
- 禁止: Insight → Runtime Mutation

**Trigger B**: Insight → Permanent Memory
- 允许: Insight → Export
- 禁止: Insight → Permanent Memory

**Trigger C**: Decision Coupling
- 允许: Insight → Decision Support → Human Approval → Action
- 禁止: Insight → Decision Engine → Runtime（Adaptive Runtime）

---

## 4. 跨 Phase 边界

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
Phase 3.16+ (Future ADR-020+)
Persistent Memory / Learning
    |
    v
Phase 4 (Future)
Adaptive Runtime (if ever)
```

**禁止跨 Phase 越界**：
- 3.15 不得做 3.16+ 的事（Persistent Memory / Learning）
- 3.15 不得直接进入 Phase 4
- 任何 Adaptive Runtime 越界 → 新 ADR

---

## 5. 与现有 ADR 关系

| 现有 ADR | 与 ADR-019 关系 |
|---------|---------------|
| ADR-013-015 Runtime Frozen | Phase 3.15 消费其 Observation Events |
| ADR-016 Observation Layer Contract | Phase 3.15 消费 ObservationReport（间接） |
| ADR-017 Observation Presentation Boundary | Phase 3.15 消费 ObservationViewModel（间接） |
| ADR-018 Agent Runtime Insight Boundary | Phase 3.15 消费 InsightArtifact |
| **ADR-019 Agent Decision Support Boundary** | **NEW: Phase 3.15 Decision 边界冻结（本 ADR）** |

---

## 6. 未来扩展

按 Review Recommendation：

- **Phase 3.16+**: Persistent Memory / Learning（需新 ADR-020+）
- **Phase 4**: Adaptive Runtime（需独立 ADR + Runtime Re-Validation）

**未来 ADR 必须**：
- 不得违反 ADR-016/017/018/019 边界
- 触发 Re-Entry Trigger 时重新 Review
- Phase 3.15 当前 **不预创建** 任何 Memory / Learning / Adaptive 模块

---

## 7. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | Boundary Strict + Human Approval | ✅ |
| Implementation Lead | Phase 3.15 Scope Defined | ✅ |
| QA Lead | Plan 可执行 | ✅ |
| Boundary Guardian | 14+6+6 = 26 Re-Entry Triggers | ✅ |
| Frozen Contract Maintainer | Zero modification | ✅ |
| OD-G0-001 Maintainer | No Speculative Abstraction | ✅ |

---

## 8. References

- [Phase 3.15 Scope Definition](../../docs/v6/phase3-15-decision-support-design.md)
- [Phase 3.14 Completion Report](../../docs/v6/phase3-14-completion-report.md)
- [ADR-018 Agent Runtime Insight Boundary](ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](../../docs/v6/phase3-11-e-freeze-validation-report.md)