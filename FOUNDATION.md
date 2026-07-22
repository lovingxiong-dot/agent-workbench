# Foundation

> **CENTRE Ecosystem Shared Ancestor** — Repository Governance v1.0
> **Status**: FROZEN (identity), PROPOSAL (contract)
> **Audience**: All contributors, AI agents, reviewers
> **Priority**: Read before modifying any shared capability

---

## What This Document Defines

`FOUNDATION.md` defines the **shared ancestor** of all products in the CENTRE ecosystem.

It answers one question: when building a new product (Workbench v6, Agent Manager OS, etc.), what can be reused without forking?

The Foundation is not a product. It is the common ground that all products share.

---

## CENTRE Ecosystem

```
                        CENTRE / AOS
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Protocol        Runtime        Gateway
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
        Workbench v6              Agent Manager OS
              │                             │
     Agent Workspace           Governance & Control Plane
     Single Agent              Multi-Agent
     Workflow Runner           Routing & Federation
     Chat UI                   Dashboard UI
```

---

## Three-Tier State Model

To prevent premature contract freeze, the Foundation has three distinct states:

### Frozen

Constitution-level decisions that are stable and authoritative.

| Asset | Reference |
|-------|-----------|
| Repository Governance | `AGENT_ENTRY.md`, `ROOT_INDEX.md`, `PROJECT_DECLARATION.md`, `PROJECT_STATE.md`, `ARCHITECTURE.md` |
| Identity Separation | `FOUNDATION.md`, `ADR-005 Project Identity Boundary` |
| Workbench v6 Identity Freeze | `ADR-006 Workbench v6 Identity Freeze` |
| AISE Governance Rules | `archive/centaur-policy` (CENTRE AOS constitution) |
| CENTRE Kernel Boundary | Runtime Kernel frozen zone |
| Runtime Authority Model | Runtime Kernel ownership rules |

### Proposal (Candidate Contract)

Interfaces under design. May change without major version bump. **Non-binding.**

| Asset | Reference |
|-------|-----------|
| Foundation Contract v0.5 | `presentation/protocols/foundation/` + `ADR-007` |
| Data Schema (AgentIdentity / AgentSession / WorkflowState) | `foundation/data.py` (PROPOSAL) |
| Provider Model (Registry vs Enum) | `foundation/gateway.py` (PROPOSAL) |
| AgentRuntime Contract | `foundation/runtime.py` (PROPOSAL) |
| Gateway Contract | `foundation/gateway.py` (PROPOSAL) |

**Validation Gate**: [ADR-008 Runtime Closure Validation](./.project/decisions/ADR-008-runtime-closure-validation.md) must pass before any proposal can be frozen.

### Experimental

Work-in-progress. May change at any time. No contract guarantee.

| Asset | Reference |
|-------|-----------|
| Workbench v6 Renderer | `presentation/renderers/v6_ui/` (in migration) |
| Chat Workspace | `v6/ui/chat_area.py`, `v6/ui/chat_scene.py` |
| Provider Integration | `agent_workbench/services/` |
| Memory Pipeline | `agent_workbench/runtime/modules/memory_module.py` |
| Workflow Engine | `agent_workbench/runtime/capability/` |

---

## Shared Ancestor vs Product-Specific

| Capability | Shared Ancestor | Workbench v6 | Agent Manager OS |
|------------|:---------------:|:------------:|:----------------:|
| **Protocol** (InteractionCommand, InteractionEvent, ShellContract) | ✅ | ✅ | ✅ |
| **Runtime** (Agent lifecycle, Capability, Decision, Orchestrator) | ✅ | ✅ | ✅ |
| **Event Bus** (RuntimeEvent → InteractionEvent mapping) | ✅ | ✅ | ✅ |
| **Data Contract** (ViewModel, ShellContract, NavigationGroup) | ✅ | ✅ | ✅ |
| **Gateway** (Provider registry, Model routing, API dispatch) | ✅ | ✅ | ✅ |
| **Workflow Engine** (Planner, Task, Chain) | ✅ | ✅ | Can invoke, not own UI |
| **Chat UI** (ChatArea, LeftPanel, InputArea) | ❌ | ✅ | ❌ |
| **Workspace UI** (Welcome, Trace, Provider) | ❌ | ✅ | ❌ |
| **Dashboard UI** (Agent registry, Runtime monitor, Federation) | ❌ | ❌ | ✅ |
| **Agent Registry** (Multi-agent identity, Permission, Routing) | ❌ | ❌ | ✅ |
| **Federation Gateway** (Cross-runtime scheduling) | ❌ | ❌ | ✅ |

---

## Rules

### Rule 1: Shared Ancestor is Read-Only for Products

Products (Workbench v6, Agent Manager OS) can consume the shared ancestor. They cannot modify it.

Shared ancestor modification requires:
1. Architecture Review
2. Impact assessment on all products
3. ADR approval

### Rule 2: Products Do Not Fork Ancestors

When building Agent Manager OS, do not copy `runtime/` or `protocols/`. Reference them from the shared ancestor.

### Rule 3: Products Are Independent

Workbench v6 and Agent Manager OS do not share UI logic. They do not share widgets. They do not share layout.

They share only: Protocol, Runtime, Data Contract, Gateway.

### Rule 4: Product Boundaries Are Explicit

Any new file must declare which product it belongs to:
- `[Workbench v6]` — Agent workspace product
- `[Agent Manager OS]` — Governance & control plane product
- `[Foundation]` — Shared ancestor (requires Architecture Review to modify)

### Rule 5: Foundation Identity Is Frozen, Foundation Contract Is Proposal

The Foundation **identity** (what is shared) is frozen.

The Foundation **contract** (how is shared, exact symbol shapes) is proposal until validated by [ADR-008](./.project/decisions/ADR-008-runtime-closure-validation.md).

---

## Current Status

| Layer | Status | Location | Contract |
|-------|--------|----------|----------|
| Protocol | Active (Frozen) | `agent_workbench/presentation/protocols/interaction/` | InteractionCommand / InteractionEvent |
| Runtime | Active | `agent_workbench/runtime/` | (not yet Foundation-contract-bound — see ADR-008) |
| Event Bus | Active | `agent_workbench/runtime/interaction/mapper.py` | (not yet Foundation-contract-bound) |
| Data Contract | Active | `agent_workbench/presentation/shell/protocol.py` | (not yet merged with Foundation proposal) |
| Gateway | Active | `agent_workbench/services/` (7 providers) | (not yet Foundation-contract-bound) |
| Workflow Engine | Active | `agent_workbench/runtime/capability/` | (not yet Foundation-contract-bound) |
| Workbench v6 | Active (Experimental) | `agent_workbench/application/`, `v6/ui/` | [ADR-006 Identity Freeze](./.project/decisions/ADR-006-workbench-v6-identity-freeze.md) |
| Agent Manager OS | Future | Not yet in this repository | Not yet defined |

---

## Foundation Contract — Candidate (v0.5 PROPOSAL, Non-binding)

Per [ADR-007](./.project/decisions/ADR-007-foundation-contract-freeze-v1.0.md), the Foundation Contract symbols live at `presentation/protocols/foundation/` as **candidate contract**, not frozen contract.

**State**: Candidate (non-binding)
**Authority**: NONE
**Binding**: NON-BINDING
**Validation**: PENDING ([ADR-008 Runtime Closure Validation](./.project/decisions/ADR-008-runtime-closure-validation.md))
**Next Milestone**: Phase 2-D.2 Renderer Migration

Workbench v6 implementation is the source of truth until validation records close. The proposal introduces the **concept** (Runtime / Event / Data / Gateway are the right dimensions), but the **implementation details** are still under review.

---

## Roadmap

```
Phase 1: Complete Workbench v6 (Phase 2-D.x)
  → Prove: Agent + Workflow + Runtime + UI can run end-to-end
  → Validate four loops: Identity / Event / Provider / Data

Phase 2: Runtime Closure Validation (ADR-008)
  → Four loops must close before any Foundation Freeze

Phase 3: Foundation Contract v1.0 Freeze (ADR-009, future)
  → Only after ADR-008 validation records close

Phase 4: Agent Manager OS
  → Build on validated Foundation Contract

Phase 5: CENTRE Federation
  → Multi-runtime, multi-agent governance
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Workbench v6 Constitution |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | Mandatory Agent onboarding |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Agent construction rules |
| [ADR-005 Project Identity Boundary](./.project/decisions/ADR-005-project-identity-boundary.md) | Repository vs Product separation |
| [ADR-006 Workbench v6 Identity Freeze](./.project/decisions/ADR-006-workbench-v6-identity-freeze.md) | Workbench v6 scope freeze |
| [ADR-007 Foundation Contract v0.5](./.project/decisions/ADR-007-foundation-contract-freeze-v1.0.md) | Foundation Contract (proposal) |
| [ADR-008 Runtime Closure Validation](./.project/decisions/ADR-008-runtime-closure-validation.md) | Validation gate before Freeze |

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Foundation. Three-tier state model (Frozen / Proposal / Experimental). ADR-008 validation gate. |