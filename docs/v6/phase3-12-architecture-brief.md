# Phase 3.12 — Architecture Brief (Observation Layer)

> **Document Type**: Phase 3.12 Architecture Brief
> **Status**: READY FOR EXECUTION
> **Date**: 2026-07-25
> **Phase**: 3.12 Observation Layer Implementation
> **ADR**: [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md) (Frozen contract designed)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Phase 3.12 Brief (post Phase 3.11 Finalization) |

---

## 1. Context

### 1.1 Current State (2026-07-25)

```
✓ Phase 3.11 Runtime Frozen (v6.16.0-alpha, ADR-013/014/015)
✓ Phase 3.10 Presentation Frozen (v6.17.0-alpha)
✓ 372 tests PASS (Phase 3.11 + Cognitive Layer)
✓ v6-agent HEAD = 71ecbf3 (Repository Authority + 3 Blueprint Optimizations)
```

### 1.2 Phase 3.12 Position

```
Phase 3.11 Runtime Finalization: ✅ DONE
    ↓
Phase 3.12 Observation Layer: ⏭ NEXT
    ↓
Phase 3.13 Presentation & Consumption
    ↓
Phase 3.14 Insight Understanding
    ↓
Phase 3.15 Decision Support
    ↓
Phase 3.16 Memory + Harness (Architecture Review only)
```

### 1.3 Goal

Implement **Observation Layer** as the first Cognitive Layer module:

```
Location:    tools/observation/
Consumes:    RuntimeEvent (read-only from v6/runtime/)
Produces:    ObservationArtifact (frozen dataclass)
Must NOT:    touch v6/runtime/
Boundary:    ADR-016 (Observation Layer Contract)
```

---

## 2. Cognitive Pipeline Position

```
Runtime
  ↓ (RuntimeEvent)
Observation (Phase 3.12, ADR-016) ⬅ THIS BATCH
  ↓ (ObservationArtifact)
ObservationViewModel (Phase 3.13, ADR-017)
  ↓ (InsightArtifact)
Insight (Phase 3.14, ADR-018)
  ↓ (DecisionSupportArtifact)
Decision Support (Phase 3.15, ADR-019)
  ↓ (requires_human_approval = True)
Human / Agent
  ↓
NEW Runtime Execution
```

---

## 3. ADR-016 Contract Summary

> **Location**: `/.project/decisions/ADR-016-observation-layer-contract.md`

### 3.1 Key Principles

1. **Read-Only Consumer**: Observation Layer consumes Runtime via `RuntimeEvent` (read-only)
2. **No Runtime Mutation**: Do NOT modify Runtime Kernel (`v6/runtime/`)
3. **Frozen Contract**: `ObservationArtifact` schema is frozen
4. **Layer Separation**: Cognitive Layer is separate from Runtime

### 3.2 Forbidden Imports

```python
PHASE_3_12_FORBIDDEN = (
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
    # Frozen Presentation
    "v6.presentation.models",
    "v6.presentation.contracts",
)
```

---

## 4. Phase 3.12 Execution Plan (5 Batches)

按用户节奏：`Architecture Review → Execution Brief → Trae Batch → Artifact Sync → Commit → Next Milestone`

### Batch 1 — Observation Contract Schema

**目标**：定义 `ObservationArtifact` 数据结构。

**输出**：
```
tools/observation/
├── __init__.py
├── observation_artifact.py    # frozen ObservationArtifact dataclass
├── observation_types.py        # ObservationType enum
└── observation_schema.py      # schema_version = "observation.v0.1"
```

**关键**：
- 5 类 ObservationType（Performance / Resource / Lifecycle / Event / Health）
- 3 维 Score（relevance / confidence / stability）
- Provenance 强制
- schema_version 字段

### Batch 2 — Runtime Event Consumer

**目标**：实现 `RuntimeEvent → ObservationArtifact` 转换器。

**输出**：
```
tools/observation/
├── runtime_event_consumer.py  # listen RuntimeEvent, produce ObservationArtifact
└── event_filter.py            # 过滤 relevant events
```

**关键**：
- 只读 `RuntimeEvent`（不写）
- Filter logic（避免噪声）
- Async subscription pattern

### Batch 3 — Observation Registry

**目标**：实现 ObservationArtifact 存储和检索。

**输出**：
```
tools/observation/
├── observation_registry.py    # in-memory registry (Phase 3.17+ 可替换为 vector store)
└── observation_query.py       # 按 execution_id / task_id / phase 检索
```

**关键**：
- In-memory default（Phase 3.17+ 替换）
- Query interface for Phase 3.13 (Presentation)

### Batch 4 — Boundary Compliance Tests

**目标**：验证 Cognitive Layer 边界。

**输出**：
```
tests/tools/observation/
├── test_observation_artifact.py
├── test_runtime_event_consumer.py
├── test_observation_registry.py
└── test_boundary_compliance.py
```

**关键**：
- Frozen dataclass verification
- No-Runtime-mutation tests
- Forbidden imports verification
- Schema stability tests

### Batch 5 — Phase 3.12 Finalization Batch

按 8-step Finalization Batch pattern：
1. Validate (all observation tests PASS)
2. Update PROJECT_BLUEPRINT.md (mark Phase 3.12 Done)
3. Update CHANGELOG.md (v6.19.0-alpha entry)
4. Update PROJECT_LINEAGE.md (lineage + reality check)
5. Update PROJECT_STATE.md (Current Snapshot)
6. Commit (feat(observation): Phase 3.12 Observation Layer Complete)
7. Tag (v6.19.0-alpha — Phase 3.12 Frozen Observation)
8. Push (v6-agent + tag)
9. Generate Handoff (Phase 3.12 Observation Layer Handoff)

---

## 5. Do Not Touch

```
v6/runtime/                   # Runtime Frozen (v6.16.0-alpha, Phase 3.11)
v6/presentation/models.py    # Frozen Presentation Contract
v6/presentation/contracts/   # Frozen Presentation Contracts
agent_workbench/runtime/      # v6.9.6 Capability Frozen
agent_workbench/presentation/protocols/  # Frozen Interaction Protocol
```

---

## 6. Validation

### 必须

- [ ] All observation tests PASS
- [ ] No forbidden imports
- [ ] No Runtime mutation
- [ ] Provenance enforced
- [ ] Schema stable

### 禁止

- ❌ Add `v6/runtime/observation/`
- ❌ Modify `v6/runtime/`
- ❌ Bypass RuntimeEvent (write directly)
- ❌ Bypass Human Approval (Observation → Decision requires approval)

---

## 7. Quick Reference

### ObservationArtifact 字段

```python
@dataclass(frozen=True)
class ObservationArtifact:
    id: str
    observation_type: ObservationType  # Performance / Resource / Lifecycle / Event / Health
    content: Any
    score: ObservationScore            # relevance / confidence / stability
    source: ObservationSource          # human / agent / runtime / system
    created_at: float
    execution_id: str
    task_id: str
    schema_version: str = "observation.v0.1"
```

### 5 类 ObservationType

| Type | 内容 | 来源 |
|------|------|------|
| Performance | latency / throughput / response time | RuntimeEvent |
| Resource | memory / cpu / connections | RuntimeEvent |
| Lifecycle | state transitions | RuntimeEvent |
| Event | task events / errors | RuntimeEvent |
| Health | system health / errors | RuntimeEvent |

### 3 维 Score

```python
@dataclass(frozen=True)
class ObservationScore:
    relevance: float   # 0.0-1.0, 与当前任务关联度
    confidence: float  # 0.0-1.0, 数据可信度
    stability: float   # 0.0-1.0, 稳定性（如 Frozen Contract = 1.0）
```

---

## 8. References

- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md) (Frozen)
- [PROJECT_BLUEPRINT.md](../../PROJECT_BLUEPRINT.md) (Architecture Charter, 2026-07-25)
- [PROJECT_DECLARATION.md](../../PROJECT_DECLARATION.md) (Constitution, Frozen)
- [PROJECT_STATE.md](../../PROJECT_STATE.md) (Current Snapshot)
- [Phase 3.11 Runtime Frozen Handoff](../../.project/handoff/phase3-11-runtime-frozen-handoff.md)
- [Phase 3.12 Architecture Brief (this document)](phase3-12-architecture-brief.md)

---

## 9. Next Steps

1. ✅ Phase 3.12 Architecture Brief (this document)
2. ⏭ Phase 3.12 Execution Authorization (user approval)
3. ⏭ Batch 1: Observation Contract Schema (Trae execution)
4. ⏭ Batch 2-4: Lifecycle / Registry / Boundary Tests
5. ⏭ Batch 5: Phase 3.12 Finalization (8-step pattern)
6. ⏭ Phase 3.13 Brief
