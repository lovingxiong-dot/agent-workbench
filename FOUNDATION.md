# Foundation

> **CENTRE Ecosystem Shared Ancestor** — Repository Governance v1.0
> **Status**: FROZEN
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

---

## Current Status

| Layer | Status | Location | Contract |
|-------|--------|----------|----------|
| Protocol | Active | `agent_workbench/presentation/protocols/interaction/` | InteractionCommand / InteractionEvent |
| Runtime | Active | `agent_workbench/runtime/` | [ADR-007 Foundation Contract v0.5 (PROPOSAL)](./.project/decisions/ADR-007-foundation-contract-freeze-v1.0.md) |
| Event Bus | Active | `agent_workbench/runtime/interaction/mapper.py` | (not yet Foundation-contract-bound) |
| Data Contract | Active | `agent_workbench/presentation/shell/protocol.py` | (not yet merged with Foundation proposal) |
| Gateway | Active | `agent_workbench/services/` (7 providers) | (not yet Foundation-contract-bound) |
| Workflow Engine | Active | `agent_workbench/runtime/capability/` | (not yet Foundation-contract-bound) |
| Workbench v6 | Active | `agent_workbench/application/`, `v6/ui/` | [ADR-006 Identity Freeze](./.project/decisions/ADR-006-workbench-v6-identity-freeze.md) |
| Agent Manager OS | Future | Not yet in this repository | Not yet defined |

---

## Foundation Contract — Proposal v0.5 (NOT Frozen)

Per [ADR-007](./.project/decisions/ADR-007-foundation-contract-freeze-v1.0.md), the Foundation Contract symbols live at `presentation/protocols/foundation/` as **proposal**, not frozen contract.

**Status: PROPOSAL — May change without major version bump.**

Why proposal (not frozen):
- Workbench v6 Runtime does not yet implement these symbols
- Real Renderer behavior is not yet validated against Gateway interface
- Data Contract duplicates with `shell/protocol.py` not yet resolved
- Provider enumeration has not been validated against real Provider needs

**When will it become v1.0 Frozen?**
- After Workbench v6 Runtime implements `AgentRuntime`
- After Renderer consumes `Gateway`
- After Data Contract duplication resolved
- After Provider enumeration validated

The proposal introduces the **concept** (Runtime / Event / Data / Gateway are the right dimensions), but the **implementation details** are still under review.

---

## Roadmap

```
Phase 1: Complete Workbench v6
  → Prove: Agent + Workflow + Runtime + UI can run end-to-end

Phase 2: Abstract Data Contract
  → Freeze shared ancestor boundaries

Phase 3: Establish Agent Manager OS
  → Build on shared ancestor, not on Workbench fork

Phase 4: CENTRE Federation
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

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Foundation. CENTRE Ecosystem shared ancestor definition. |