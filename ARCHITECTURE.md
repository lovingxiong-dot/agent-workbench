# Architecture

> **Navigation Layer** — Repository Governance v1.0
> **Status**: FROZEN
> **Audience**: Contributors, AI agents, reviewers
> **Rule**: This file is a navigation index. It does not duplicate architecture documents.

---

## Architecture Overview

Current architecture: **v6.14.0-alpha** — Presentation Boundary Freeze.

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

For the full architecture document, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

---

## Layer Map

```
Application Layer
  → [application/](./agent_workbench/application/)
  → Owns: startup, wiring, lifecycle
  → Doc: [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) § Application Layer

Presentation Layer
  → [presentation/](./agent_workbench/presentation/)
  → Owns: renderer lifecycle, event dispatch, shell state sync
  → Key files:
    - [PresentationRuntime](./agent_workbench/presentation/runtime.py)
    - [RendererRegistry](./agent_workbench/presentation/renderers/registry.py)
    - [V6UIRenderer](./agent_workbench/presentation/renderers/v6_ui/renderer.py)

Protocols Layer
  → [presentation/protocols/](./agent_workbench/presentation/protocols/)
  → Owns: communication contracts
  → Key files:
    - [InteractionCommand](./agent_workbench/presentation/protocols/interaction/command.py)
    - [InteractionEvent](./agent_workbench/presentation/protocols/interaction/event.py)
    - [UIEventRenderer](./agent_workbench/presentation/protocols/interaction/renderer.py)

Runtime Layer
  → [runtime/](./agent_workbench/runtime/)
  → Owns: execution, agent lifecycle, capability
  → Doc: [docs/v6/runtime-kernel-spec.md](./docs/v6/runtime-kernel-spec.md)

UI Foundation
  → [v6/ui/](./v6/ui/) (22 files)
  → Owns: visual interaction, zero agent_workbench dependency
  → Doc: [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md)
```

---

## Architecture Documents

### Primary (Read First)

| Document | Purpose |
|----------|---------|
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Repository Constitution |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Agent construction rules |
| [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) | Project overview, frozen zones |
| [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) | v6/ui freeze contract |

### Deep Architecture

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Full architecture overview |
| [docs/v6/architecture-boundaries.md](./docs/v6/architecture-boundaries.md) | Detailed boundary spec |
| [docs/v6/runtime-kernel-spec.md](./docs/v6/runtime-kernel-spec.md) | Runtime kernel specification |
| [docs/v6/runtime-glossary.md](./docs/v6/runtime-glossary.md) | Runtime terminology |
| [docs/v6/SPEC.md](./docs/v6/SPEC.md) | UI signal contract |
| [docs/v6/ROADMAP.md](./docs/v6/ROADMAP.md) | Development roadmap |

### Architecture Decisions

| Document | Decision |
|----------|----------|
| [.project/decisions/ADR-001-shell-contract-freeze.md](./.project/decisions/ADR-001-shell-contract-freeze.md) | Shell Contract ADR |
| [.project/decisions/ADR-002-phase-2c-presentation-rfc.md](./.project/decisions/ADR-002-phase-2c-presentation-rfc.md) | Phase 2-C Presentation RFC |
| [.project/decisions/ADR-003-phase-2d-migration-audit.md](./.project/decisions/ADR-003-phase-2d-migration-audit.md) | Phase 2-D Migration Audit |

### Architecture Reports

| Document | Report |
|----------|--------|
| [.project/architecture/v6.13-freeze-report.md](./.project/architecture/v6.13-freeze-report.md) | v6.13 Architecture Freeze |
| [docs/v6/freeze-verification-report.md](./docs/v6/freeze-verification-report.md) | Freeze verification |
| [docs/v6/shell-integration-architecture-report.md](./docs/v6/shell-integration-architecture-report.md) | Shell integration |
| [docs/v6/shell-adapter-architecture.md](./docs/v6/shell-adapter-architecture.md) | Shell adapter |

---

## Key Architecture Rules

1. **v6/ui is frozen** — no Runtime concepts, no agent_workbench imports
2. **Renderer layer maps data to UI** — never touches v6/ui private members
3. **Application layer uses WorkbenchController** — never WorkbenchUIController
4. **Single Active Renderer** — only one renderer active at a time
5. **Documentation defines architecture** — code implements documentation

For full rules, see [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md).

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial navigation layer. Repository Governance v1.0. |