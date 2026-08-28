# PROJECT_CONTEXT

> **Document Type**: Execution Context Snapshot (NOT Architecture Charter)
> **Status**: Active (2026-07-25)
> **Last Updated**: 2026-07-25
> **Purpose**: 让未来 Agent 30 秒内理解项目当前状态，**不需**重新发现。

---

## 1. Current State (2026-07-25)

| Field | Value |
|-------|-------|
| **Active Branch** | `v6-agent` ⭐ (SINGLE source of truth) |
| **HEAD Commit** | `6301a14` |
| **Current Version** | `v6.19.0-alpha` (Reference) |
| **Current Milestone** | Phase 3.15 Decision Support (Code Complete) |
| **Next Milestone** | Phase 3.16 Memory + Harness (Architecture Review Only) |

## 2. Frozen Tags (Architecture Anchors)

| Tag | Date | Milestone |
|-----|------|-----------|
| `v6.9.6-foundation` | 2026-07-09 | **Runtime Foundation Frozen** ⭐ |
| `v6.16.0-alpha` | 2026-07-25 | **Phase 3.11 Runtime Kernel Frozen** (ADR-013/014/015) |
| `v6.17.0-alpha` | 2026-07-25 | **Phase 3.10 Presentation Layer Frozen** |
| `v6.18.0-alpha` | 2026-07-25 | **Current HEAD** (Phase 3.11 Finalization) |

> Tag ordering ≠ Phase ordering（v6.16 = Phase 3.11, v6.17 = Phase 3.10 是 commit 顺序与 architectural 顺序不一致）。

## 3. Stable Line

| Branch | Status | Version |
|--------|--------|---------|
| `main` | Stable release | `v6.12.0-beta.15` |

> **NEVER commit directly to `main`**. All changes go through `v6-agent`.

## 4. Current Phase: 3.12 Observation Layer

### Completed

- ✅ **Phase 3.12 Observation Layer** (`6c15b70` → `3c754f4`) — 3 submodules, 88/88 tests
- ✅ **Phase 3.13 Presentation & Consumption** (`b14754d` → `21c4752`) — 3 submodules, 100/100 tests (NOT promoted to release per AISE Standard)
- ✅ **Phase 3.14 Insight Understanding** (`70141a4` → `69eb7e9`) — 3 submodules, 84/84 tests (NOT promoted to release per AISE Standard)
- ✅ **Phase 3.15 Decision Support** (`9a5f1db` → `6301a14`) — 3 submodules, 100/100 tests (NOT promoted to release per AISE Standard)

### In Progress

- 🔍 **Phase 3.16 Memory + Harness** (Architecture Review Only)
  - NOT a Code Phase. NO Implementation, NO Test, NO Runtime changes.
  - Location: `.project/architecture/phase-3.16-review/`
  - 5 ADRs covering root boundaries:
    - ADR-016 State Ownership (who owns system state)
    - ADR-017 Persistence Authority (Read ≠ Write)
    - ADR-018 Agent Lifecycle (Created/Initialized/Active/Suspended/Archived)
    - ADR-019 Runtime Authority (Runtime can/can't)
    - ADR-020 Human Approval Boundary (Insight → Human Approval → Execution)

### AISE Standard (Daily Phase)

- Code: feature commits per submodule
- Docs: update `PROJECT_CONTEXT.md` (light) + `CHANGELOG.md` (one line)
- No tag, no full Blueprint/Lineage sync, no ADR, no Handoff doc

### AISE Standard (Foundation Milestone)

- Full sync: PROJECT_BLUEPRINT + PROJECT_LINEAGE + ADR + Tag + Handoff
- Trigger: Foundation-level architecture change (e.g. v6.0 → v6.1 → v6.2)

### Principle

> **Observation records what happened. Memory remembers what matters.**
> 两者不要提前合并。Presentation 保持 platform-agnostic。

## 5. Known Structure (tools/observation/)

| Subdir | Status | Purpose |
|--------|--------|---------|
| `tools/observation/contract/` | **NEW (Frozen)** | Phase 3.12 Frozen Contract Schema |
| `tools/observation/reports/` | Prototype (Pending Review) | Internal 5 derived metrics output |
| `tools/observation/collectors/` | Prototype (Pending Review) | EvidenceCollector orchestration |
| `tools/observation/adapters/` | Prototype (Pending Review) | Runtime → Observation Adapters |
| `tools/observation/derived/` | Prototype (Pending Review) | Pure Functions (5 derived metrics) |

> **Coexistence strategy**: Old prototype + new Frozen Contract. Don't delete prototype (already referenced by presentation, insight, tests tools). Phase 3.12 Finalization will decide merge / deprecate.

## 6. Runtime Frozen Boundary (ADR-013/014/015)

**Allowed**:
- ✓ Bug Fix
- ✓ Frozen Contract compatibility

**Forbidden** (in `v6/runtime/`):
- ✗ Memory / Knowledge / Identity
- ✗ Agent Role / Harness Logic
- ✗ New Runtime concepts or control flows
- ✗ New responsibilities for existing Runtime modules

> **Do not touch `v6/runtime/`** unless approved Runtime bug fix. Cognitive Layer lives in `tools/`, NOT `v6/runtime/`.

## 7. Multi-Layer Artifact Chain (Established)

```
RuntimeEvent
    ↓
ObservationArtifact (Phase 3.12 Frozen Contract, schema "observation.v0.1")
    ↓
InsightArtifact (Phase 3.14, schema "insight.v0.1")
    ↓
DecisionSupportArtifact (Phase 3.15, requires_human_approval = True)
    ↓
Human / Agent
    ↓
NEW Runtime Execution
```

## 8. Source Documents (Authoritative)

| Document | Purpose |
|----------|---------|
| [FOUNDATION.md](../FOUNDATION.md) | CENTRE ecosystem worldview |
| [PROJECT_DECLARATION.md](../PROJECT_DECLARATION.md) | **Constitution (FROZEN)** |
| [PROJECT_BLUEPRINT.md](../PROJECT_BLUEPRINT.md) | **Architecture Charter** (active) |
| [PROJECT_STATE.md](../PROJECT_STATE.md) | Current development snapshot |
| [PROJECT_LINEAGE.md](../PROJECT_LINEAGE.md) | Version lineage |
| [AGENT_ENTRY.md](../AGENT_ENTRY.md) | AI Agent onboarding |

## 9. Key ADRs (Frozen)

| ADR | Title | Status |
|-----|-------|--------|
| ADR-013 | Runtime Lifecycle Event Extension | Frozen (Phase 3.11) |
| ADR-014 | Cancellation Precedence Rule | Frozen (Phase 3.11) |
| ADR-015 | Parent-Child Execution Propagation v0.3 | Frozen (Phase 3.11) |
| ADR-016 | Observation Layer Contract | Frozen (Phase 3.12) |
| ADR-017 | Observation Presentation Boundary | Frozen (Phase 3.13) |
| ADR-018 | Agent Runtime Insight Boundary | Frozen (Phase 3.14) |
| ADR-019 | Agent Decision Support Boundary | Frozen (Phase 3.15) |
| ADR-020 | Cognitive Continuity & Harness Architecture Contract | Architecture Review only |

## 10. Tests

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 3.11 Runtime | 100 | ✅ PASS |
| Phase 3.12 Observation Contract | 38 | ✅ PASS |
| Total Frozen Tests | 138 | ✅ PASS |

## 11. Open Items

| Item | Status | Priority |
|------|--------|----------|
| Phase 3.16 Memory + Harness (Architecture Review Only) | 🔍 In Progress | High |
| Future Architecture Cycle | ⏸ Pending | Medium |

### Known Working Tree (untracked / modified, NOT in current Phase scope)

| File | Type | Reason |
|------|------|--------|
| `tests/tools/` | untracked dir | Future Phase tests (3.14+) |
| `tests/v6/presentation/` | untracked dir | Future Runtime tests |
| `tools/insight/` | untracked dir | Phase 3.14 asset |
| `tools/decision_support/` | untracked dir | Phase 3.15 asset |
| `v6/presentation/` | untracked dir | Runtime internal (out of scope) |
| `storage/sessions/*.json` (modified) | runtime data | Now gitignored (storage/**/*.json) |
| `v6/ui/*.py` (modified) | Phase 2-D legacy | Pre-v6.9.6, deferred cleanup |

## 12. Next Steps for Incoming Agent

1. Read this file (PROJECT_CONTEXT.md) — 30 seconds
2. Read [PROJECT_BLUEPRINT.md](../PROJECT_BLUEPRINT.md) — 5 minutes (Architecture Charter)
3. Run `python -m pytest tests/observation/ tests/presentation/ tests/insight/ tests/decision_support/ -v` — verify all PASS
4. Continue with Phase 3.16 (Architecture Review Only, NO code)

**DO NOT**:
- ❌ Re-discover project structure (already in this file)
- ❌ Touch `v6/runtime/`
- ❌ Delete prototype subdirs
- ❌ Commit to `main`
- ❌ Mix Observation with Memory (different concepts)
- ❌ Mix Presentation with UI (Presentation is platform-agnostic, NOT UI Model)
- ❌ Mix Insight with Decision (Insight ≠ Decision, separate phases)
- ❌ Mix Decision with Execution (Decision = options, NOT ActionExecutor)
- ❌ Write any code in Phase 3.16 (Architecture Review ONLY)
- ❌ Add Runtime / Memory / Harness in Phase 3.16
- ❌ Do release ceremonies on every phase (defer to Foundation Milestone)
