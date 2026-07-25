# Project Lineage

This file defines the product-line identity of AI Agent Workbench. It exists so that any AI agent, contributor, or reviewer entering the repository can immediately understand which line is active and which is historical.

## V5 Line

| Field | Value |
|---|---|
| **Status** | Frozen / Legacy |
| **Purpose** | Previous architecture: PySide6 desktop assistant with Phase-Driven Workflow Engine, Ask/Plan/Craft modes, and integrated tools. |
| **Branch** | `v5-dev` |
| **Tags** | `v5.x.x-alpha`, `v4.x.x-alpha` |
| **Maintenance** | Read-only archive. No new features, no bug fixes unless critical security issues. |

## V6 Line

| Field | Value |
|---|---|
| **Status** | Active Development |
| **Purpose** | New Runtime Architecture: an embeddable Agent OS Kernel built around `RuntimeContext`, eight Engines, and Runtime Trace. |
| **Branch** | `v6-dev` |
| **Public Baseline** | `v6.0.0-alpha` |
| **Internal Migration Checkpoint** | `v6.5.8-alpha` (kept for historical traceability, not a public release) |

## Version Lineage Diagram

```text
v5-dev (Frozen)
    |
    |-- v5.0.23-alpha
    |-- ...
    |
    +-- v6.5.8-alpha  ← internal migration checkpoint (Step 4 technical snapshot)
            |
            | cut to v6-dev
            |
            v
v6-dev (Active)
    |
    +-- v6.0.0-alpha  ← public baseline: V6 independent Runtime architecture line
    |
    +-- v6.9.6-foundation  ← Runtime Foundation Layer Frozen
    |
    +-- v6.15.0-alpha  ← Phase 2-D Product Shell Integration
    |
    +-- v6.16.0-alpha (2026-07-24)  ← Phase 3.9 Presentation Contract Stabilization [narrative]
    |     |
    |     +-- v6.17.0-alpha (2026-07-25)  ← Phase 3.10 Runtime Presentation Integration
    |     |
    |     +-- v6.16.0-alpha (2026-07-25)  ← Phase 3.11 Execution Kernel Evolution [RE-TAGGED]
    |           |
    |           |  ← Phase 3.11 Finalization Batch (Runtime Boundary Audit + Tag Migration)
    |           |
    |           +-- v6.18.0-alpha (2026-07-25)  ← Phase 3.11 Execution Kernel [NEW HEAD]
    |
    +-- Step 5+ / Phase 3.12+  ← Workbench Ecosystem evolution
```

### Tag Migration Note (2026-07-25)

> `v6.16.0-alpha` tag was originally created for Phase 3.9 Presentation Contract (narrative). After Phase 3.11 Finalization Batch, the same tag was **migrated** to point to the Phase 3.11 Runtime commit. `v6.18.0-alpha` was created as the new top-level version. CHANGELOG records both states for clarity.

> **Important**: When referring to v6.16.0-alpha in narrative context, the meaning depends on date:
> - **Before 2026-07-25**: Phase 3.9 Presentation Contract (narrative only, no actual tag was created)
> - **After 2026-07-25**: Phase 3.11 Execution Kernel Evolution (actual git tag)

## Rules for AI Agents

1. **The active development line is `v6-dev` at version `v6.18.0-alpha` (2026-07-25).** All new code, tests, documentation, and tags must go here.
2. **The Runtime Kernel is frozen at `v6.16.0-alpha` (Phase 3.11 Execution Kernel Evolution).** Future Runtime changes are limited to: bug fix, frozen contract compatibility. Memory, Knowledge, Identity, Harness Logic are **forbidden** in `v6/runtime/`.
3. **Do not modify `v5-dev` except for archival documentation.** No feature commits, no version bumps, no tag moves.
4. **Do not merge `v5-dev` into `v6-dev`.** If V6 needs a capability that exists in V5, re-implement it within V6 architecture or bridge through an Adapter.
5. **When in doubt, read `PROJECT_BLUEPRINT.md` and `.handoff/HANDOFF.md` first.** They contain the current authoritative state.
6. **Phase 3 Consolidation (ACTIVE)**: After every Architecture Leap, perform an Artifact Sync Batch (CHANGELOG / BLUEPRINT / LINEAGE / commit / tag / push / handoff) before proceeding to next phase.

## Current Milestone (2026-07-25)

- **Current Version**: v6.18.0-alpha
- **Current Branch**: v6-agent (Runtime: v6-dev)
- **Frozen Baseline**: v6.16.0-alpha (Phase 3.11 Runtime Frozen) + v6.17.0-alpha (Phase 3.10 Presentation Frozen) + v6.9.6-foundation (Runtime Foundation Frozen)
- **Pending Changes**: Phase 3.12-3.15 Asset Sync (Observation/Presentation/Insight/Decision Support) + Phase 3.16 Architecture (Memory + Harness)
- **Next Phase**: Phase 3.12 Observation Layer (after Phase 3 Consolidation C0-C3)
