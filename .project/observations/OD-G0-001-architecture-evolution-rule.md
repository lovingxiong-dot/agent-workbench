# OD-G0-001 — Architecture Evolution Rule

> **Type**: Observation Log (Governance Rule Proposal)
> **Date**: 2026-07-23
> **Scope**: Repository-wide Architecture Evolution Discipline
> **Status**: PROPOSAL (NOT enforced yet)

---

## Title

Architecture Evolution Rule: "Existing Capability First"

## Purpose

Prevent speculative abstraction that re-engineers proven Runtime capabilities. Codify the discipline that has emerged from Phase 2-D / 2-E observation.

This is a **governance rule proposal**, not a hard constraint. It must be referenced in every Architecture Review.

## The Rule (Chinese)

> **先发现能力，再抽象边界；禁止为了未来设计提前创造空层。**

## The Rule (English)

```
Existing capability first.

Before creating new abstraction:

1. Search existing implementation
2. Observe actual behavior
3. Validate boundary
4. Extract only if repeated usage appears

No speculative abstraction.
```

## Why This Rule Exists

During Phase 2-D / 2-E, two near-misses were observed:

### Near-miss 1: ReplayService relocation temptation

Observation OD-C0-001 found `ReplayService` inside `v6/runtime/`. A naive next step would be:

```
move v6/runtime/replay.py
       ↓
consumer/debugger/
```

This would be **wrong** because:
- ReplayService behavior is already Consumer-like (passive subscriber).
- File location does not equal architecture ownership.
- Moving without evidence of repeated usage = speculative abstraction.

### Near-miss 2: ReplayService denial temptation

Alternative naive step:

```
ReplayService is in v6/runtime/, therefore NOT a Consumer
```

This would be **wrong** because:
- Architecture is defined by behavior, not file location.
- ReplayService subscribes to all events and never invokes Engine — it is Consumer by behavior.
- Denying its Consumer nature hides a useful capability.

**The Rule prevents both temptations** by mandating observation before relocation.

---

## Application Procedure

### Before creating any new abstraction (e.g., `consumer/debugger/`, `consumer/audit/`)

1. **Search existing implementation**: `grep -r "subscribe" v6/` for EventBus subscribers; `grep -r "RuntimeTrace" v6/` for trace collectors.
2. **Observe actual behavior**: Read the source; identify whether the existing module is a passive observer, active driver, or hybrid.
3. **Validate boundary**: Does the existing module cross any forbidden boundary (e.g., invoke Engine, mutate Session State, modify EventBus schema)?
4. **Extract only if repeated usage appears**: If 2+ use cases share the same Consumer pattern, then extraction is justified. Otherwise, observe more.

### Forbidden moves (without Architecture Review)

- `mv v6/runtime/replay.py consumer/` (file location change for an already-working Consumer)
- `cat v6/runtime/replay.py consumer/debugger/` (copying without extraction rationale)
- `cp v6/runtime/replay.py tools/trace_viewer/` (renaming without behavior change)

### Allowed moves (with Architecture Review evidence)

- `mv v6/runtime/replay.py consumer/replay/` IF extraction rationale exists (e.g., cross-product reuse).
- New `consumer/<type>/` module IF no existing equivalent in Runtime.

---

## Why "Behavior > File Location"

Architecture ownership is determined by:
- What the module produces (evidence vs authority).
- What boundaries it crosses (passive subscriber vs active invoker).
- What state it owns (per-task evidence vs cross-task history).

NOT by:
- Which directory it lives in.
- Which package it imports from.
- Which import path is used.

`v6/runtime/replay.py` lives in `v6/runtime/` but behaves as a Consumer. Therefore it IS a Consumer (location-bound, but Consumer).

---

## Relation to Existing ADR

| ADR | Status | Relation |
|-----|--------|----------|
| ADR-005 Project Identity Boundary | Frozen | Defines Repository vs Product; this rule enforces within Product |
| ADR-006 Workbench v6 Identity Freeze | Frozen | Defines Workbench v6 scope; this rule prevents Workbench v6 from expanding into Runtime |
| ADR-007 Foundation Contract v0.5 | Candidate | This rule blocks premature Foundation Freeze |
| ADR-008 Runtime Closure Validation | Closed | This rule preserves closure by preventing re-architecture |
| ADR-009 Foundation Contract Promotion Proposal | Proposal | This rule requires Tier A promotion via behavior evidence |

---

## Enforcement

This rule is **proposed**, not enforced. To enforce:

1. Add to [AGENT_ENTRY.md](../../AGENT_ENTRY.md) "Before Touching ANY File" checklist.
2. Add to Architecture Review template.
3. Reference in every ADR that proposes new abstraction.

Until enforced, this rule is **advisory**.

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Architecture Evolution Rule proposal. Behavior > file location principle. Existing capability first discipline. |