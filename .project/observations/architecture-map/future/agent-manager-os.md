# Agent Manager OS (Out of Current Product Boundary)

> **Type**: External Scope (NOT part of Workbench v6)
> **Status**: NOT IN SCOPE — separate product

---

## Classification (Per OD-EX0-003 + Guardian Review)

| Capability | Classification |
|------------|----------------|
| Multi-Agent Coordination | **External Scope (Agent Manager OS)** |
| Federation | **External Scope (Agent Manager OS)** |
| Global Registry | **External Scope (Agent Manager OS)** |
| Tenant Governance | **External Scope (Agent Manager OS)** |

These are **NOT Missing** in Workbench v6. They are **Out of Current Product Boundary**.

## Workbench v6 Boundary

```
Workbench v6
    =
Runtime Validation Platform
    +
Human Interaction Shell
```

Workbench v6 covers:
- Runtime Kernel
- Capability / Skill Composition
- Renderer / Presentation
- Configuration-Driven Workbench Loop

Workbench v6 **does NOT** cover:
- Multi-Agent orchestration
- Agent Federation
- Cross-tenant Registry
- Global Governance

## Why This Boundary is Healthy

Past risk: easy to absorb Agent Manager into Workbench v6 → Runtime Kernel pollution.

Current boundary:
```
Workbench v6 (Runtime + Capability + Renderer)
        |
        | consume RuntimeEvent
        |
Agent Manager OS (Multi-Agent + Registry + Scheduling + Federation + Governance)
```

Agent Manager OS lives **OUTSIDE** Workbench v6. It consumes Runtime evidence (RuntimeEvent stream) and builds its own authority.

## Required Evidence for Future Boundary Decisions

Before any future ADR to extend Workbench v6 toward Agent Manager OS:
1. ✅ Tier A evidence from second consumer (per ADR-009)
2. ✅ Multi-round Architecture Review (currently 0/3)
3. ✅ Explicit user authorization

Until then, this file remains **placeholder only** (NOT design).

## Position in 5-Layer Model

```
Workbench v6 Foundation (frozen)
    ↓
[Future: Agent Manager OS = separate product]
    ↓
Future product layer (not yet defined)
```