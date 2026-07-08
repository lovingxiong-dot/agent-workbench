# V6 Repository Governance

> Git is the archive. The workspace contains only the current truth.

This document defines the governance rules for the `agent_workbench` repository. It complements [`runtime-kernel-spec.md`](./runtime-kernel-spec.md) — while that document constrains how the Runtime works, this document constrains how the project is organized.

---

## Principle 1: Git is the Archive

All history is preserved by Git. The workspace must not keep historical copies, backups, or duplicated old versions.

- Do not commit `v4/`, `v5/`, `old/`, `backup/`, `copy/` directories.
- Do not commit `*.bak`, `*.tmp`, `*.draft` files.
- If historical context is needed, retrieve it from Git history or from the remote archive.

## Principle 2: Workspace Contains Only the Current Truth

The working directory should look like a freshly cloned repository focused on the current V6 development line.

Allowed top-level categories:

- **Source** — `agent_workbench/`, `v6/`, `core/`, `services/`, `workers/`, `tools/`
- **Documentation** — `docs/`, `README.md`, `PROJECT_BLUEPRINT.md`, `PROJECT_LINEAGE.md`, `CHANGELOG.md`
- **Tests** — `tests/`
- **Build Scripts** — `scripts/`, `main.py`, `agent_workbench.spec`, `requirements.txt`
- **Configuration** — `config/`, `pytest.ini`, `.gitignore`

Everything else should be ignored, deleted, or moved outside the repository.

## Principle 3: One Asset, One Authority

Each type of document has exactly one official version.

| Asset | Authority |
|---|---|
| README | `README.md` (root) |
| Blueprint | `PROJECT_BLUEPRINT.md` (root) |
| Changelog | `CHANGELOG.md` (root) |
| Lineage | `PROJECT_LINEAGE.md` (root) |
| Runtime Kernel Spec | `docs/v6/runtime-kernel-spec.md` |
| Runtime Glossary | `docs/v6/runtime-glossary.md` |
| Repository Governance | `docs/v6/repository-governance.md` |
| Repository Map | `docs/v6/repository-map.md` |
| UI Contract Spec | `docs/v6/SPEC.md` |
| Roadmap | `docs/v6/ROADMAP.md` |

Do not create files such as `SPEC_NEW.md`, `README_old.md`, `PROJECT_BLUEPRINT_copy.md`, or `runtime_spec_v2.md`.

## Principle 4: Generated Files Are Disposable

Build artifacts, caches, and generated outputs must never be committed. They can always be regenerated.

Examples:

- `dist/` — PyInstaller output
- `build/` — PyInstaller build cache
- `__pycache__/` — Python bytecode
- `.pytest_cache/` — test cache
- `coverage/` — coverage reports
- `*.pyc`, `*.pyo`

These are already covered by `.gitignore`. If a new generated artifact appears, add it to `.gitignore` immediately.

## Principle 5: Repository Is Self-Explanatory

A new contributor should understand the layout within 5 minutes.

- `README.md` provides project intro, quick start, and document navigation.
- `docs/v6/repository-map.md` provides the auto-generated directory map.
- `docs/v6/repository-governance.md` explains why the repository is organized this way.
- `scripts/audit_repository.py` can be run to verify repository health.

---

## Directory Structure Standard

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
    v6/
        runtime-kernel-spec.md
        runtime-glossary.md
        repository-governance.md
        repository-map.md
        SPEC.md
        ROADMAP.md
    archive/              # Historical documents worth keeping
README.md
PROJECT_BLUEPRINT.md
PROJECT_LINEAGE.md
CHANGELOG.md
main.py
agent_workbench.spec
requirements.txt
pytest.ini
.gitignore
```

---

## Forbidden Names

Do not create files or directories with the following keywords, unless they are explicitly part of an approved archive process:

- `legacy`
- `deprecated`
- `old`
- `backup`
- `copy`
- `copy2`
- `tmp`
- `draft`
- `v4`, `v5` (in current source)

If such names appear during development, they must be removed before commit.

---

## Automation

The following scripts enforce this governance:

- `scripts/audit_repository.py` — scan for duplicate docs, legacy names, generated files, and build artifacts.
- `scripts/generate_repository_map.py` — generate `docs/v6/repository-map.md`.
- `scripts/verify_repository.py` — verify repository health before commit or CI.

Run them manually or integrate into CI.

---

## Local Workspace Recommendation

To keep the development repository clean, maintain related but non-source assets outside Git:

```text
AI/
├── AgentWorkbench/              ← Git repository (development only)
├── AgentWorkbench-Release/      ← Packaged releases
├── AgentWorkbench-Assets/       ← Models, images, datasets
└── Sandbox/                     ← Temporary experiments and downloads
```

The Git repository should never contain release binaries, large models, or temporary downloads.
