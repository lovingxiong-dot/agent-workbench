# Root Index

> **CENTRE Ecosystem Repository Router** — Repository Governance v1.0
> **Status**: FROZEN
> **Audience**: All contributors, AI agents, reviewers
> **Priority**: First read for any new participant

---

## What Is This Repository?

This repository currently contains **Workbench v6** — an Agent Workspace product inside the CENTRE ecosystem. Future products (Agent Manager OS) will live alongside it.

For the shared ancestor that defines common capabilities across all CENTRE products, read [FOUNDATION.md](./FOUNDATION.md).

```
CENTRE / AOS
    │
    ├── Workbench v6 (active)         ← Agent Workspace
    └── Agent Manager OS (future)     ← Governance Plane

Current architecture:
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

For full context, read [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md).

---

## New Here? Read This

```
1. ROOT_INDEX.md              ← Repository Router (this file — what is here)
2. FOUNDATION.md              ← Shared Ancestor (CENTRE ecosystem worldview)
3. AGENT_ENTRY.md             ← AI Agent onboarding + action rules
4. PROJECT_DECLARATION.md     ← Workbench v6 Constitution
5. PROJECT_STATE.md           ← Current development snapshot
6. ARCHITECTURE.md            ← Architecture navigation
7. Relevant Domain Docs       ← Deep dive into your area
8. Code                       ← Start working
```

The reading order follows cognitive progression: **Map → Worldview → Rules → Constitution → State → Architecture → Domain → Code**.

---

## Repository Map

```
agent_workbench/
├── FOUNDATION.md              ← Shared ancestor (CENTRE ecosystem)
├── PROJECT_DECLARATION.md     ← Workbench v6 Constitution
├── PROJECT_STATE.md           ← Current development snapshot
├── AGENT_ENTRY.md             ← Mandatory Agent onboarding
├── ARCHITECTURE.md            ← Architecture navigation
├── ROOT_INDEX.md              ← This file
│
├── README.md                  ← Project README
├── PROJECT_BLUEPRINT.md       ← Project overview, frozen zones
├── ARCHITECTURE_BOUNDARY.md   ← Agent construction rules
├── PROJECT_LINEAGE.md         ← V5/V6 identity map
├── CHANGELOG.md               ← Version history
│
├─── Source Code ─────────────────────────────────────
│
├── agent_workbench/
│   ├── application/           ← Startup, wiring, lifecycle
│   ├── presentation/          ← Renderer, registry, protocols, shell
│   │   ├── protocols/         ← Interaction Protocol (Contract)
│   │   ├── renderers/         ← Renderer implementations
│   │   ├── shell/             ← Shell Contract + Pipeline
│   │   └── runtime.py         ← PresentationRuntime
│   ├── runtime/               ← Runtime Kernel (Frozen)
│   │   ├── capability/        ← Capability execution
│   │   ├── decision/          ← Decision layer
│   │   ├── interaction/       ← Interaction boundary
│   │   ├── modules/           ← Runtime modules
│   │   └── manager/           ← Runtime manager
│   ├── services/              ← Provider integrations
│   ├── ui/                    ← Legacy UI (deprecated)
│   │   └── workbench/         ← Old Workbench UI (32 files)
│   ├── conversation/          ← Conversation service
│   ├── engines/               ← LLM/Tool engines
│   ├── metadata/              ← Metadata system
│   ├── package/               ← Agent package system
│   └── app.py                 ← Entry point
│
├── v6/
│   ├── ui/                    ← Pure UI Foundation (22 files, Frozen)
│   ├── runtime/               ← V6 Runtime (old v6-agent, deprecated)
│   └── UI_FOUNDATION.md       ← v6/ui freeze contract
│
├─── Documentation ───────────────────────────────────
│
├── docs/
│   ├── ARCHITECTURE.md        ← Full architecture overview
│   ├── getting-started.md     ← Getting started guide
│   ├── engineering-workflow.md ← Engineering workflow
│   └── v6/                    ← V6-specific docs
│       ├── ROADMAP.md
│       ├── SPEC.md
│       ├── architecture-boundaries.md
│       ├── runtime-kernel-spec.md
│       └── ...
│
├─── Governance ──────────────────────────────────────
│
├── .project/
│   ├── decisions/             ← Architecture Decision Records
│   │   ├── ADR-001-shell-contract-freeze.md
│   │   ├── ADR-002-phase-2c-presentation-rfc.md
│   │   └── ADR-003-phase-2d-migration-audit.md
│   ├── handoff/               ← Agent handoff context
│   ├── architecture/          ← Architecture reports
│   └── contracts/             ← Repository contracts
│
├─── Other ───────────────────────────────────────────
│
├── packages/                  ← Agent packages (3 agents)
├── tests/                     ← Test suite
├── scripts/                   ← Build/utility scripts
├── config/                    ← Configuration
├── storage/                   ← Session storage
└── _archive/                  ← Archived legacy code
```

---

## Quick Links

### For AI Agents

- [AGENT_ENTRY.md](./AGENT_ENTRY.md) — **Start here**
- [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) — Construction rules
- [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) — v6/ui freeze contract

### For Developers

- [README.md](./README.md) — Project README
- [PROJECT_STATE.md](./PROJECT_STATE.md) — Current state
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — Full architecture
- [docs/getting-started.md](./docs/getting-started.md) — Getting started

### For Reviewers

- [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) — Constitution
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Architecture navigation
- [.project/decisions/](./.project/decisions/) — ADRs

---

## Quick Commands

```bash
# CLI mode
python -m agent_workbench.app --mode cli

# GUI mode (legacy Workbench UI)
python -m agent_workbench.app --mode gui

# GUI mode (v6/ui Pure UI Foundation)
python -m agent_workbench.app --mode gui-v6

# Run tests
python -m pytest tests/ -x -q

# Multi Renderer Proof
python -m agent_workbench.presentation.renderers.multi_renderer_proof
```

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial navigation. Repository Governance v1.0. |