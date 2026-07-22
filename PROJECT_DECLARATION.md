# Project Declaration

> **Repository Constitution** — Repository Governance v1.0
> **Status**: FROZEN
> **Audience**: All contributors, AI agents, reviewers
> **Priority**: First read for any new participant

---

## Vision

**Agent Workbench OS** is a CENTRE-governed AI Agent Runtime platform.

It is not a chatbot. It is not an IDE. It is an **Agent Operating System** — a runtime kernel that hosts multiple AI agents, manages their capabilities, and presents their output through a replaceable UI shell.

The goal: a single Runtime that can power Desktop, Web, CLI, and Mobile interfaces without changing the agent logic.

---

## Philosophy

### Documentation Defines Architecture

Architecture is not what the code happens to do. Architecture is what the documentation declares.

Code must implement architecture. Architecture must not be reverse-engineered from code.

When code and documentation disagree, documentation is correct until explicitly revised.

### Contract First

Every boundary is a contract. Every contract is explicit.

```
Protocol Layer
    ↓
Runtime Layer
    ↓
Presentation Layer
    ↓
Governance Layer
```

Contracts define interfaces. Layers implement contracts. Governance enforces rules.

### Repository Before Implementation

The repository structure is the first architecture document. File placement is a design decision. Import paths are boundary declarations.

Before adding code, ask: "Does this belong in this layer?"

---

## Design Principles

| # | Principle | Meaning |
|---|-----------|---------|
| P1 | **Runtime is the Kernel** | Agent logic, capability execution, and decision flow live in Runtime. UI is a shell. |
| P2 | **UI is Replaceable** | v6/ui is a Pure UI Foundation. It can be replaced with Web, CLI, or Mobile without changing Runtime. |
| P3 | **Protocols are Boundaries** | Communication between layers goes through protocols. No layer imports the implementation of another. |
| P4 | **Presentation is Renderer-Agnostic** | PresentationRuntime does not know what UI technology is active. |
| P5 | **Single Active Renderer** | Only one renderer can be active at a time. |
| P6 | **Documentation First** | Architecture decisions are written before code is changed. |
| P7 | **Frozen Zones are Absolute** | Marked Frozen Zones cannot be modified without an Architecture Review. |

---

## Repository Scope

### In Scope

- CENTRE Runtime Kernel (agent lifecycle, capability execution, decision flow)
- Interaction Protocol (Runtime ↔ Presentation communication)
- Presentation Runtime (lifecycle, event dispatch, renderer registry)
- v6/ui Pure UI Foundation (visual components, zero agent_workbench dependency)
- Application Layer (startup, wiring, lifecycle)
- Agent packages (Personal, Coding, Research)
- Provider integrations (OpenAI, DeepSeek, Claude, Gemini, Qwen, Kimi)
- CLI and GUI entry points

### Out of Scope

- Production deployment infrastructure
- Authentication / authorization
- Multi-user server
- SaaS platform
- IDE plugin development
- Old V5 architecture (frozen in archive)

---

## Current Mission

**Phase 2-D**: Complete the migration from Application-Centric UI to Runtime-First Presentation-Agnostic architecture.

The old architecture:
```
UI → Controller → Runtime
```

The new architecture:
```
Interaction Protocol → Runtime → Presentation → Renderer → UI
```

---

## Non-Goals

- Do not build a web application (yet)
- Do not support legacy V5 workflows
- Do not add Runtime concepts to the UI layer
- Do not add UI concepts to the Runtime layer
- Do not bypass the Renderer layer when connecting UI to Runtime

---

## Architecture Boundary

```
┌─────────────────────────────────────────┐
│              Governance                 │
│  (.project/decisions/, ADRs, rules)     │
├─────────────────────────────────────────┤
│           Application                   │
│  (startup, wiring, lifecycle)           │
├─────────────────────────────────────────┤
│          Presentation                   │
│  ┌───────────────────────────────────┐  │
│  │    PresentationRuntime            │  │
│  │    RendererRegistry               │  │
│  │    Renderers (Qt, CLI, Web...)    │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│            Protocols                     │
│  (InteractionCommand, InteractionEvent,  │
│   ShellContract, RendererProtocol)       │
├─────────────────────────────────────────┤
│             Runtime                      │
│  (Kernel: Agent, Capability, Decision,   │
│   Orchestrator, Modules, Engines)        │
├─────────────────────────────────────────┤
│            Foundation                    │
│  (v6/ui — Pure UI, zero Runtime deps)    │
└─────────────────────────────────────────┘
```

### Frozen Zones

| Zone | Files | Rule |
|------|-------|------|
| Runtime Kernel | `runtime/` 19 files | No modification without Architecture Review |
| v6/ui Foundation | `v6/ui/` 22 files | Visual refinement only. No Runtime concepts. |
| Shell Contract | `presentation/shell/protocol.py` | Frozen |
| Interaction Protocol | `presentation/protocols/` | Frozen |
| v6/ui Public API | `v6/ui/chat_area.py` | Only UI Capability APIs allowed |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | Mandatory Agent onboarding |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) | Project overview and blueprints |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Agent construction rules |
| [PROJECT_LINEAGE.md](./PROJECT_LINEAGE.md) | V5/V6 identity map |
| [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) | v6/ui freeze contract |

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Constitution. Repository Governance v1.0. |