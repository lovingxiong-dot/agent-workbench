# Architecture Knowledge Map

> **Type**: Knowledge Index (NOT ADR, NOT Decision)
> **Date**: 2026-07-23
> **Scope**: Knowledge consolidation of already-validated observations
> **Status**: PHASE EX-1 CONSOLIDATION

---

## Purpose

Index all **already-validated observations** in a unified, searchable knowledge map. **NO new design, NO new abstraction, NO new decision.**

This is a **knowledge organization** task, not an Architecture Review.

---

## 5-Layer Architecture Model (Insight from OD-EX0-003)

```
                  Governance
                       |
        +--------------+--------------+
        |              |              |
   Layer 0         Layer 1        Layer 1.5
   Foundation    Architecture    Protocol Contracts
   Runtime       Governance     (CIP/CAP/Event/Request)
        |              |              |
        +--------------+--------------+
                       |
                  Layer 2
              Agent Behavior Contract
                       |
                       v
                  Layer 3
            Runtime Execution Workflow
                       |
                       v
                  Layer 4
            Applications / Renderers
```

---

## Map Index

| Layer | Sub-domain | File | Source OD/ADR |
|-------|------------|------|---------------|
| 0 | Runtime Kernel Boundary | [runtime/kernel-boundary.md](runtime/kernel-boundary.md) | ADR-008 |
| 0 | Runtime Event Evidence | [runtime/event-evidence.md](runtime/event-evidence.md) | ADR-008, OD-R0-004 |
| 0 | Consumer Model | [runtime/consumer-model.md](runtime/consumer-model.md) | OD-C0-001/002/003 |
| 1 | Architecture Constitution | [governance/constitution.md](governance/constitution.md) | architecture-constitution-v6.13.md |
| 1 | ADR Index | [governance/adr-index.md](governance/adr-index.md) | .project/decisions/ |
| 1 | OD Index | [governance/od-index.md](governance/od-index.md) | .project/observations/ |
| 1 | Evolution Rules | [governance/evolution-rules.md](governance/evolution-rules.md) | OD-G0-001, this phase |
| 1.5 | RuntimeRequest | [protocol/request.md](protocol/request.md) | ADR-008.4.1 |
| 1.5 | InteractionEvent + RuntimeEvent | [protocol/event.md](protocol/event.md) | ADR-008.4.3 |
| 1.5 | Presentation Contract | [protocol/presentation.md](protocol/presentation.md) | architecture-constitution P3 |
| 2-3 | Consumer Evidence (validated) | [consumer-evidence/](consumer-evidence/) | OD-C0-001/002 |
| Future | Agent Manager OS Scope | [future/agent-manager-os.md](future/agent-manager-os.md) | OD-EX0-002/003 |
| Future | Personal Assistant Candidate | [future/personal-assistant.md](future/personal-assistant.md) | OD-EX0-002/003 |
| Future | Multi-Agent (Deferred) | [future/multi-agent.md](future/multi-agent.md) | OD-EX0-003 |

---

## Workbench v6 Position (Validated Insight)

```
Workbench v6
    =
Runtime Validation Platform
    +
Human Interaction Shell
```

Similar to **Android Framework + System UI**, NOT Android App.

Runtime is the platform. Workbench is the first validating product.

---

## What This Knowledge Map Does NOT Do

- ❌ Does NOT propose new architecture.
- ❌ Does NOT freeze new symbols.
- ❌ Does NOT submit ADR.
- ❌ Does NOT modify Runtime / Protocol / Foundation.
- ❌ Does NOT trigger AD-A1-005.

---

## Long-term Rule

> **Observation precedes Abstraction.**
>
> Observation → Validation → Promotion → Extraction.

This rule is enforced via [governance/evolution-rules.md](governance/evolution-rules.md).

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Architecture Knowledge Map. Phase EX-1 Consolidation. 13 indexed documents across 5 layers + future scope. |