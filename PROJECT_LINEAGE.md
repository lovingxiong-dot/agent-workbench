# Project Lineage

> **Repository Authority Sync 2026-07-25** — v6-agent is the **single active development branch**.
> `v6-dev`, `v6-core`, `v6-service` are **historical archives** (not active).

This file defines the product-line identity of AI Agent Workbench. It exists so that any AI agent, contributor, or reviewer entering the repository can immediately understand which line is active and which is historical.

---

## Active Development Branch

```
main              ← Stable release line (always compilable, runnable, releasable)
  └── v6-agent    ← Active development ⭐ (single source of truth)
        ├── feature/*
        ├── fix/*
        └── experiment/*

archive/*         ← Frozen version snapshots (v3 / v4 / v5 / archive/v6-core / archive/v6-service / archive/v6-dev)
```

> **Reality Check (2026-07-25)**:
> - Local HEAD = `b736cb7` on `v6-agent`
> - Remote HEAD = `b736cb7` on `v6-agent` (synced)
> - `v6-agent` is **the single active development branch**
> - `v6-dev`, `v6-core`, `v6-service` exist only as **historical archives** (`archive/v6-*`)

> **Important**: All AI agents MUST checkout `v6-agent` for development. Never develop on `main` or any archive branch.

---

## V5 Line

| Field | Value |
|---|---|
| **Status** | Frozen / Legacy |
| **Purpose** | Previous architecture: PySide6 desktop assistant with Phase-Driven Workflow Engine, Ask/Plan/Craft modes, and integrated tools. |
| **Branch** | `v5-dev` |
| **Tags** | `v5.x.x-alpha`, `v4.x.x-alpha` |
| **Maintenance** | Read-only archive. No new features, no bug fixes unless critical security issues. |

---

## V6 Line (Reality 2026-07-25)

| Field | Value |
|---|---|
| **Status** | Active Development |
| **Active Branch** | `v6-agent` ⭐ |
| **Historical Branches** | `archive/v6-core`, `archive/v6-service`, `archive/v6-dev` |
| **Runtime Foundation** | `v6.9.6-foundation` (2026-07-09, frozen) |
| **Runtime Execution Kernel** | `v6.16.0-alpha` (2026-07-25, Frozen, ADR-013/014/015) |
| **Presentation Layer** | `v6.17.0-alpha` (2026-07-25, Frozen) |
| **Observation Layer** | `v6.19.0-alpha` (2026-07-25, Phase 3.12 Complete, ADR-016) |
| **Current HEAD** | `v6.19.0-alpha` (post-Phase 3.12, pre-Phase 3.13) |
| **Public Baseline** | `v6.0.0-alpha` |
| **Internal Migration Checkpoint** | `v6.5.8-alpha` (kept for historical traceability) |

---

## Version Lineage Diagram (Reality)

```text
v5-dev (Frozen)
    |
    +-- v6.5.8-alpha  ← internal migration checkpoint (Step 4 technical snapshot)
            |
            | cut to v6-dev (now archived)
            v
v6-agent (Active Development — single source)
    |
    +-- v6.0.0-alpha  ← public baseline
    |
    +-- v6.9.6-foundation  ← Runtime Foundation Layer Frozen
    |
    +-- v6.10.0-alpha  ← Phase 2-D Configuration-driven Workbench
    |
    +-- v6.12.0-beta.15  ← Stable release on `main`
    |
    +-- v6.14.0-alpha  ← D5 Agent Selector (currently on stable line)
    |
    +-- v6.15.0-alpha  ← Product Shell Integration Milestone
    |
    +-- v6.16.0-alpha  ← Phase 3.11 Runtime Frozen ⭐
    |
    +-- v6.17.0-alpha  ← Phase 3.10 Presentation Frozen
    |
    +-- v6.18.0-alpha  ← Phase 3.11 Finalization [Current HEAD]
    |
    +-- Phase 3.12+    ← Workbench Ecosystem evolution (pending commits)
```

### Tag Migration Note (2026-07-25)

> `v6.16.0-alpha` tag was originally declared in narrative for Phase 3.9 Presentation Contract. After Phase 3.11 Finalization Batch, the same tag was **migrated** to point to the Phase 3.11 Runtime commit. `v6.18.0-alpha` was created as the new top-level version. CHANGELOG records both states for clarity.

> **Important**: When referring to v6.16.0-alpha in narrative context, the meaning depends on date:
> - **Before 2026-07-25**: Phase 3.9 Presentation Contract (narrative only, no actual tag was created)
> - **After 2026-07-25**: Phase 3.11 Execution Kernel Evolution (actual git tag)

---

## Historical Branches (Archive Only)

| Branch | Original Purpose | Current Status |
|--------|------------------|-----------------|
| `v6-core` | Runtime Kernel (planned separation) | **ARCHIVED** (`archive/v6-core`) |
| `v6-service` | Runtime Service Architecture (planned) | **ARCHIVED** (`archive/v6-service`) |
| `v6-dev` | Generic V6 development line | **ARCHIVED** (`archive/v6-dev`) |

> **Note**: These branches were **planned in theory** as a 3-tier separation (v6-core → v6-service → v6-agent). However, in practice, only `v6-agent` has been actively maintained. The other branches were archived without significant development. This is reflected in the actual git history.

---

## Rules for AI Agents

1. **The active development line is `v6-agent`** ✅ (not `v6-dev`, `v6-core`, or `v6-service`).
2. **Check out `v6-agent`** before any development. Never develop on `main` or any archive branch.
3. **The Runtime Kernel is frozen at `v6.16.0-alpha` (Phase 3.11 Execution Kernel Evolution).** Future Runtime changes are limited to: bug fix, frozen contract compatibility. Memory, Knowledge, Identity, Harness Logic are **forbidden** in `v6/runtime/`.
4. **Do not modify `v5-dev`, `archive/*` except for archival documentation.** No feature commits, no version bumps, no tag moves.
5. **Do not merge `v5-dev`, `archive/*` into `v6-agent`.** If V6 needs a capability that exists in V5 or archive, re-implement it within V6 architecture or bridge through an Adapter.
6. **When in doubt, read `PROJECT_BLUEPRINT.md` and `.handoff/HANDOFF.md` first.** They contain the current authoritative state.
7. **Phase 3 Consolidation (ACTIVE)**: After every Architecture Leap, perform an Artifact Sync Batch (CHANGELOG / BLUEPRINT / LINEAGE / commit / tag / push / handoff) before proceeding to next phase.

---

## Current Milestone (2026-07-25)

- **Current Version**: v6.18.0-alpha
- **Current Branch**: `v6-agent` ⭐
- **HEAD Commit**: `b736cb7` (pushed)
- **Frozen Baseline**: v6.16.0-alpha (Phase 3.11 Runtime Frozen) + v6.17.0-alpha (Phase 3.10 Presentation Frozen) + v6.9.6-foundation (Runtime Foundation Frozen)
- **Stable Release Line**: `main` (currently at v6.12.0-beta.15)
- **Pending Changes**: 
  - Phase 3.12-3.15 Asset Sync (Observation/Presentation/Insight/Decision Support)
  - Phase 3.16 Architecture (Memory + Harness, ADR-020 v0.4)
  - Legacy Phase 2-D working tree changes (v6/ui, agent_workbench/application/, storage/sessions/)
- **Next Phase**: Phase 3.12 Observation Layer (after Phase 3 Consolidation C2-C3)

### Working Tree Status (2026-07-25)

- 3 modified files (uncommitted)
- Phase 2-D legacy changes: `v6/ui/*.py`, `agent_workbench/application/v6_ui_application.py`, `storage/sessions/*.json`
- Phase 3.13-3.15 untracked: `tools/presentation/`, `tools/insight/`, `tools/decision_support/`, `tests/tools/`, `v6/presentation/observation/`
- Phase 3.12 Observation: ✅ committed (3c754f4)
