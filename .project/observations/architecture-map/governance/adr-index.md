# ADR Index

> **Layer**: 1 — Architecture Governance
> **Type**: Decision Records (append-only)

---

## Index

| ADR | Title | Status | Function |
|-----|-------|--------|----------|
| [ADR-001](../../decisions/ADR-001-shell-contract-freeze.md) | Shell Contract Freeze | Frozen | Presentation boundary |
| [ADR-002](../../decisions/ADR-002-phase-2c-presentation-rfc.md) | Phase 2-C Presentation RFC | Frozen | Renderer direction |
| [ADR-003](../../decisions/ADR-003-phase-2d-migration-audit.md) | Phase 2-D Migration Audit | Frozen | Migration audit |
| [ADR-004](../../decisions/ADR-004-governance-audit-phase-2.md) | Governance Audit Phase 2 | Frozen | Governance health |
| [ADR-005](../../decisions/ADR-005-project-identity-boundary.md) | Project Identity Boundary | **Frozen** | Repository vs Product |
| [ADR-006](../../decisions/ADR-006-workbench-v6-identity-freeze.md) | Workbench v6 Identity Freeze | **Frozen** | Workbench v6 scope |
| [ADR-007](../../decisions/ADR-007-foundation-contract-freeze-v1.0.md) | Foundation Contract v0.5 | **Candidate** (PROPOSAL, NON-BINDING) | Foundation symbols |
| [ADR-008](../../decisions/ADR-008-runtime-closure-validation.md) | Runtime Closure Validation | **Closed** (v2.0, append-only) | 4 Loops + Q5 observation |
| [ADR-009](../../decisions/ADR-009-foundation-contract-promotion-proposal.md) | Foundation Contract Promotion Proposal | **Proposal** (NOT Freeze) | Tier A/B/C promotion |
| [ADR-DRAFT-010](../../observations/OD-EX0-003-v6-constitution-external-synthesis.md#section-5-candidate-adr-draft-draft-only-not-submitted) | Personal Assistant & Multi-Agent | **DRAFT ONLY, NOT SUBMITTED** | Future candidate |

## Status Categories

| Status | Count | Description |
|--------|-------|-------------|
| Frozen | 6 | Cannot be modified |
| Closed (append-only) | 1 (ADR-008) | Validation record, only new appends |
| Candidate / Proposal | 2 (ADR-007, 009) | May change without notice |
| Draft Only (Not Submitted) | 1 (ADR-DRAFT-010) | Waiting evidence |

## Append-Only Discipline

| ADR | Version | Discipline |
|-----|---------|------------|
| ADR-008 | v1.0 → v2.1 | Strict append-only, no retroactive edits |

## What This Index Does NOT Do

- ❌ Does NOT submit new ADR.
- ❌ Does NOT change frozen ADR status.
- ❌ Does NOT promote Candidate → Frozen without Tier A evidence.
- ❌ Does NOT submit ADR-DRAFT-010 without Multi-round Architecture Review.