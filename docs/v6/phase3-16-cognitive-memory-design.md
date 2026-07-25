# Phase 3.16 — Cognitive Continuity Layer + Harness Integration

> **Status**: DESIGN v0.3 (MVP-Focused)
> **Date**: 2026-07-25
> **Phase**: 3.16
> **Depends on**: Phase 3.15 Frozen (ADR-019)
> **Output**: ADR-020 v0.3 + Phase 3.16-B MVP Execution Brief
> **Mode**: MVP Implementation (不治理化)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Design (Boundary-only) |
| v0.2 | 2026-07-25 | Refined: CMS Contract (4 Types / 7 Lifecycle / 5 Importance) |
| **v0.3** | 2026-07-25 | **MVP-Focused: Cognitive Continuity Layer + Harness Integration** (5 Lifecycle / 3 Importance) |

---

## 1. Purpose

按 Phase 3.16 v0.3 Refinement（避免过度设计）：

> 我们不是在设计一个 "完美治理的 Memory 标准"，而是在给 AOS / Workbench / CAO 建立一个真正可用的 **Cognitive Continuity System（认知连续性系统）**。
> 
> 解决三个真实问题：
> 1. 上下文压缩导致项目连续性丢失
> 2. 长期项目知识无法自动恢复
> 3. Agent 每次启动像新人，需要重新学习

**v0.3 核心原则**：
- **MVP First**（实现优先，治理延后）
- **Cognitive Continuity Layer**（不是 Memory Governance）
- **Harness 整合**（避免双系统）
- **5 Lifecycle + 3 Importance**（不 7+5）

---

## 2. 当前问题

### 2.1 Runtime Cognitive Pipeline v1（已建立）

```
Runtime
  ↓ Observation
ObservationReport
  ↓ Presentation
ObservationViewModel
  ↓ Insight
InsightArtifact (Understanding)
  ↓ Decision Support
DecisionSupportArtifact (Recommendation)
  ↓ requires_human_approval = True
Human / Agent
  ↓ NEW Execution
Runtime
```

### 2.2 长期运行问题

- Agent 每次启动无法稳定恢复历史理解
- 上下文压缩导致架构决策、项目状态、工作流程丢失
- 缺乏 "Experience → Meaning Extraction → Memory Formation → Context Reconstruction" 闭环

### 2.3 v0.1 / v0.2 校准原因

v0.1 偏 "安全治理型 Memory"，v0.2 升 CMS Contract。两者都偏治理化。

v0.3 校准：
- 避免 "Memory Governance Project"
- 解决实际 3 个问题
- Harness 整合（避免双系统）
- MVP 5 Lifecycle（不 7）

---

## 3. Memory 重新定位

### 3.1 Memory 位置

```
Memory System (Context Provider)
       ↑
Human Knowledge / Agent Experience / Project Documents / Workflow History
       ↓
Context Reconstruction
       ↓
Runtime / Insight / Decision Support
```

### 3.2 Memory 是

**Context Provider**

**不是**：
- Decision Engine
- Runtime Controller
- Learning Controller

### 3.3 命名

| 命名 | 状态 |
|------|------|
| ❌ Persistent Memory | Prohibited（避免暗示自主学习） |
| ❌ Learning System | Prohibited |
| ❌ Database / Knowledge Base | Prohibited |
| ❌ Memory Governance System | Prohibited |
| ✅ **Cognitive Continuity Layer** | 本 ADR 选择 |

---

## 4. Harness Integration

### 4.1 统一 Agent Harness

**合并前（重叠）**：
- Expert Team (Architect / Reviewer / Tester)
- Harness (Context / Workflow / Validation)

**合并后**：

```
Agent Harness
       |
Context Layer / Reasoning Layer / Execution Layer
       |
Memory System
       |
Observation / Insight / Decision Support
```

### 4.2 专家团降级为 Harness Role Profile

- Architect Role
- Reviewer Role
- Developer Role
- Research Role
- Validator Role

---

## 5. 4 类 Memory Types（保留 v0.2）

| Type | 内容 | 生命周期 |
|------|------|---------|
| **Working** | 当前任务上下文 | 小时/session |
| **Episodic** | 历史事件 | 长期 |
| **Semantic** | 知识/规则/ADR | 长期 |
| **Procedural** | Workflow 经验 | 长期 |

---

## 6. MVP 5 阶段 Lifecycle

```
Capture
   ↓
Classify
   ↓
Validate
   ↓
Store
   ↓
Retrieve
```

**推迟到 Phase 3.16-C**：
- Compress
- Consolidate
- Archive

---

## 7. MVP 3 维 Importance

```yaml
MemoryScore:
  importance: 0.0-1.0
  stability: 0.0-1.0
  freshness: 0.0-1.0
```

**推迟到 Phase 3.16-C**：
- relevance
- reuse_probability

---

## 8. Context Reconstruction

### 8.1 旧 vs 新

**旧**：
```
100万 token 历史聊天 → 直接压缩 → 丢失架构决策
```

**新**：
```
历史交互
    ↓
Memory Extraction
    ↓
Structured Memory
    ↓
Context Loader
    ↓
Agent Startup Context
```

### 8.2 关键原则

**压缩的是 Memory，不是 Conversation。**

### 8.3 启动时加载

不是加载 "昨天所有聊天"，而是加载：

```
Relevant Cognitive Context:
- Foundation Freeze v3.4
- ADR-016 Observation
- ADR-019 Decision Boundary
- Current Milestone: Phase 3.16
- Open Questions
```

---

## 9. 3-Layer Authority

```
Layer 1: Human Memory
   → 直接写
Layer 2: Agent Proposed Memory (Candidate)
   → 必须经 Validate
Layer 3: Validated Memory
   → 进入长期系统
```

**禁止**：Agent 直接写 Memory。

---

## 10. MemoryStore Protocol

```python
class MemoryStore(Protocol):
    """Memory Store 抽象接口。"""
    def store(self, item: MemoryItem) -> None: ...
    def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]: ...
    def delete(self, item_id: str) -> None: ...
    def update(self, item: MemoryItem) -> None: ...
```

**默认实现**：InMemoryStore（仅字典存储）
**未来**：Vector / Graph / Hybrid

---

## 11. Phase 3.16-B Execution Plan

### Batch 1 — MemoryItem Schema
### Batch 2 — MemoryStore Protocol
### Batch 3 — ContextLoader
### Batch 4 — Candidate Validation
### Batch 5 — Tests

（详细见 [Phase 3.16 Execution Brief](phase3-16-execution-brief.md)）

---

## 12. 32 项 Re-Entry Triggers（保持 v0.2 6 项，不新增）

| 阶段 | 数量 |
|------|------|
| ADR-016 继承 | 8 |
| ADR-017 继承 | 6 |
| ADR-018 继承 | 6 |
| ADR-019 继承 | 6 |
| ADR-020 v0.2 保留 | 6 |
| **Total** | **32** |

---

## 13. 验收标准

### 必须

- Boundary tests PASS
- Provenance tests PASS
- Import isolation tests PASS
- Regression tests PASS（Phase 3.11-3.15 全量）

### 禁止修改

```
v6/runtime/                   # Runtime Frozen
v6/presentation/              # Presentation Frozen
tools/observation/            # Frozen ADR-016
tools/presentation/           # Frozen ADR-017
tools/insight/                # Frozen ADR-018
tools/decision_support/       # Frozen ADR-019
agent_workbench/runtime/      # v6.9.6 Frozen
```

---

## 14. Phase 3.16 未来路线

```
Phase 3.16 (v0.3, 本文)
Cognitive Continuity Layer MVP
        ↓
Phase 3.16-B (Agent Batch)
5 Batches Implementation
        ↓
Phase 3.16-C (Future)
Lifecycle 扩展（Compress/Consolidate/Archive）
+ Importance 扩展（relevance/reuse_probability）
        ↓
Phase 3.17 (Future, Independent ADR)
Persistent Storage (Vector / Graph)
        ↓
Phase 3.18 (Future, Independent ADR)
Memory → Decision Support (显式 enable only)
        ↓
Phase 4 (Future, if ever)
Adaptive Runtime
```

---

## 15. References

- [ADR-020 v0.3 Cognitive Memory Architecture Contract](../decisions/ADR-020-cognitive-memory-architecture-contract.md)
- [Phase 3.16 Execution Brief](phase3-16-execution-brief.md)
- [Phase 3.16 Architecture Review Report](phase3-16-architecture-review-report.md)
- [Phase 3.15 Completion Report](phase3-15-completion-report.md)
- [ADR-019 Agent Decision Support Boundary](../decisions/ADR-019-agent-decision-support-boundary.md)
- [ADR-018 Agent Runtime Insight Boundary](../decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)