# OD-EX0-004 — A1 Entry Condition (Ready Criteria Only)

> **Type**: Entry Condition Definition (NOT Gate Activation)
> **Date**: 2026-07-23
> **Scope**: Define when AD-A1-005 Validation Track can be activated
> **Status**: CRITERIA DEFINED ONLY — A1 NOT STARTED

---

## Purpose

Define **Ready Criteria** for AD-A1-005 (A1 Validation Infrastructure) without activating the Gate.

**Critical**: This document does NOT trigger A1. It only lists the conditions that, when all met, would justify a future user authorization to begin Step 1.

---

## Background

AD-A1-005 has been waiting for user authorization since earlier in this session. Multiple Architecture Guardian Reviews have confirmed:

```
AD-A1-005
Validation Infrastructure
WAITING (not abandoned, not started)
```

This document formalizes **what** would justify activation.

---

## Three Required Criteria (NOT yet met)

### Criterion 1: Knowledge Orientation Confirmed

| Sub-criterion | Status | Source |
|---------------|--------|--------|
| Architecture Knowledge Map exists | ✅ DONE | Phase EX-1 (architecture-map/) |
| Knowledge Map ≠ Architecture Contract | ✅ Confirmed | Guardian Review (this session) |
| Knowledge Map covers 5 layers | ✅ DONE | README.md |
| Future scope is Radar only | ✅ Confirmed | future/*.md placeholders |
| v6 ≠ incomplete Agent OS, v6 = Runtime OS Foundation | ✅ Confirmed | OD-EX0-003 + FOUNDATION.md alignment |

**Result**: ✅ Criterion 1 MET.

### Criterion 2: Boundary Stabilization Confirmed

| Sub-criterion | Status | Source |
|---------------|--------|--------|
| Runtime ↔ Protocol boundary clean (no imports crossing) | ✅ Confirmed | Grep result this session |
| Protocol ↔ Application boundary clean (Application routes via InteractionLayer only) | ✅ Confirmed | Grep result this session |
| RuntimeEvent ↔ InteractionEvent mapper is single translation point | ✅ Confirmed | OD-R0-004 Q1 |
| ADR/OD/FOUNDATION/PROJECT_STATE alignment | ✅ Confirmed | EX-2 review this session |
| No contradictory artifacts | ✅ Confirmed | This document |

**Result**: ✅ Criterion 2 MET (this Phase EX-2 session).

### Criterion 3: User Explicit Authorization

| Sub-criterion | Status |
|---------------|--------|
| User has explicitly authorized AD-A1-005 Step 1 (Infrastructure Preparation) | ❌ NOT MET |
| Scope of Step 1 is bounded (workspace skeleton + Evidence Model + Integrity Hash Baseline only) | ❌ PENDING user confirmation |
| Boundary exceptions are documented (no Runtime / Contract / Protocol modification) | ❌ PENDING user confirmation |

**Result**: ❌ Criterion 3 NOT MET.

---

## A1 Entry Condition Verdict

```
Criterion 1: Knowledge Orientation  ✅ MET
Criterion 2: Boundary Stabilization   ✅ MET
Criterion 3: User Authorization      ❌ NOT MET

Overall: NO-GO (waiting user authorization)
```

The Knowledge Map and Boundary Stabilization work is **complete**. The only remaining gate is **explicit user authorization**.

---

## What This Document Does NOT Do

- ❌ Does NOT activate AD-A1-005.
- ❌ Does NOT pre-authorize A1 Step 1.
- ❌ Does NOT define A1 implementation.
- ❌ Does NOT modify Runtime / Protocol / Foundation.

---

## A1 Step 1 Scope (Reference, NOT Activated)

When (and ONLY when) user explicitly authorizes:

Allowed:
- Create `E:\Development\AOS\aos-validation\` directory skeleton
- Define Evidence Model v0.x
- Record aos-runtime Integrity Hash Baseline

Forbidden (R0/R1 Risk):
- Validation Harness Implementation
- Test Execution
- Runtime / Contract / Protocol / State / Identity modification
- CI integration
- Release / Tag operation

---

## Future Step Mapping (Reference)

If Step 1 is authorized:
```
Step 1: Infrastructure Preparation      (workspace skeleton + Evidence Model + Baseline)
Step 2: Validation Harness Design       (R2 Risk, requires separate Authorization)
Step 3: Behavioral Validation          (R3 Risk, requires separate Authorization)
Step 4: Cross-Product Validation       (R4 Risk, separate ADR required)
```

Each Step requires separate authorization per [Architecture Evolution Rule 4 — Intent First + Risk Bounded](../architecture-map/governance/evolution-rules.md).

---

## Recommended Next

**Do NOT** activate A1 immediately after this document.

**Recommended sequence**:
1. ✅ Knowledge Orientation (EX-1)
2. ✅ Boundary Stabilization (EX-2)
3. ⏳ User explicitly authorizes A1 Step 1
4. ⏳ A1 Step 1 executes with bounded scope
5. ⏳ A1 Step 2+ each require separate authorization

Until user explicit authorization, AD-A1-005 remains WAITING.

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial A1 Entry Condition Definition. Criterion 1 + 2 met, Criterion 3 waiting user. No A1 activation. |