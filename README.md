# AI Agent Workbench

> **Active development line: V6 (`v6-agent` branch).**
>
> V6 is a ground-up rewrite of the Agent Runtime platform. It uses `RuntimeContext` as the single public protocol and treats Agent capabilities as first-class Runtime objects.
>
> V5 and earlier are frozen in Git history and no longer maintained in the workspace.

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
| [`docs/v6/runtime-kernel-spec.md`](./docs/v6/runtime-kernel-spec.md) | Runtime Kernel: layers, ownership, dependency rules | 30 min |
| [`docs/v6/runtime-glossary.md`](./docs/v6/runtime-glossary.md) | Standard vocabulary for the platform | 15 min |
| [`docs/v6/repository-governance.md`](./docs/v6/repository-governance.md) | Repository structure and cleanliness rules | 10 min |
| [`docs/v6/repository-map.md`](./docs/v6/repository-map.md) | Auto-generated directory overview | 5 min |
| [`PROJECT_BLUEPRINT.md`](./PROJECT_BLUEPRINT.md) | Project lineage, current task, and roadmap | 1 hour |
| [`PROJECT_LINEAGE.md`](./PROJECT_LINEAGE.md) | V5 / V6 identity map and branch rules | 15 min |
| [`CHANGELOG.md`](./CHANGELOG.md) | Version-by-version changelog | 20 min |
| [`docs/v6/SPEC.md`](./docs/v6/SPEC.md) | UI component signal contracts | 30 min |

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
| Active branch | `v6-agent` |
| Current version | `v6.9.6-alpha` |
| Runtime Kernel | Frozen — Request / Planning / Task / Capability / Engine / Provider |
| Test status | `pytest` 575/575 passed |
| Package status | V6 spec configured via `agent_workbench.spec` |

---

## Build Release

```powershell
.\scripts\rebuild.ps1
```

Release artifacts are generated under `dist/` and `build/`. These directories are disposable and ignored by Git.

---

## For AI / New Contributors

1. **Use the project venv** — do not install packages into the system Python.
2. **Read the Runtime Kernel Spec first** — it defines the architectural boundaries.
3. **Use the glossary** — terms like Capability, Engine, Provider, and Adapter have precise meanings.
4. **Run repository audits** — `python scripts/audit_repository.py` and `python scripts/verify_repository.py`.
5. **Keep the workspace clean** — generated files, backups, and historical copies do not belong in Git.

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
