# Workbench v6 — Current Architecture

> **Status**: v6.17.0-alpha Foundation Snapshot
> **Date**: 2026-07-25
> **Scope**: Phase 3 Consolidation - Batch 2

---

## 1. Top-Level Architecture

```
                    Workbench v6
           (Official Product Validation Platform)
                          |
        +-----------------+-----------------+
        |                 |                 |
   v6/runtime      v6/presentation      tools/*
   (Kernel Infra)  (Renderer Contract) (Cognitive Layer)
   Frozen          Frozen              Evolving
```

### 1.1 三层定位

| 层 | 定位 | 状态 |
|----|------|------|
| **v6/runtime** | Kernel Infrastructure | Frozen（Phase 3.11） |
| **v6/presentation** | Renderer Contract | Frozen（Phase 3.10） |
| **tools/*** | Cognitive Capability Layer | Evolving（Phase 3.12-3.16+） |

---

## 2. Runtime Layer (v6/runtime)

**定位**：Kernel Infrastructure（不是主要开发区域）

**状态**：Frozen (Phase 3.11)

**核心模块**：
- `orchestrator` — Execution Coordinator
- `engine_manager` — Engine Lifecycle
- `planner_loop` — Planning Loop
- `capability_router` — Capability Routing
- `event_bus` — Runtime Event Bus
- `context` — Runtime Context
- `enums` — Runtime Enums
- `execution_*` — Execution Domain

**ADR 关联**：
- ADR-013: Runtime Lifecycle Event Extension
- ADR-014: Cancellation Precedence Rule
- ADR-015: Parent-Child Execution Propagation v0.3

---

## 3. Presentation Layer (v6/presentation)

**定位**：Renderer Contract（不是 UI 产品层）

**状态**：Frozen (Phase 3.10)

**核心模块**：
- `models.py` — TracePresentationModel
- `contracts/` — Adapter/Renderer/Model Contracts
- `adapters/` — Runtime/Event/Session/Composite Adapters
- `renderers/` — Fold/Message/Phase/Tool Renderers
- `design/` — Tokens/Themes/Layouts
- `observation/` — Phase 3.13 Runtime Observation Panel (NEW)

**ADR 关联**：
- ADR-001: Shell Contract Freeze

---

## 4. Cognitive Capability Layer (tools/*)

**定位**：Cognitive Capability Layer（演进空间）

**状态**：Evolving (Phase 3.12-3.16+)

### 4.1 模块关系

```
tools/
├── observation/        # Phase 3.12 (Frozen, ADR-016)
│
├── presentation/       # Phase 3.13 (Frozen, ADR-017)
│   └── adapters + exports
│
├── insight/            # Phase 3.14 (Frozen, ADR-018)
│   └── types + adapters + exports
│
├── decision_support/   # Phase 3.15 (Frozen, ADR-019)
│   ├── recommendation/
│   ├── approval/
│   └── exports/
│
├── memory/             # Phase 3.16 (Pending, ADR-020)
│   └── 待设计
│
├── harness/            # Phase 3.16+ (Pending)
│   └── 待设计
│
└── context/            # Phase 3.16+ (Pending)
    └── 待设计
```

### 4.2 7 模块依赖关系

```
              [Harness]
                  |
   +--------------+--------------+
   |              |              |
   v              v              v
[Context]    [Memory]    [Decision Support]
   |              |              |
   +-------+------+              |
           |                     |
           v                     |
       [Insight] <----------------+
           |
           v
    [Observation]
           |
           v
   [Runtime Artifact]
```

### 4.3 数据流（Phase 3.15+）

```
Runtime
  ↓
Observation (Phase 3.12)
  ↓
ObservationViewModel (Phase 3.13)
  ↓
InsightArtifact (Phase 3.14)
  ↓
DecisionSupportArtifact (Phase 3.15)
  ↓ requires_human_approval = True
Human / Agent
  ↓ NEW Execution
Runtime
```

### 4.4 未来 Phase 3.16+ 演进

```
Insight / Decision Support / Observation
  ↓
Memory (Context Provider, Phase 3.16)
  ↓
Context Reconstruction
  ↓
Harness (Cognitive Runtime Coordinator, Phase 3.16+)
  ↓
Runtime
```

---

## 5. ADR 索引

| ADR | Title | Status | Layer |
|-----|-------|--------|-------|
| ADR-013 | Runtime Lifecycle Event Extension | Frozen | Runtime |
| ADR-014 | Cancellation Precedence Rule | Frozen | Runtime |
| ADR-015 | Parent-Child Execution Propagation v0.3 | Frozen | Runtime |
| ADR-016 | Observation Layer Contract | Frozen | tools/observation |
| ADR-017 | Observation Presentation Boundary | Frozen | tools/presentation |
| ADR-018 | Agent Runtime Insight Boundary | Frozen | tools/insight |
| ADR-019 | Agent Decision Support Boundary | Frozen | tools/decision_support |
| ADR-020 | Cognitive Continuity & Harness Architecture Contract | Pending v0.4 | tools/memory + tools/harness |

---

## 6. Re-Entry Triggers 累积

| 阶段 | 数量 |
|------|------|
| ADR-016 继承 | 8 |
| ADR-017 继承 | 6 |
| ADR-018 继承 | 6 |
| ADR-019 继承 | 6 |
| ADR-020 v0.2 保留 | 6 |
| **Total** | **32** |

---

## 7. Test Coverage 累积

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 3.8 / 3.9 / 3.10 | 96 | ✅ |
| Phase 3.11 | 98 | ✅ |
| Phase 3.12 | 59 | ✅ |
| Phase 3.13 | 37 | ✅ |
| Phase 3.14 | 45 | ✅ |
| Phase 3.15 | 37 | ✅ |
| **Total** | **372** | **✅ ALL PASS** |

---

## 8. 演进路线

### 8.1 Phase 3 路径

```
Phase 3.11 (Frozen)        →  v6.15.0-alpha
    ↓
Phase 3.12-3.15 Frozen    →  v6.16.0-alpha
    ↓
Phase 3 Consolidation    →  v6.17.0-alpha ← 现在
    ↓
Phase 3.16 Memory         →  v6.18.0-alpha（Pending）
    ↓
Phase 3.17 Context        →  v6.19.0-alpha（Future）
    ↓
Phase 3.18 CAO            →  v6.20.0-alpha（Future）
    ↓
Phase 4 Adaptive Runtime  →  v7.0.0（Future, if ever）
```

### 8.2 当前状态

| Version | 状态 | 描述 |
|---------|------|------|
| v6.15.0-alpha | Current HEAD | Phase 3.11 Frozen |
| v6.16.0-alpha | Pending Tag | Phase 3.12-3.15 Frozen Assets |
| v6.17.0-alpha | Pending Tag | Phase 3 Consolidation Snapshot |
| v6.18.0-alpha | Future | Phase 3.16 Memory + Harness |

---

## 9. Frozen Boundary 规则

### 9.1 不可越界

| 类别 | 不可越界 |
|------|---------|
| v6/runtime | 任何工具模块不得 import Orchestrator / EngineManager / PlannerLoop / CapabilityRouter（仅读 event_bus / execution_metadata 类型） |
| v6/presentation/models.py | 任何工具模块不得 import（仅通过 v6/presentation/observation/ 子目录集成） |
| agent_workbench/runtime | 任何工具模块不得 import（v6.9.6 Frozen） |
| ADR Frozen 内容 | 不得修改 |

### 9.2 Forbidden Imports 集合

```python
PHASE_3_14_PLUS_FORBIDDEN = (
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

## 10. References

- [Phase 3 Consolidation Design](phase3-consolidation-design.md)
- [Phase 3 Repository Alignment Plan](phase3-repository-alignment-plan.md)
- [Phase 3.15 Completion Report](phase3-15-completion-report.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-018 Agent Runtime Insight Boundary](../decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-019 Agent Decision Support Boundary](../decisions/ADR-019-agent-decision-support-boundary.md)