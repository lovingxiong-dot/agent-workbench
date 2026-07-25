# Phase 3 — Cognitive Layer Boundary

> **Status**: PLAN v0.1
> **Date**: 2026-07-25
> **Phase**: Phase 3 Consolidation - Batch 3

---

## 1. Purpose

按 Phase 3 Consolidation：

冻结 tools/ 7 模块关系，定义 Cognitive Layer 边界。

---

## 2. Cognitive Layer 模块关系

### 2.1 7 模块职责

| 模块 | 职责 | Phase | Status |
|------|------|-------|--------|
| `tools/observation/` | Runtime → ObservationReport（采集） | 3.12 | Frozen (ADR-016) |
| `tools/presentation/` | ObservationReport → ObservationViewModel（投影） | 3.13 | Frozen (ADR-017) |
| `tools/insight/` | ObservationViewModel → InsightArtifact（理解） | 3.14 | Frozen (ADR-018) |
| `tools/decision_support/` | InsightArtifact → DecisionSupportArtifact（建议） | 3.15 | Frozen (ADR-019) |
| `tools/memory/` | Experience → MemoryItem（持久化） | 3.16 | Pending (ADR-020) |
| `tools/harness/` | Cognitive Runtime Coordinator | 3.16+ | Pending (ADR-020 v0.4) |
| `tools/context/` | MemoryItem → Agent Startup Context（恢复） | 3.16+ | Pending (ADR-020) |

### 2.2 依赖关系

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
    [Presentation]
           |
           v
    [Observation]
           |
           v
   [Runtime Artifact]
```

### 2.3 数据流（Phase 3.15+）

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

### 2.4 未来 Phase 3.16+ 演进

```
Insight / Decision Support / Observation
  ↓
Memory (Context Provider, Phase 3.16)
  ↓
Context Reconstruction (Phase 3.16+)
  ↓
Harness (Cognitive Runtime Coordinator, Phase 3.16+)
  ↓
Runtime
```

---

## 3. 边界规则

### 3.1 允许 import

```python
PHASE_3_14_PLUS_ALLOWED = {
    "tools.observation",         # Phase 3.12
    "tools.presentation",        # Phase 3.13
    "tools.insight",             # Phase 3.14
    "tools.decision_support",    # Phase 3.15
    "v6.runtime.event_bus",      # Frozen Types (read-only)
    "v6.runtime.execution_metadata",  # Frozen Types
    "v6.runtime.execution_registry",  # Frozen Public API
    "v6.runtime.trace",          # Frozen Types
}
```

### 3.2 禁止 import

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

## 4. 模块依赖矩阵

| Module | observation | presentation | insight | decision_support | memory | harness | context |
|--------|-------------|--------------|---------|------------------|--------|---------|---------|
| observation | - | - | - | - | - | - | - |
| presentation | ✅ | - | - | - | - | - | - |
| insight | ✅ | ✅ | - | - | - | - | - |
| decision_support | ✅ | ✅ | ✅ | - | - | - | - |
| memory | ✅ | ✅ | ✅ | ✅ | - | - | - |
| harness | ✅ | ✅ | ✅ | ✅ | ✅ | - | - |
| context | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**规则**：
- ✅ 允许：上游模块 → 下游模块
- ❌ 禁止：跨级 / 反向依赖

---

## 5. 验收标准

### 必须

- [ ] 7 模块路径明确
- [ ] 依赖矩阵无环
- [ ] Forbidden Imports 集合完整
- [ ] 边界规则文档化

### 禁止

- ❌ 跨级依赖
- ❌ 反向依赖
- ❌ 共享状态
- ❌ 持久化跨模块写入

---

## 6. References

- [Phase 3 Consolidation Design](phase3-consolidation-design.md)
- [Phase 3 Current Architecture](current-architecture.md)
- [ADR-016 Observation Layer Contract](../decisions/ADR-016-observation-layer-contract.md)
- [ADR-017 Observation Presentation Boundary](../decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-018 Agent Runtime Insight Boundary](../decisions/ADR-018-agent-runtime-insight-boundary.md)
- [ADR-019 Agent Decision Support Boundary](../decisions/ADR-019-agent-decision-support-boundary.md)