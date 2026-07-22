# AI Agent Workbench

> **Stable line: `main` (v6.12.0-beta.15) | Development line: `v6-agent` (v6.14.0-alpha)**
>
> V6 is a ground-up rewrite of the Agent Runtime platform. It uses `RuntimeContext` as the single public protocol and treats Agent capabilities as first-class Runtime objects.
>
> V5 and earlier are frozen in Git history (`archive/*`) and no longer maintained in the workspace.

---

## Architecture Status (v6.14.0-alpha)

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

- **v6/ui** (22 files) is the frozen Pure UI Foundation — NOT the deprecated v6-agent
- **Renderer** layer (`presentation/renderers/v6_ui/`) maps data to UI, never touches v6/ui private members
- **Application** layer (`application/`) uses `WorkbenchController`, NOT `WorkbenchUIController`
- Read [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) before modifying any file

---

## For AI Agents — Start Here

**Before any operation, read these documents in order:**

1. [AGENT_ENTRY.md](./AGENT_ENTRY.md) — **Mandatory onboarding (Repository Governance v1.0)**
2. [ROOT_INDEX.md](./ROOT_INDEX.md) — Repository navigation
3. [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) — Repository Constitution
4. [PROJECT_STATE.md](./PROJECT_STATE.md) — Current development snapshot
5. [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) — Construction rules
6. [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) — v6/ui freeze contract
7. [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) — Project overview and frozen zones

Governance center: [`lovingxiong-dot/agent-governance`](https://github.com/lovingxiong-dot/agent-governance)

---

## Branch Strategy

```
main          ← Stable release line (always compilable, runnable, releasable)
  └── v6-agent ← Active development (all feature/fix branches merge here)
        ├── feature/*
        ├── fix/*
        └── experiment/*

archive/v3, v4, v5, v6-core, v6-service, v6-dev  ← Frozen version snapshots
```

**Rules:**
- NEVER commit directly to `main`
- All changes go through `v6-agent`
- `trae/*` branches are temporary — merge to `v6-agent` only, then delete
- Use `--no-ff` merge to preserve complete commit history
- Tests must pass before any merge

---

## Tech Stack

`Python 3.14` · `PySide6` · `SQLite` · `YAML` · `PyInstaller`

---

## Quick Start

```powershell
cd F:\Agent\agent_workbench
venv\Scripts\Activate.ps1
python main.py
```

Or double-click `scripts/start.bat`.

### First-Time Setup

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

---

## Run Tests

```powershell
venv\Scripts\Activate.ps1
pytest
```

Current status: **575/575 passed**.

---

## Architecture Navigation

| Document | Purpose | Read Time |
|---|---|---|
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | **Mandatory Agent onboarding — MUST read first** | 5 min |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | **Repository navigation homepage** | 3 min |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | **Repository Constitution** | 10 min |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot | 5 min |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation layer | 5 min |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Agent construction rules | 10 min |
| [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) | v6/ui formal freeze contract | 10 min |
| [PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md) | Project lineage, architecture, frozen zones | 1 hour |
| [`docs/v6/architecture-boundaries.md`](./docs/v6/architecture-boundaries.md) | Detailed architecture boundary spec | 20 min |
| [`docs/v6/runtime-kernel-spec.md`](./docs/v6/runtime-kernel-spec.md) | Runtime Kernel: layers, ownership, dependency rules | 30 min |
| [`docs/v6/runtime-glossary.md`](./docs/v6/runtime-glossary.md) | Standard vocabulary for the platform | 15 min |
| [`docs/v6/repository-governance.md`](./docs/v6/repository-governance.md) | Repository structure and cleanliness rules | 10 min |
| [`docs/v6/repository-map.md`](./docs/v6/repository-map.md) | Auto-generated directory overview | 5 min |
| [`docs/v6/SPEC.md`](./docs/v6/SPEC.md) | UI component signal contracts | 30 min |
| [`PROJECT_LINEAGE.md`](./PROJECT_LINEAGE.md) | V5 / V6 identity map and branch rules | 15 min |
| [`CHANGELOG.md`](./CHANGELOG.md) | Version-by-version changelog | 20 min |

---

## Repository Structure

```text
agent_workbench/          # V6 Agent Workbench application
v6/                       # V6 Framework Core
core/                     # Shared core utilities
services/                 # Application services
workers/                  # Background workers
tools/                    # Tool implementations
scripts/                  # Repository and build scripts
tests/                    # Test suite
config/                   # Configuration templates and defaults
docs/                     # Documentation
main.py                   # Application entry point
agent_workbench.spec      # PyInstaller spec
```

For the full map, see [`docs/v6/repository-map.md`](./docs/v6/repository-map.md).

---

## Current Status

| Item | Value |
|---|---|
| Stable branch | `main` |
| Development branch | `v6-agent` |
| Current version | `v6.14.0-alpha` (Presentation Boundary Freeze) |
| Runtime Kernel | Frozen — Request / Planning / Task / Capability / Engine / Provider |
| v6/ui Foundation | Frozen — 22 files Pure UI Foundation |
| Presentation Boundary | Frozen — Phase 2-B.1 |
| Test status | `pytest` 575/575 passed |
| Package status | V6 spec configured via `agent_workbench.spec` |

---

## Build Release

```powershell
.\scripts\rebuild.ps1
```

Release artifacts are generated under `F:\Agent\.dist/`. Build cache goes to `F:\Agent\.dist\build/`. These environment directories are outside the Git repository and can be discarded at any time.

---

## For AI / New Contributors

1. **Read `.agent-entry.json` first** — it defines the governance contract all agents must follow.
2. **Use the project venv** — do not install packages into the system Python.
3. **Read the Runtime Kernel Spec** — it defines the architectural boundaries.
4. **Use the glossary** — terms like Capability, Engine, Provider, and Adapter have precise meanings.
5. **Run repository audits** — `python scripts/audit_repository.py` and `python scripts/verify_repository.py`.
6. **Keep the workspace clean** — generated files, backups, and historical copies do not belong in Git.

---

## V6 Runtime Kernel

```text
Request
    ↓
Planning
    ↓
Task
    ↓
Capability
    ↓
Engine
    ↓
Provider
```

See [`docs/v6/runtime-kernel-spec.md`](./docs/v6/runtime-kernel-spec.md) for the full specification.