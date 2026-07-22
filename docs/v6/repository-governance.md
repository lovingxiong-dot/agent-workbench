# V6 Repository Governance

> Git is the archive. The workspace contains only the current truth.
> **Repository Governance v1.0**: Root-level governance entry layer at [`AGENT_ENTRY.md`](../../AGENT_ENTRY.md), [`PROJECT_DECLARATION.md`](../../PROJECT_DECLARATION.md), [`PROJECT_STATE.md`](../../PROJECT_STATE.md), [`ARCHITECTURE.md`](../../ARCHITECTURE.md), [`ROOT_INDEX.md`](../../ROOT_INDEX.md).

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

## Principle 6: Environment Directories Are Not Source

Directories that begin with `.` and live next to the Git repository are part of the local development environment, not the project source. Git does not track them, and they can be recreated or discarded.

- `.dist/` — packaged releases and build artifacts.
- `.resource/` — models, images, datasets, and other large assets.
- `.sandbox/` — temporary experiments, downloads, and scratch work.
- `.monitor/` — local monitoring and runtime environment data.
- `.workbuddy/` — local AI collaboration state.
- `.trae-logs/` — Trae Code mode work logs and session memory.

Any new top-level directory in the workspace that is not source must fit into one of these environment categories. If it cannot be classified, it should not exist.

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

## Agent Collaboration Convention

This repository is maintained by multiple agents. The following conventions ensure that every agent can enter the workspace, understand its state, and leave it cleaner than it was found.

### Before You Start

1. **Read the constitution first** — `repository-governance.md`, `runtime-glossary.md`, and `runtime-kernel-spec.md` define the boundaries.
2. **Check the baseline** — note the current Git commit and tag (e.g., `v6.9.6-hygiene`).
3. **Run the audits** — `python -B scripts/audit_repository.py` and `python -B scripts/verify_repository.py` must pass before you claim completion.

### While You Work

1. **One Asset, One Authority** — do not create `README_new.md`, `SPEC_v2.md`, `blueprint_copy.md`, or any duplicate authority document.
2. **Classify every new file** — each file or directory must belong to **Source**, **Documentation**, **Tests**, **Build Scripts**, **Configuration**, or an environment category (`.dist/`, `.resource/`, `.sandbox/`). If it does not fit, it does not belong.
3. **No generated files in Git** — `__pycache__/`, `.pytest_cache/`, `build/`, `dist/`, `*.pyc`, `*.bak`, and `*.tmp` must never be committed.
4. **Temporary work goes to `.sandbox/`** — prototype scripts, downloaded files, experiment outputs, and scratch notes belong in `.sandbox/`. Delete them when the task is done.
5. **Do not leave orphan files** — if you create a file and later decide it is unnecessary, delete it. Do not rename it to `*_old` or `*_backup`.

### Before You Finish

1. **Run tests** — `pytest` must pass.
2. **Run audits** — `python -B scripts/audit_repository.py` must score 100/100.
3. **Inspect Git status** — `git status --short` should show only intentional changes.
4. **Commit atomically** — one coherent change per commit, with a clear message.

### Handoff Rule

When transferring context to another agent, use the standard handoff flow. Do not rely on chat history or uncommitted files to carry state.

---

## Local Workspace Layout

Keep the Git repository focused on source. All non-source assets live in sibling environment directories under the same parent:

```text
F:\Agent/
├── agent_workbench/      ← Git repository (development only)
├── .dist/                ← Packaged releases and build artifacts
├── .resource/            ← Models, images, datasets, and other assets
├── .sandbox/             ← Temporary experiments and downloads
├── .monitor/             ← Local monitoring and runtime environment data
└── .workbuddy/           ← Local AI collaboration state
```

The Git repository should never contain release binaries, large models, or temporary downloads.

---

## Environment Directory Usage Conventions

Environment directories live next to the Git repository and are not tracked by Git. Use them consistently so every agent knows where to read and write non-source data.

| Directory | Purpose | Who Writes | Lifetime |
|---|---|---|---|
| `.dist/` | Packaged releases (`*.exe`, `*.zip`, `*.msi`) and PyInstaller build cache. | `scripts/rebuild.ps1` only. | Disposable; can be wiped and rebuilt. |
| `.resource/` | Long-term assets: models, images, icons, examples, datasets. | Agents may add assets here; never commit them. | Persistent; back up externally if valuable. |
| `.sandbox/` | Temporary experiments, downloads, prototypes, scratch work. | Any agent. | Ephemeral; safe to delete anytime. |
| `.monitor/` | Local runtime monitoring, logs, and environment state. | Running application. | Local; can be reset. |
| `.workbuddy/` | Local AI collaboration state and memory. | AI tooling. | Local; already ignored by Git. |

### `.sandbox/` Subdirectory Convention

Organize sandbox work by intent so it is easy to clean later:

```text
.sandbox/
├── prototype/      # Feature prototypes and spikes
├── download/       # Files fetched from the internet for inspection
├── playground/     # Ad-hoc experiments
├── test/           # One-off validation scripts
└── scratch/        # Notes and disposable outputs
```

When a sandbox experiment graduates into the product, move its files into the proper source tree. When it is abandoned, delete the directory.

### Creating New Environment Directories

Do not create arbitrary directories next to the repository. If a new category of non-source data appears, propose an update to this governance document. Until then, fit it into `.dist/`, `.resource/`, or `.sandbox/`.

---

## 6. Workbench Constitution: No-Code Registration

除 Runtime Kernel 和内置核心能力外，所有 Provider、LLM、MCP、Skill、Tool、Workflow、Prompt、Memory 等扩展对象，都应支持通过 Workbench UI 注册、配置和管理。开发者不应为了新增一个实例而修改源码。

新增实例的正确路径：
1. 在 Workbench UI 中打开对应面板（Provider / Skill / Tool / MCP 等）。
2. 点击 "+" 或 "Add"。
3. 填写配置表单。
4. ConfigManager 持久化。
5. Registry 自动 Reload。
6. Capability 更新，Agent 立即可用。

反模式：
- 直接修改源码文件来新增 Provider、Skill 或 Tool。
- 为了换一个模型地址而重新编译或重启应用。
