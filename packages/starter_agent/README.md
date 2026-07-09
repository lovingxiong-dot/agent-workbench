# Starter Agent

This is the minimal Agent Package template for Workbench OS 1.0.

It exists to validate the complete Agent Package lifecycle, not to be a useful agent.

## Files

- `manifest.json` — Package entry point and schema version.
- `metadata.json` — Identity, properties, statistics, and actions.
- `capabilities.json` — Capability declarations.
- `view_schema.json` — UI layout for Workbench.
- `runtime.json` — Runtime status and binding hints.
- `prompts/` — Optional prompt templates.
- `resources/` — Optional static assets.

## Lifecycle

1. Copy this folder into `packages/`.
2. Start Workbench OS.
3. Navigator should show "Starter Agent".
4. Click it → Workspace and Inspector render.
5. Click "Execute" → Runtime executes (Commit 12.4).
6. Delete this folder → Navigator entry disappears after refresh.

## Constraints

- No Qt imports.
- No Renderer registration.
- All UI is declared through `view_schema.json`.
