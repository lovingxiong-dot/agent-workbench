# Agent Architecture Rules

> **Status**: FROZEN — Phase 2-B.2
> **Priority**: 最高 — Agent 首次进入项目必须读取
> **Read Time**: 3 min

---

## Quick Reference Card

### Before Touching ANY File

```
1. Read ARCHITECTURE_BOUNDARY.md (project root)
2. Check which layer you're modifying
3. Check Frozen Zone status
4. Verify dependency direction is downward only
```

### Architecture (One-Line)

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

### Layer Rules

| Layer | Can Touch | Cannot Touch |
|-------|-----------|-------------|
| **Application** (`application/`) | WorkbenchController, v6/ui widgets, Renderer binding | WorkbenchUIController, UI behavior |
| **Renderer** (`presentation/renderers/v6_ui/`) | InteractionEvent, ShellContract, v6/ui Public API | Runtime Implementation, v6/ui private members |
| **v6/ui** (`v6/ui/`) | PySide6, Qt, theme constants | Any agent_workbench/ package |
| **Runtime** (`agent_workbench/runtime/`) | Internal Runtime modules | v6/ui, any UI framework |

### Frozen Zones

| Zone | Files | Rule |
|------|-------|------|
| Runtime Kernel | 19 files | Bug fixes only |
| v6/ui Foundation | 22 files | Visual refinement + Public API only |
| Shell Contract | 7 files | No modification |
| Metadata Contract | metadata/ | Additive only |

### Red Flags — STOP Immediately

- ✗ Importing `from agent_workbench` in `v6/ui/`
- ✗ Accessing `self._chat._scene` or any `._` member in Renderer
- ✗ Importing `WorkbenchUIController` in Application layer
- ✗ Adding `update_agent()` / `update_model()` / `update_session()` to ChatArea
- ✗ Treating `v6/ui` as the old `v6-agent` UI
- ✗ Importing upward (Runtime → v6/ui, v6/ui → Renderer, etc.)

### Key Documents

| Document | When to Read |
|----------|-------------|
| `ARCHITECTURE_BOUNDARY.md` | **First thing — always** |
| `v6/UI_FOUNDATION.md` | Before touching v6/ui |
| `PROJECT_BLUEPRINT.md` | For project overview |
| `docs/v6/architecture-boundaries.md` | For detailed boundary rules |
| `docs/v6/SPEC.md` | For UI signal contracts |

### Lineage — Do Not Confuse

| Artifact | What It Is | Status |
|----------|-----------|--------|
| `v6/ui/` | Pure UI Foundation | **ACTIVE** |
| `agent_workbench/ui/workbench/` | Legacy validation UI | **PRESERVED** |
| `v6-agent` branch | Deprecated architecture | **ARCHIVED** |