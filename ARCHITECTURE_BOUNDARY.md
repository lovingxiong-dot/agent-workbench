# Architecture Boundary — Agent Construction Rules

> **Status**: FROZEN — Phase 2-B.1
> **Priority**: 最高 — Agent 首次进入项目必须读取
> **Audience**: AI Agents, Contributors, Developers
> **Scope**: 项目全局

---

## Purpose

This document defines the **construction rules** for any Agent or developer entering the Agent Workbench OS project. It prevents architecture regression by making boundaries explicit.

---

## Quick Reference: "Before You Touch Anything"

### 1. Determine Which Layer You're Modifying

```
Application Layer (application/)
  → startup, wiring, lifecycle
  → Can touch: WorkbenchController, v6/ui widgets, Renderer binding
  → Cannot: own UI behavior, own Renderer logic

Renderer Layer (presentation/renderers/)
  → data→UI mapping, event→UI method calls
  → Can touch: InteractionEvent, ShellContract, v6/ui Public API
  → Cannot: import Runtime Implementation, touch v6/ui private members

v6/ui Foundation (v6/ui/)
  → visual system, layout, interaction widgets
  → Can touch: PySide6, Qt, theme constants only
  → Cannot: import anything from agent_workbench/

Runtime Layer (agent_workbench/runtime/)
  → execution, agent lifecycle, capability
  → Can touch: internal Runtime modules
  → Cannot: know v6/ui or any UI framework exists
```

### 2. Check Frozen Zones Before Modifying

| Frozen Zone | Files | Rule |
|-------------|-------|------|
| Runtime Kernel | `runtime/capability/`, `runtime/interaction/`, `runtime/config_store.py`, `runtime/manager/decision_manager.py`, `package/loader.py`, `package/registry.py` | Bug fixes only. No new features. |
| Shell Contract | `presentation/shell/` (7 files) | No modification. Add new Renderer instead. |
| v6/ui Foundation | `v6/ui/` (22 files) | Visual refinement + Public API additions only. No Runtime concepts. |
| Metadata Contract | `agent_workbench/metadata/` | Additive changes only. No breaking changes. |

### 3. Follow the Dependency Direction

```
Runtime → Interaction Contract → Renderer → v6/ui → Qt
```

**Only downward. Never upward.** If you find yourself importing upward, you're in the wrong layer.

---

## Layer Ownership

### Application Layer

**Owns**: startup, dependency wiring, lifecycle
**Does NOT own**: UI behavior, Renderer logic, Session management, Agent management

```python
# Allowed
from agent_workbench.controller import WorkbenchController
controller = WorkbenchController()
controller.start()

# Forbidden
from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController
```

### Renderer Layer

**Owns**: data→UI mapping, event→UI method calls
**Does NOT own**: Runtime Implementation, UI private members

**Allowed imports**:
- `agent_workbench.runtime.interaction.event` (Interaction Contract)
- `agent_workbench.presentation.shell.protocol` (Shell Contract)
- `v6.ui.*` (Public API only)

**Forbidden imports**:
- `agent_workbench.runtime.engine`
- `agent_workbench.runtime.executor`
- `agent_workbench.runtime.session`
- `agent_workbench.runtime.llm`
- `agent_workbench.runtime.tool`
- `agent_workbench.ui.workbench_ui_controller`

**Forbidden patterns**:
```python
# ✗ Private member access
self._chat._scene.clear_chat()

# ✓ Public API
self._chat.reset_workspace()
```

### v6/ui Foundation

**Owns**: visual system, layout, interaction widgets
**Does NOT own**: Runtime, Agent, Session, Model, LLM, Tool

**Verification**: `grep -r "from agent_workbench" v6/ui/` must return empty.

**Allowed additions**:
- Public API methods that expose existing internal capabilities
- Example: `ChatArea.reset_workspace()` → delegates to `self._scene.clear_chat()`

**Forbidden additions**:
- Methods with Runtime concepts: `update_agent()`, `update_model()`, `update_session()`
- Business logic inside widgets
- New widgets that don't belong to the Presentation Foundation

### Runtime Layer

**Owns**: execution, agent lifecycle, capability
**Does NOT own**: UI, v6/ui, any Widget

**Rule**: Runtime must never import or reference `v6/ui`, `PySide6`, or any UI framework.

---

## Artifact Lineage — Do Not Confuse

| Artifact | What It Is | What It Is NOT |
|----------|-----------|----------------|
| `v6/ui/` (22 files) | Pure UI Foundation — extracted from early Workbench | NOT the deprecated v6-agent |
| `agent_workbench/ui/workbench/` (32 files) | Legacy architecture validation UI | NOT the main product UI |
| `v6-agent` branch | Deprecated application-centric architecture | NOT the current development line |

The old architecture (DEPRECATED):

```
UI → Controller → Agent Runtime → LLM
```

The current architecture (ACTIVE):

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

---

## Modification Checklist

Before modifying any file, Agent MUST verify:

1. **Which layer am I in?** (Application / Renderer / v6/ui / Runtime)
2. **Is this a Frozen Zone?** (check Frozen Zone table above)
3. **Does this change require Runtime knowledge?** (if yes → wrong layer)
4. **Can this be solved in the Renderer?** (if yes → do it there, not in v6/ui)
5. **Am I importing upward?** (if yes → stop, reassign to correct layer)

### Before Modifying v6/ui

```
□ Is this a visual refinement? (colors, spacing, accessibility)
  → YES: proceed
  → NO: continue

□ Is this a UI Capability API addition?
  → YES: does it expose an existing internal capability? (no new Runtime concepts?)
    → YES: proceed
    → NO: stop — belongs in Renderer
  → NO: continue

□ Does this add Runtime knowledge to v6/ui?
  → YES: STOP — this is architecture pollution
  → NO: proceed with caution
```

### Before Modifying Runtime

```
□ Is this a bug fix?
  → YES: proceed
  → NO: does it go through the frozen Capability Runtime Contract?
    → YES: proceed with architecture review
    → NO: STOP — new Runtime capabilities require architecture review
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) | Project overview, architecture, frozen zones |
| [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) | v6/ui formal freeze contract |
| [docs/v6/architecture-boundaries.md](./docs/v6/architecture-boundaries.md) | Detailed architecture boundary spec |
| [docs/v6/SPEC.md](./docs/v6/SPEC.md) | UI signal contract, module constraints |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Historical architecture overview |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial creation. Phase 2-B.1 Architecture Declaration Sync. |