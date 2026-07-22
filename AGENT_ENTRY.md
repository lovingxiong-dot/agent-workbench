# Agent Entry

> **Mandatory Onboarding** — Repository Governance v1.0
> **Status**: FROZEN
> **Audience**: AI Agents (Claude, Codex, Trae, etc.)
> **Priority**: Read before any operation

---

## Reading Order

Every AI Agent entering this repository MUST read these documents in order:

```
1. ROOT_INDEX.md            ← Repository Router (what is here)
       ↓
2. FOUNDATION.md            ← Shared Ancestor (worldview)
       ↓
3. AGENT_ENTRY.md           ← Onboarding + Action Rules
       ↓
4. PROJECT_DECLARATION.md   ← Workbench v6 Constitution
       ↓
5. PROJECT_STATE.md         ← Current development snapshot
       ↓
6. ARCHITECTURE.md          ← Architecture navigation
       ↓
7. Relevant Domain Docs
       ↓
8. Code
```

The reading order follows cognitive progression: **Map → Worldview → Rules → Constitution → State → Architecture → Domain → Code**.

---

## Before Any Modification — Identify Your Target System

Every modification MUST declare which system it targets. Check before you touch:

```
Modification Target Checklist:

[ ] FOUNDATION (Shared Ancestor) — Protocol, Runtime, Data Contract, Gateway
    → Requires Architecture Review before any change

[ ] Workbench v6 — Agent Workspace, Chat UI, Workflow
    → This is the current active product

[ ] Agent Manager OS — Governance, Dashboard, Federation
    → Future product. Not yet in this repository.

[ ] Documentation Only — No code changes
```

**Rule**: You cannot modify one target system while thinking you're modifying another.

---

## Quick Reference (3 Minutes)

### What This Repository Contains

```
CENTRE / AOS (Shared Ancestor)
    │
    ├── Workbench v6 (active)         ← Agent Workspace
    └── Agent Manager OS (future)     ← Governance Plane

For shared ancestor definition, see FOUNDATION.md.
```

### What You Must NOT Do

| Rule | Reason |
|------|--------|
| Never redesign UI without Architecture Review | v6/ui is frozen |
| Never modify Runtime Boundary without Protocol Review | Contracts are frozen |
| Never add Runtime concepts to v6/ui | Pure UI Foundation |
| Never add UI concepts to Runtime | Kernel is UI-agnostic |
| Never bypass the Renderer layer | Renderer is the only UI bridge |
| Never import `WorkbenchUIController` in new code | Deprecated |
| Never import `v6.runtime.*` (old v6-agent) in new code | Deprecated |
| Never modify Frozen Zones | See [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) |

### What You MUST Do

| Rule | Meaning |
|------|---------|
| Documentation first | Write the decision before changing code |
| Contract first | Define the protocol before implementing |
| Layer check | Verify which layer your change belongs to |
| Frozen Zone check | Verify the zone is not frozen |
| Dependency direction | Only downward in the layer stack |
| Audit your imports | No `from agent_workbench` in v6/ui |

---

## Layer Quick Reference

```
Application Layer
  → startup, wiring, lifecycle
  → Can touch: WorkbenchController, v6/ui widgets, Renderer binding
  → Cannot: own UI behavior, own Renderer logic

Renderer Layer
  → data→UI mapping, event→UI method calls
  → Can touch: InteractionEvent, ShellContract, v6/ui Public API
  → Cannot: import Runtime Implementation, touch v6/ui private members

Protocols Layer
  → communication contracts only
  → Can touch: Python dataclasses, Protocol types
  → Cannot: import Runtime, import UI frameworks

Runtime Layer
  → execution, agent lifecycle, capability
  → Can touch: Modules, Engines, Decision, Orchestrator
  → Cannot: import PySide6, import v6/ui

UI Foundation (v6/ui)
  → visual interaction only
  → Can touch: PySide6, v6.ui.*
  → Cannot: import agent_workbench, import Runtime
```

---

## Before Modifying Any File

1. Read [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) — construction rules
2. Check which layer you're modifying
3. Check Frozen Zone status in [PROJECT_STATE.md](./PROJECT_STATE.md)
4. Verify dependency direction is downward only
5. If modifying v6/ui: read [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) first

---

## Before Creating a New File

1. Determine which layer it belongs to
2. Check [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) for scope
3. Verify it doesn't duplicate existing functionality
4. Verify it doesn't violate dependency direction
5. Add documentation reference in the appropriate index

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [FOUNDATION.md](./FOUNDATION.md) | **Shared ancestor — read first** |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Workbench v6 Constitution |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Construction rules |
| [.agent/architecture_rules.md](./agent_workbench/.agent/architecture_rules.md) | Quick reference card |

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial onboarding. Repository Governance v1.0. |