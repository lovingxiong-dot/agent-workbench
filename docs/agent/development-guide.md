# Agent Development Guide

> **Target reader**: AI Agent entering this repository for the first time.
> **Goal**: Understand the architecture in 5 minutes without reading commit history.

---

## Quick Start

1. Read `.agent-entry.json` — machine-readable project identity and boundaries
2. Read this file — human-readable architecture map
3. Read `docs/v6/architecture-boundaries.md` — detailed frozen zone rules

---

## Architecture (3 layers)

```
agent_workbench/          ← Product Layer (you work here)
        │
        │ depends on
        ▼
v6/                       ← Runtime Foundation Layer (FROZEN, do not touch)
        │
        │ replaced
        ▼
_archive/                 ← Pre-v6 legacy (do not scan)
```

---

## What You Can Modify

| Area | Path | Freedom |
|------|------|---------|
| Provider | `agent_workbench/services/*_provider.py` | Free |
| Tool | `agent_workbench/runtime/modules/tool_module.py` | Free |
| Skill | `agent_workbench/runtime/modules/skill_module.py` | Free |
| Workspace | `agent_workbench/ui/workbench/*_workspace.py` | Free |
| Workflow | `agent_workbench/runtime/modules/workflow_module.py` | Free |
| UI | `agent_workbench/ui/workbench/` | Free |
| Package | `packages/` | Free |

## What You Must NOT Touch

| Layer | Reason | Frozen Since |
|-------|--------|-------------|
| `v6/runtime/context.py` | RuntimeContext ABI | v6.9.6-foundation |
| `v6/runtime/task.py` | Task Contract | v6.9.2-alpha |
| `v6/runtime/orchestrator.py` | Orchestrator | v6.9.6-foundation |
| `v6/runtime/event_bus.py` | EventBus | v6.9.6-foundation |
| `agent_workbench/runtime/capability/` | Capability Contract | v6.9.6-foundation |
| `agent_workbench/runtime/decision/` | Decision ABI | v6.9.4-alpha |
| `agent_workbench/runtime/interaction/` | Interaction Boundary | v6.9.5-alpha |
| `agent_workbench/metadata/model.py` | Metadata Contract | v6.11.0-beta.4 |

---

## Key Rules

1. **Metadata First**: All Runtime Modules expose `metadata()` → `MetadataAdapter` → `PresentationModel` → UI. Never hardcode UI for a specific module.
2. **No Module Cross-Import**: Runtime Modules communicate via EventBus, Interface, or Registry. Never `import` another module directly.
3. **UI Does Not Own State**: Business state lives in Runtime. UI only holds `selection`, `focus`, `scroll`, `expanded`.
4. **WorkspaceHost Pattern**: Workspace is a container. All content is `WorkspaceItem`. Adding a new workspace type never requires modifying WorkspaceHost.
5. **Capability → Resource**: Capability = "what I can do". Resource = "what I can use". Python, Chrome, VS Code are Resources, not Capabilities.

---

## Entry Points

| Entry | File | Purpose |
|-------|------|---------|
| CLI | `agent_workbench/app.py` | `python -m agent_workbench --mode cli` |
| GUI | `agent_workbench/ui/main_window.py` | `python -m agent_workbench --mode gui` |
| EXE | `dist/AgentWorkbench/AgentWorkbench.exe` | PyInstaller build |

---

## Further Reading

- `docs/v6/architecture-boundaries.md` — complete frozen zone definitions
- `docs/v6/runtime-kernel-spec.md` — six-layer Runtime Kernel spec
- `docs/v6/product-contract.md` — Workbench OS 1.0 product contract
- `PROJECT_BLUEPRINT.md` — full project history and architecture constitution
- `PROJECT_LINEAGE.md` — version lineage and active product declaration
- `cleanup_manifest.md` — Pre-AISE Stabilization cleanup record