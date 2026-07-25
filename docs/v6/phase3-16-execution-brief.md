# Phase 3.16 — Execution Brief (v0.3 MVP-Focused)

> **Status**: EXECUTION BRIEF (Ready for Agent Batch)
> **Date**: 2026-07-25
> **Phase**: 3.16 Cognitive Continuity Layer + Harness Integration (MVP)
> **ADR**: ADR-020 v0.3
> **Input**: Phase 3.16 Architecture Review Approved

---

## 1. Context

**Phase 3.11-3.15 已完成**：
- Phase 3.11: Runtime Execution Model (Frozen)
- Phase 3.12: Observation Foundation (ADR-016)
- Phase 3.13: Presentation & Consumption (ADR-017)
- Phase 3.14: Insight Understanding (ADR-018)
- Phase 3.15: Decision Support (ADR-019)

**当前能力**：
```
Runtime → Observation → Insight → Decision → Human Approval → Runtime
```

**当前问题（Phase 3.16 解决）**：
1. 上下文压缩导致项目连续性丢失
2. 长期项目知识无法自动恢复
3. Agent 每次启动像新人，需要重新学习

**Phase 3.16 目标**：建立 Cognitive Continuity Layer（Context Provider）。

**不是**：Memory Governance / AI Brain / Persistent Memory
**是**：Context Provider，连接 Runtime / Insight / Decision Support

---

## 2. Architecture Goal

### 2.1 目标

建立 **Cognitive Continuity Layer**（CMS）：
- 保存重要经验
- 恢复上下文
- 维护项目连续性
- **不**修改 Runtime
- **不**控制 Execution
- **不**自动优化策略

### 2.2 位置

```
Memory System (Context Provider)
       ↑
Human Knowledge / Agent Experience / Project Documents / Workflow History
       ↓
Context Reconstruction
       ↓
Runtime / Insight / Decision Support
```

### 2.3 Harness Integration

Agent Harness 是统一框架：
- Context Layer / Reasoning Layer / Execution Layer
- Memory System 在 Context Layer
- 专家团（Architect / Reviewer / Developer / Research / Validator）降级为 Harness Role Profile

---

## 3. Objective

实现 **Cognitive Continuity Layer MVP**（5 Batches）。

---

## 4. Changes Required

### Batch 1 — MemoryItem Schema

**目标**：定义基础 Memory 数据结构。

**输出**：
```
tools/memory/
├── __init__.py
├── memory_item.py         # frozen MemoryItem
├── memory_types.py        # 4 MemoryType + 4 Source
├── memory_score.py        # 3 维 MemoryScore (v0.3 简化)
└── memory_provenance.py  # ProvenanceRecord
```

**关键**：
- 4 Memory Types: `working / episodic / semantic / procedural`
- 3 Score Dims: `importance / stability / freshness`
- 4 Sources: `human / agent / insight / runtime`
- Provenance: `source / created_at / created_by / decision_support_artifact_id`

**禁止**：
- 无 Runtime import
- 无 Decision Support import
- 无 EventBus

### Batch 2 — MemoryStore Protocol

**目标**：抽象 Storage 接口。

**输出**：
```
tools/memory/
└── memory_store.py        # MemoryStore Protocol + InMemoryStore（默认）
```

**关键**：
```python
class MemoryStore(Protocol):
    def store(self, item: MemoryItem) -> None: ...
    def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]: ...
    def delete(self, item_id: str) -> None: ...
    def update(self, item: MemoryItem) -> None: ...
```

**不要绑定**：
- Vector DB
- SQLite
- Redis
- Cloud

**默认实现**：InMemoryStore（仅字典存储，Phase 3.17+ 再加持久化）

### Batch 3 — ContextLoader

**目标**：解决上下文恢复。

**输入**：
- `project_id`
- `task_id`
- `phase`

**输出**：
- `AgentContextPackage`（含相关 Memory + Project State + Open Questions）

**输出位置**：
```
tools/context/
├── __init__.py
├── context_loader.py        # 主入口
├── context_package.py       # 输出格式
└── query_strategy.py        # 按 query 检索
```

**关键原则**：
- 压缩的是 Memory，**不**是 Conversation
- 按 importance + relevance 排序
- 按 score threshold 过滤

### Batch 4 — Candidate Validation

**目标**：实现 Agent Memory Candidate → Validated Memory 流程。

**输出**：
```
tools/memory/
├── capture.py               # Capture (Agent → Candidate)
├── classify.py              # Classify to 4 Types
├── validate.py              # Validate (Provenance + boundary)
└── memory_candidate.py      # MemoryCandidate dataclass
```

**关键**：
- Agent **不**直接写 Memory
- 必须经 Validate（Provenance 强制 + 边界检查）
- Importance < 0.2 → Discard

### Batch 5 — Tests

**测试**：

| 类别 | 测试 |
|------|------|
| MemoryItem 不可变 | frozen dataclass 验证 |
| 4 Types 完整 | enum 验证 |
| 3 Score 维度 | score dataclass 验证 |
| Provenance 强制 | 必填字段验证 |
| 3-Layer Authority | Human / Agent / Validated |
| MemoryStore 接口 | Protocol 验证 |
| ContextLoader 输出 | package 内容验证 |
| Boundary | 无 Runtime import |
| Regression | Phase 3.11-3.15 全量 |

---

## 5. Do Not Touch

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

## 6. Validation

### 必须

- **Boundary tests** PASS
- **Provenance tests** PASS
- **Import isolation tests** PASS
- **Regression tests** PASS（Phase 3.11-3.15 全量）
- **Memory cannot import Runtime**
- **Memory cannot modify Runtime**
- **Memory cannot trigger Execution**
- **Memory cannot write Decision**
- **3-Layer Authority 验证**

### 禁止路径

- Memory → Runtime direct
- Memory → Runtime via Decision Support
- Runtime → Memory auto-write
- Memory → Autonomous Learning
- Memory → Self Modification
- Memory Candidate 直接 Store（未经 Validate）
- MemoryStore 绑定具体存储（Vector/SQLite/Redis）

---

## 7. 32 项 Re-Entry Triggers（保持）

| 阶段 | 数量 |
|------|------|
| ADR-016 继承 | 8 |
| ADR-017 继承 | 6 |
| ADR-018 继承 | 6 |
| ADR-019 继承 | 6 |
| ADR-020 v0.2 保留 | 6 |
| **Total** | **32** |

**v0.3 决策**：不新增 Trigger（避免膨胀）。

---

## 8. Commit

单一 Phase 3.16 Implementation Batch commit。

---

## 9. Quick Reference

### MemoryItem 字段

```python
@dataclass(frozen=True)
class MemoryItem:
    id: str
    memory_type: MemoryType  # working / episodic / semantic / procedural
    content: Any
    score: MemoryScore       # importance / stability / freshness
    source: MemorySource      # human / agent / insight / runtime
    created_at: float
    created_by: str
    provenance: ProvenanceRecord
    schema_version: str = "memory.v0.1"
```

### 5 阶段 Lifecycle

```
Capture → Classify → Validate → Store → Retrieve
```

### 3 维 Score

```python
@dataclass(frozen=True)
class MemoryScore:
    importance: float  # 0.0-1.0
    stability: float    # 0.0-1.0
    freshness: float   # 0.0-1.0
```

### MemoryStore Protocol

```python
class MemoryStore(Protocol):
    def store(self, item: MemoryItem) -> None: ...
    def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]: ...
    def delete(self, item_id: str) -> None: ...
    def update(self, item: MemoryItem) -> None: ...
```

### ContextLoader

```python
def load_context(
    project_id: str,
    task_id: str,
    phase: str,
) -> AgentContextPackage: ...
```

---

## 10. References

- [ADR-020 v0.3 Cognitive Memory Architecture Contract](../../.project/decisions/ADR-020-cognitive-memory-architecture-contract.md)
- [Phase 3.16 Scope Definition v0.3](phase3-16-cognitive-memory-design.md)
- [Phase 3.15 Completion Report](phase3-15-completion-report.md)
- [ADR-019 Agent Decision Support Boundary](../../.project/decisions/ADR-019-agent-decision-support-boundary.md)
- [ADR-018 Agent Runtime Insight Boundary](../../.project/decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](../../.project/decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../../.project/decisions/ADR-016-observation-layer-contract.md)