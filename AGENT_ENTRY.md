# Agent Entry

> **Mandatory Onboarding** — Repository Governance v1.0
> **Status**: FROZEN
> **Audience**: AI Agents (Claude, Codex, Trae, etc.)
> **Priority**: Read before any operation

---

## Reading Order

Every AI Agent entering this repository MUST read these documents in order:

```
1. ROOT_INDEX.md
       ↓
2. PROJECT_DECLARATION.md
       ↓
3. PROJECT_STATE.md
       ↓
4. ARCHITECTURE.md
       ↓
5. Relevant Domain Docs
       ↓
6. Code
```

---

## Quick Reference (3 Minutes)

### What This Project Is

Agent Workbench OS — a CENTRE-governed AI Agent Runtime platform.

```
Interaction Protocol → Runtime → Presentation → Renderer → UI
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
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation (first read) |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Repository Constitution |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Construction rules |
| [.agent/architecture_rules.md](./agent_workbench/.agent/architecture_rules.md) | Quick reference card |

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial onboarding. Repository Governance v1.0. |