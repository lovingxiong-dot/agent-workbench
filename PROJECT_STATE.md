# Project State — Workbench v6

> **Current Development Snapshot** — Repository Governance v1.0
> **Last Updated**: 2026-07-25 (Repository Narrative Migration Batch)
> **Audience**: Contributors, AI agents, reviewers
> **Important**: Version numbers do NOT equal Milestone numbers. They are independent.

---

## Product Identity

| Field | Value |
|-------|-------|
| Repository | `agent-workbench` (lovingxiong-dot/agent-workbench) |
| Product | **Workbench v6** = Workbench OS 1.0 (Agent Workspace) |
| Future Product | Agent Manager OS — Governance Plane (next era) |
| Shared Ancestor | CENTRE / AOS — see [FOUNDATION.md](./FOUNDATION.md) |

---

## Current Snapshot (2026-07-25)

| Field | Value |
|-------|-------|
| **Active Branch** | `v6-agent` ⭐ (SINGLE source of truth) |
| **HEAD Commit** | `b736cb7` (pushed to origin/v6-agent) |
| **Current Version** | `v6.18.0-alpha` |
| **Current Milestone** | Phase 3.11 Finalization Complete |
| **Next Milestone** | Phase 3.12 Observation Layer Implementation |
| **Stable Line** | `main` (v6.12.0-beta.15) |
| **Runtime Foundation** | `v6.9.6-foundation` (2026-07-09, Frozen) |
| **Runtime Execution Kernel** | `v6.16.0-alpha` (2026-07-25, Frozen, ADR-013/014/015) |
| **Presentation Layer** | `v6.17.0-alpha` (2026-07-25, Frozen) |
| **Public Baseline** | `v6.0.0-alpha` |
| **Internal Migration Checkpoint** | `v6.5.8-alpha` (historical) |

> **Version vs Milestone**: `v6.18.0-alpha` is the version; `Phase 3.11 Finalization` is the architectural milestone. They are independent dimensions. v6.16.0-alpha ≈ Phase 3.11 Runtime Freeze is a coincidence, not a rule.

---

## Repository Status

| Indicator | Status |
|-----------|--------|
| Build | Passes |
| Tests | 372 PASS (Phase 3.8-3.15) |
| CLI Mode | `python -m agent_workbench.app --mode cli` |
| GUI Mode (v6/ui) | `python -m agent_workbench.app --mode gui-v6` |
| Multi Renderer Proof | Passes |
| Runtime Frozen | ✅ Phase 3.11 (v6.16.0-alpha) |
| Cognitive Layer (3.12-3.15) | 🟡 Designed, Asset uncommitted (working tree) |
| Phase 3.16 (Memory + Harness) | ⏸ Architecture Review only (not Runtime extension) |

---

## Active Modules

| Module | Path | Status |
|--------|------|--------|
| Runtime Kernel | `v6/runtime/` | **FROZEN** (Phase 3.11, v6.16.0-alpha) |
| Runtime Foundation | `v6/runtime/` (Foundation layer) | **FROZEN** (v6.9.6-foundation) |
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Active |
| Presentation Runtime | `agent_workbench/presentation/runtime.py` | Active |
| Renderer Registry | `agent_workbench/presentation/renderers/registry.py` | Active |
| v6/ui Foundation | `v6/ui/` (22 files) | **FROZEN** (Phase 2-B.2) |
| V6UIRenderer | `agent_workbench/presentation/renderers/v6_ui/` | Active |
| CLI Renderer | `agent_workbench/presentation/renderers/cli_renderer.py` | Active |
| Application Layer | `agent_workbench/application/` | Active |
| Agent Packages | `packages/` (3 agents: personal/coding/research) | Active |
| Provider Integrations | `agent_workbench/services/` (7 providers) | Active |
| **Cognitive Layer (3.12-3.15, uncommitted)** | `tools/observation/`, `tools/presentation/`, `tools/insight/`, `tools/decision_support/` | 🟡 Designed, asset pending commit |
| **Memory + Harness (Phase 3.16)** | `tools/memory/`, `tools/harness/`, `tools/context/` | ⏸ Architecture Review only |

---

## Frozen Modules

| Module | Path | Freeze Point | Tag |
|--------|------|--------------|-----|
| Runtime Foundation | `v6/runtime/` (Foundation) | Phase 3.11 | `v6.9.6-foundation` |
| Runtime Execution Kernel | `v6/runtime/` (Execution) | Phase 3.11 | `v6.16.0-alpha` |
| v6/ui Foundation | `v6/ui/` (22 files) | Phase 2-B.2 | (within v6-agent history) |
| Shell Contract | `agent_workbench/presentation/shell/protocol.py` | Phase 1-B | (within v6-agent history) |
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Phase 2-C.1 | (within v6-agent history) |
| Legacy Workbench UI | `agent_workbench/ui/workbench/` (32 files) | Phase 2-D.1 (deprecated) | (within v6-agent history) |
| V5 Architecture | `_archive/v5/` | Frozen | - |
| Old Agent Engine | `_archive/agent_engine/` | Frozen | - |
| Old Core | `_archive/old_core/` | Frozen | - |

---

## Runtime Freeze Certificate (v6.16.0-alpha)

> After `v6.16.0-alpha`, the `v6/runtime/` kernel is **frozen with explicit boundaries**:

**Allowed**:
- ✓ Bug Fix
- ✓ Frozen Contract compatibility (向后兼容字段)

**Forbidden**:
- ✗ Memory / Knowledge / Identity additions
- ✗ Agent Role / Harness Logic
- ✗ New Runtime concepts or control flows
- ✗ New responsibilities for existing Runtime modules

**Rationale**: Runtime is stable infrastructure. New capabilities enter via Capability Runtime Contract and the Workbench Ecosystem (Provider, Tool, Skill, Workflow, Memory, Knowledge).

---

## Cognitive Layer Architecture (Working Tree — Uncommitted)

> **Important**: Cognitive Layer is **NOT** Runtime Kernel. It is a separate layer above Runtime.

```
Runtime Kernel (Frozen: v6.16.0-alpha)
        ↑
        │ (read-only via RuntimeEvent / ObservationReport)
        ↓
Cognitive Layer (tools/ - NOT in v6/runtime/)
        |
        ├── Observation (Phase 3.12, ADR-016, Frozen contract designed)
        ├── Insight (Phase 3.14, ADR-018, Frozen contract designed)
        └── Decision Support (Phase 3.15, ADR-019, Frozen contract designed)
        ↑
        │ (requires_human_approval = True)
        ↓
Human / Agent
        ↓
NEW Runtime Execution (caller submits)
```

> **Anti-Pattern Warning**: Do NOT add `runtime/observation/`, `runtime/insight/`, or `runtime/decision_support/` to v6/runtime/. This would violate the v6.16.0-alpha Frozen Contract.

---

## Known TODO (2026-07-25)

| # | Item | Priority | Phase |
|---|------|----------|-------|
| 1 | Phase 3.12-3.15 Asset Sync (commit untracked `tools/`, `tests/tools/`, `v6/presentation/observation/`, ADRs, docs) | **High** | Phase 3.12-3.15 |
| 2 | Phase 3.12 Observation Layer Implementation | High | Phase 3.12 |
| 3 | Phase 3.16 Memory + Harness (Architecture Review only) | Medium | Phase 3.16 |
| 4 | PROJECT_BLUEPRINT line 464 disambiguation | **Done (2026-07-25)** | - |
| 5 | Stash cleanup (3 → 0) | Low | Post-Phase 3.12 |
| 6 | Working Tree cleanup (Phase 2-D vs Phase 3.12-3.15 split) | Low | Post-Phase 3.12 |
| 7 | v6/ui legacy worktree changes commit | Low | Post-Phase 3.12 |

---

## Current Milestone

```
Phase 3.11 Runtime Finalization: ✅ CLOSED (2026-07-25, v6.16.0-alpha)
    ├── 8 Runtime components frozen
    ├── 372 tests PASS
    ├── Runtime Boundary Audit (8/8 A, 0 B)
    ├── Handoff document generated
    └── v6-agent HEAD = b736cb7

Next: Phase 3.12 Observation Layer
    ├── 3.12-3.15 Asset Sync (commit working tree)
    ├── Phase 3.12 Observation Layer Implementation
    ├── Phase 3.13 Presentation & Consumption
    ├── Phase 3.14 Insight Understanding
    └── Phase 3.15 Decision Support
```

---

## Last Architecture Decision

- [ADR-019 Agent Decision Support Boundary](../.project/decisions/ADR-019-agent-decision-support-boundary.md) — **Phase 3.15 Frozen** (requires_human_approval=True)
- [ADR-015 Parent-Child Execution Propagation](../.project/decisions/ADR-015-parent-child-execution-propagation.md) — **Phase 3.11 Runtime Frozen**
- [ADR-013 Runtime Lifecycle Event Extension](../.project/decisions/ADR-013-runtime-lifecycle-event-extension.md) — **Phase 3.11 Runtime Frozen**

---

## Git Tags (v6 Series)

| Tag | Date | Milestone | Status |
|-----|------|-----------|--------|
| `v6.0.0-alpha` | 2026-06 | Public baseline | Stable |
| `v6.5.8-alpha` | 2026-06 | Internal migration checkpoint | Historical |
| `v6.9.6-foundation` | 2026-07-09 | **Runtime Foundation Frozen** ⭐ | Frozen |
| `v6.10.0-alpha` | 2026-07 | Configuration-driven Workbench | Active history |
| `v6.12.0-beta.15` | 2026-07 | Stable on `main` | Stable |
| `v6.14.0-alpha` | 2026-07 | D5 Agent Selector | Active history |
| `v6.15.0-alpha` | 2026-07 | Product Shell Integration | Active history |
| **`v6.16.0-alpha`** | 2026-07-25 | **Phase 3.11 Runtime Frozen** ⭐ | Frozen |
| **`v6.17.0-alpha`** | 2026-07-25 | **Phase 3.10 Presentation Frozen** | Frozen |
| **`v6.18.0-alpha`** | 2026-07-25 | **Phase 3.11 Finalization HEAD** | Active |

> **Tag ordering note**: Version numbers (e.g. v6.16, v6.17, v6.18) reflect commit order and may not match architectural phase order. Phase 3.10 (Presentation) is `v6.17.0-alpha`; Phase 3.11 (Runtime Kernel) is `v6.16.0-alpha`. This is intentional to keep stable line on `main` (`v6.12.0-beta.15`) untouched.

---

## Branch Architecture

| Branch | Status | Purpose | Reality |
|--------|--------|---------|---------|
| `main` | Stable release | Always compilable, runnable, releasable | `v6.12.0-beta.15` (落后 v6-agent) |
| `v6-agent` | **Active Development** ⭐ | Single source of truth for product evolution | HEAD = `b736cb7` |
| `archive/*` | Frozen snapshots | Historical v3/v4/v5 + planned v6-core/v6-service/v6-dev | (理论规划未 actualize) |

> **Implementation Reality (2026-07-25)**: In current Git state, **only `v6-agent` is actively maintained**. The planned 3-tier separation (`v6-core` / `v6-service` / `v6-agent`) in PROJECT_BLUEPRINT design has been merged into single `v6-agent` branch. This is intentional to avoid merge conflicts.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [FOUNDATION.md](./FOUNDATION.md) | **Shared ancestor — CENTRE ecosystem** |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Workbench v6 Constitution |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | Agent onboarding |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |
| [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) | Project overview, frozen zones |
| [PROJECT_LINEAGE.md](./PROJECT_LINEAGE.md) | Version lineage map |
| [docs/v6/repo-authority-audit-report.md](./docs/v6/repo-authority-audit-report.md) | 2026-07-25 Authority Audit |
| [Phase 3.11 Runtime Frozen Handoff](./.project/handoff/phase3-11-runtime-frozen-handoff.md) | Phase 3.11 Handoff |
