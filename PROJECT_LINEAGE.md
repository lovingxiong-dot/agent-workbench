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
    +-- Step 5+
```

## Rules for AI Agents

1. **The active development line is `v6-dev` at version `v6.0.0-alpha`.** All new code, tests, documentation, and tags must go here.
2. **Do not modify `v5-dev` except for archival documentation.** No feature commits, no version bumps, no tag moves.
3. **Do not merge `v5-dev` into `v6-dev`.** If V6 needs a capability that exists in V5, re-implement it within V6 architecture or bridge through an Adapter.
4. **When in doubt, read `PROJECT_BLUEPRINT.md` and `.handoff/HANDOFF.md` first.** They contain the current authoritative state.
