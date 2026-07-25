---
# PROJECT BLUEPRINT — AI Agent Workbench v6

> **Document Type**: Project Blueprint (Architecture Charter, NOT Constitution)
> **Status**: Active (2026-07-25)
> **Source of Truth**: [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) (Constitution) > [FOUNDATION.md](./FOUNDATION.md) (CENTRE ecosystem) > [PROJECT_STATE.md](./PROJECT_STATE.md) (Current Snapshot) > THIS FILE (Architecture Charter)
> **Important**: PROJECT_DECLARATION.md is the **constitution** (frozen). This file is the **charter** (living, can be updated within constitutional bounds).
> **Important Distinction**: Version numbers (e.g. v6.18) do NOT equal Milestone numbers (e.g. Phase 3.11). They are independent dimensions.

---

## Part 0 — Header (元信息)

### Current Snapshot (2026-07-25)

| Field | Value |
|-------|-------|
| **Product** | AI Agent Workbench v6 = **Workbench OS 1.0** (Agent Workspace) |
| **Active Branch** | `v6-agent` ⭐ (SINGLE source of truth) |
| **HEAD Commit** | `2c6ff08` (pushed) |
| **Current Version** | `v6.18.0-alpha` |
| **Current Milestone** | Phase 3.11 Finalization Complete |
| **Next Milestone** | Phase 3.12 Observation Layer Implementation |
| **Stable Line** | `main` (v6.12.0-beta.15) |
| **Public Baseline** | `v6.0.0-alpha` |

### Frozen Tags (Architecture Anchors)

| Tag | Date | Milestone |
|-----|------|-----------|
| `v6.0.0-alpha` | 2026-06 | Public baseline |
| `v6.5.8-alpha` | 2026-06 | Internal migration checkpoint |
| `v6.9.6-foundation` | 2026-07-09 | **Runtime Foundation Frozen** ⭐ |
| `v6.16.0-alpha` | 2026-07-25 | **Phase 3.11 Runtime Execution Kernel Frozen** ⭐ (ADR-013/014/015) |
| `v6.17.0-alpha` | 2026-07-25 | **Phase 3.10 Presentation Layer Frozen** |
| `v6.18.0-alpha` | 2026-07-25 | **Phase 3.11 Finalization HEAD** (current) |
| `v6.19.0-alpha` | 2026-07-25 | Phase 3.12 Observation Layer Complete |
| `v6.20.0-alpha` | 2026-07-25 | **Phase 3.13 Presentation & Consumption Complete** (current) |

> **Historical Note (Tag vs Phase ordering)**:
> - **Version tags** (e.g. v6.16) represent **commit chronology** (when code was tagged)
> - **Phase numbers** (e.g. Phase 3.11) represent **architecture evolution** (what milestone was achieved)
> 
> These are **independent dimensions**. v6.16.0-alpha = Phase 3.11 (latest frozen), v6.17.0-alpha = Phase 3.10 (previous frozen). This is intentional: the tag for Phase 3.10 (Presentation) was created after the tag for Phase 3.11 (Runtime) to keep stable `main` (`v6.12.0-beta.15`) untouched. **When in doubt: read the Milestone column, not the Version column.**

### ADR Index (Architecture Decisions)

| ADR | Title | Status |
|-----|-------|--------|
| ADR-013 | Runtime Lifecycle Event Extension | Frozen (Phase 3.11) |
| ADR-014 | Cancellation Precedence Rule | Frozen (Phase 3.11) |
| ADR-015 | Parent-Child Execution Propagation v0.3 | Frozen (Phase 3.11) |
| ADR-016 | Observation Layer Contract | Frozen (Phase 3.12, designed) |
| ADR-017 | Observation Presentation Boundary | Frozen (Phase 3.13, designed) |
| ADR-018 | Agent Runtime Insight Boundary | Frozen (Phase 3.14, designed) |
| ADR-019 | Agent Decision Support Boundary | Frozen (Phase 3.15, designed) |
| ADR-020 | Cognitive Continuity & Harness Architecture Contract | Architecture Review only |

> **Phase 3.12 Status (2026-07-25)**: Observation Layer Contract (ADR-016) implemented with 3 submodules: `contract/` (Frozen Schema, 5 types / 4 sources / 3 scores), `consumer/` (read-only RuntimeEvent Adapter), `registry/` (Minimal in-memory, 3 methods). 88/88 Observation tests PASS. Runtime tests 100/100 unchanged.

---

## Part 1 — Constitution (Constitution Reference)

> **This Blueprint is a CHARTER, not a CONSTITUTION.**
> The Constitution is [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) (FROZEN).

Constitution principles (from PROJECT_DECLARATION.md) that govern this Blueprint:

### 1.1 Documentation Defines Architecture

> Architecture is not what the code happens to do. Architecture is what the documentation declares.
> Code must implement architecture. Architecture must not be reverse-engineered from code.
> When code and documentation disagree, documentation is correct until explicitly revised.

### 1.2 Contract First

Every boundary is a contract. Every contract is explicit.

### 1.3 Repository Before Implementation

All architecture decisions are recorded in `/.project/decisions/` (ADRs) before any code change.

### 1.4 Layered Architecture

```
Protocol Layer
    ↓
Runtime Layer
    ↓
Presentation Layer
    ↓
Governance Layer
```

Contracts define interfaces. Layers implement contracts. Governance enforces rules.

### 1.5 No-Code Registration Principle

> All AI capabilities (Provider / Tool / Skill / Workflow / Prompt / Memory / MCP) are added through the Workbench UI, never by modifying code.
> 
> Flow: UI → ConfigManager → Registry Reload → Capability Update → Agent Ready

---

## Part 2 — Product Identity (产品定位)

### 2.1 One-Line Description

> **AI Agent Workbench v6** is the **Official Product Validation Platform** of the V6 Runtime — a Single-Agent intelligent workbench where users and agents collaborate on tasks.

### 2.2 Product Constitution — No-Code Registration Principle (from PROJECT_DECLARATION.md)

> **Definition**: All AI capabilities (Provider, LLM, MCP, Skill, Tool, Workflow, Prompt, Memory) are added through the Workbench UI.

**Implications**:
- "Add a new OpenAI-compatible model" → Click "AI Models → +"
- "Add an MCP server" → Click "MCP → +"
- "Write a Python skill" → Click "Skills → +", select script
- "Change model, API endpoint, permissions, disable a tool" → All in Workbench

**Anti-Pattern** (禁止):
> ❌ UI → modify code → recompile → restart
> ❌ Workbench as Demo / temporary showcase
> ❌ Special-case logic for new capability types

### 2.3 Product Boundary

> **Workbench is NOT**:
> - ❌ A chatbot
> - ❌ A standalone IDE
> - ❌ A multi-agent governance platform (this is Agent Manager OS, next era)
> - ❌ Agent Factory (next era)

> **Workbench IS**:
> - ✅ Single Agent intelligent workbench
> - ✅ Runtime + Cognitive Capability + UI full integration validation platform
> - ✅ The official v6 Runtime productization gate
> - ✅ Composable AI Workbench (extensible via No-Code Registration)

### 2.4 Product Roadmap (from PROJECT_DECLARATION.md)

```
CENTRE / AOS (Shared Ancestor)
    │
    ├── Workbench v6 (this product, ACTIVE)    ← Agent Workspace
    │     Single Agent, Workflow, Chat UI
    │
    └── Agent Manager OS (future)              ← Governance Plane
          Multi-Agent, Routing, Dashboard
```

> **The goal**: prove that Agent + Workflow + Runtime + UI can run end-to-end on the CENTRE Foundation.

### 2.5 Core Statement

> **Workbench's role is to prove the following statement true**:
> 
> "Agent + Workflow + Runtime + UI can run end-to-end on the CENTRE Foundation."

---

## Part 3 — Architecture Position (架构定位)

### 3.1 Workbench v6 in the V6 Stack

```
┌────────────────────────────────────────────────────────┐
│                    CENTRE / AOS                         │
│                  (Shared Ancestor)                      │
└────────────────────────┬───────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────┐                 ┌─────────────────┐
│ Workbench v6 │                 │  Agent Manager  │
│   (ACTIVE)   │                 │  OS (future)    │
│              │                 │                 │
│ Single Agent │                 │ Multi-Agent      │
│ Workspace    │                 │ Governance       │
└──────┬───────┘                 └─────────────────┘
       │
       │  v6-agent (active branch)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                   Workbench Runtime                       │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Runtime Kernel (FROZEN: v6.16.0-alpha)            │  │
│  │                                                    │  │
│  │ v6.9.6-foundation (Frozen) + Phase 3.11 Evolution │  │
│  │ RuntimeContract: Provider, Tool, Skill, Workflow   │  │
│  │                                                    │  │
│  │ Memory: NOT implemented in Runtime Kernel          │  │
│  │   (Future Memory through Capability Contract;     │  │
│  │    designed in Phase 3.16, ADR-020;                │  │
│  │    not in v6/runtime/)                             │  │
│  └────────────────────────────────────────────────────┘  │
│                          ↑                                │
│                          │ (read-only event flow)        │
│                          ↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Cognitive Layer (tools/, separate layer)            │  │
│  │                                                    │  │
│  │ ├── Observation (Phase 3.12, ADR-016)              │  │
│  │ ├── Insight (Phase 3.14, ADR-018)                  │  │
│  │ └── Decision Support (Phase 3.15, ADR-019)        │  │
│  └────────────────────────────────────────────────────┘  │
│                          ↑                                │
│                          │ (requires_human_approval)     │
│                          ↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │ v6/ui (Frozen Phase 2-B.2)                        │  │
│  │ Pure UI Foundation — visual rendering only        │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       │ v6/ui is Frozen Foundation (22 files)
       ▼
┌──────────────────────────────────────────────────────────┐
│              Qt / Web / CLI / REST API (Frontends)         │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Runtime Cognitive Pipeline v1 (Phase 3.12-3.15)

```
Runtime
  ↓
Observation (Phase 3.12, ADR-016)
  ↓
ObservationViewModel (Phase 3.13, ADR-017)
  ↓
InsightArtifact (Phase 3.14, ADR-018)
  ↓
DecisionSupportArtifact (Phase 3.15, ADR-019)
  ↓ requires_human_approval = True
Human / Agent
  ↓ NEW Execution
Runtime
```

> **Important**: Cognitive Layer is **NOT** part of Runtime Kernel. Do NOT add `v6/runtime/observation/`, `v6/runtime/insight/`, or `v6/runtime/decision_support/`.

### 3.3 Current Architecture Status

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

- **v6/ui** (22 files): Frozen Pure UI Foundation
- **Renderer** layer (`presentation/renderers/v6_ui/`): Maps data to UI, never touches v6/ui private members
- **Application** layer (`application/`): Uses `WorkbenchController`, NOT `WorkbenchUIController`
- **v6/runtime/**: FROZEN at v6.16.0-alpha (Phase 3.11). Only bug fix / contract compatibility allowed.

---

## Part 4 — Branch Classification (分支分类)

### 4.1 Branch Architecture (Blueprint Definition)

> **The Branch Architecture is a BLUEPRINT design**. The actual implementation may merge multiple branches into a single active branch.

| Branch | Blueprint Status | Purpose | Allowed Changes | Reality (2026-07-25) |
|--------|------------------|---------|-----------------|----------------------|
| `v6-core` | Frozen (Runtime Kernel) | Framework Core Foundation | Only bug fixes; Runtime = frozen infrastructure | Planned in design, merged into `v6-agent` |
| `v6-service` | Extension Layer (planned) | Runtime Service Architecture (Memory, Prompt, Model Adapter, Tool Adapter, Knowledge Adapter) | Capability extension via Capability Runtime Contract | Planned in design, merged into `v6-agent` |
| `v6-agent` | **Active Development** ⭐ | Agent Application (Product Evolution) | All product work — Metadata, UI, Workflow, etc. | **Current single active branch** (HEAD = `2c6ff08`) |

> **Implementation Reality (2026-07-25)**: In current Git state, **only `v6-agent` is actively maintained** as a single-source-of-truth branch. `v6-core` and `v6-service` were planned as 3-tier separation in PROJECT_BLUEPRINT design, but in practice their work has been merged into `v6-agent`. This single-branch strategy is intentional to avoid merge conflicts and keep the agent-product co-evolving.

### 4.2 Branch Lifecycle

| Stage | Branch | Status |
|-------|--------|--------|
| **Public Baseline** | `v6.0.0-alpha` | Stable, public |
| **Internal Migration** | `v6.5.8-alpha` | Historical, not public |
| **Runtime Foundation** | `v6.9.6-foundation` | Frozen (2026-07-09) |
| **Stable Release** | `main` (currently v6.12.0-beta.15) | Always compilable, runnable, releasable |
| **Active Development** | `v6-agent` | SINGLE source of truth (HEAD = `2c6ff08`) |
| **Historical Snapshots** | `archive/*` | Frozen (v3/v4/v5 + planned v6-core/v6-service/v6-dev) |

### 4.3 Branch Rules

| Rule | Description |
|------|-------------|
| **NEVER commit directly to `main`** | All changes go through `v6-agent` |
| **ALL changes in `v6-agent`** | Single source of truth |
| **`trae/*` temporary branches** | Merge to `v6-agent` only, then delete |
| **`--no-ff` merge** | Preserve complete commit history |
| **Tests must pass before merge** | 372 tests PASS gate |

---

## Part 5 — Layer Classification (层级分类)

### 5.1 Runtime Kernel (FROZEN)

**Location**: `v6/runtime/`
**Status**: FROZEN at v6.16.0-alpha (Phase 3.11, 2026-07-25)
**ADR**: ADR-013 / ADR-014 / ADR-015

**8 Frozen Components**:

| Component | Description |
|-----------|-------------|
| Parent-Child Execution | `submit_child()` / `cancel()` DFS propagation |
| Cancellation Propagation | `CancellationPropagationContext` (frozen + invariants) |
| Execution Metadata | `ExecutionMetadata` (frozen) |
| Execution Registry | Topology owner |
| Lifecycle / Activity Dual State | `LifecycleState` + `ActivityState` |
| TASK_CANCELLED Event | RuntimeEvent extension |
| ExecutionControl | Cancellation Token aggregator |
| CancellationPropagation | PropagationType + Limits |

**Runtime Freeze Certificate**:

**Allowed**:
- ✓ Bug Fix
- ✓ Frozen Contract compatibility (向后兼容字段)

**Forbidden**:
- ✗ Memory / Knowledge / Identity
- ✗ Agent Role / Harness Logic
- ✗ New Runtime concepts or control flows
- ✗ New responsibilities for existing Runtime modules

**Anti-Pattern Warning** (DO NOT):
- ❌ `v6/runtime/observation/`
- ❌ `v6/runtime/insight/`
- ❌ `v6/runtime/decision_support/`
- ❌ `v6/runtime/memory/`
- ❌ `v6/runtime/harness/`

### 5.2 Runtime Foundation (Frozen 2026-07-09)

**Location**: `v6/runtime/` (Foundation layer)
**Status**: FROZEN at v6.9.6-foundation
**6-Layer Runtime Kernel**:
```
Request → Planning → Task → Capability → Engine → Provider
```

### 5.3 Cognitive Layer (Designed, Asset uncommitted)

**Location**: `tools/` (NOT in `v6/runtime/`)

> **Boundary Statement**:
> - `tools/` is **NOT** a Runtime extension.
> - `tools/` consumes Runtime artifacts / events (read-only via `RuntimeEvent`).
> - `tools/` does NOT modify Runtime Kernel.
> - `tools/` does NOT introduce new concepts into `v6/runtime/`.

| Module | Phase | Status | ADR |
|--------|-------|--------|-----|
| `tools/observation/` | Phase 3.12 | Designed, uncommitted | ADR-016 |
| `tools/presentation/` (cognitive) | Phase 3.13 | Designed, uncommitted | ADR-017 |
| `tools/insight/` | Phase 3.14 | Designed, uncommitted | ADR-018 |
| `tools/decision_support/` | Phase 3.15 | Designed, uncommitted | ADR-019 |
| `tools/memory/` | Phase 3.16 | Architecture Review only | ADR-020 |
| `tools/harness/` | Phase 3.16 | Architecture Review only | ADR-020 |
| `tools/context/` | Phase 3.16 | Architecture Review only | ADR-020 |

> **Important**: Cognitive Layer consumes Runtime via read-only event flow. It does NOT modify Runtime Kernel. Do NOT add `v6/runtime/observation/`, `v6/runtime/insight/`, or `v6/runtime/decision_support/`.

### 5.4 Presentation Layer

| Module | Location | Status |
|--------|----------|--------|
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Active |
| Presentation Runtime | `agent_workbench/presentation/runtime.py` | Active |
| Renderer Registry | `agent_workbench/presentation/renderers/registry.py` | Active |
| v6/ui Foundation | `v6/ui/` (22 files) | **FROZEN** (Phase 2-B.2) |
| V6UIRenderer | `agent_workbench/presentation/renderers/v6_ui/` | Active |
| CLI Renderer | `agent_workbench/presentation/renderers/cli_renderer.py` | Active |

### 5.5 Application Layer

| Module | Location | Status |
|--------|----------|--------|
| WorkbenchController | `agent_workbench/application/` | Active |
| Agent Packages | `packages/` (3 agents: personal/coding/research) | Active |
| Provider Integrations | `agent_workbench/services/` (7 providers) | Active |

### 5.6 UI Layer (Frozen Foundation)

**Location**: `v6/ui/` (22 files)
**Status**: **FROZEN** (Phase 2-B.2)

**Allowed Changes**:
- Visual refinement (colors, spacing, accessibility)
- UI Capability API additions (e.g., `ChatArea.reset_workspace()`)

**Forbidden Changes**:
- Runtime dependency, Agent lifecycle, Session ownership, Model ownership
- Business logic inside widgets
- Layout/component structure changes per Renderer need

---

## Part 6 — Version vs Milestone (版本与里程碑)

### 6.1 Two Independent Dimensions

| Dimension | Format | Meaning | Example |
|-----------|--------|---------|---------|
| **Version** | `v6.X.Y-alpha` | Commit order (chronological) | v6.18.0-alpha |
| **Milestone** | `Phase X.Y` | Architectural semantic | Phase 3.11 Finalization |

**They are independent**. A version can match a milestone by coincidence (e.g. v6.16.0-alpha ≈ Phase 3.11) but this is not a general rule.

### 6.2 Version → Milestone Map (Reality 2026-07-25)

| Version | Milestone | Status |
|---------|-----------|--------|
| v6.0.0-alpha | Public baseline | Stable |
| v6.5.8-alpha | Internal migration checkpoint | Historical |
| v6.9.6-foundation | Runtime Foundation Frozen | **Frozen (2026-07-09)** |
| v6.10.0-alpha | Configuration-driven Workbench | Active history |
| v6.12.0-beta.15 | Stable on `main` | **Stable** |
| v6.14.0-alpha | D5 Agent Selector | Active history |
| v6.15.0-alpha | Product Shell Integration | Active history |
| v6.16.0-alpha | **Phase 3.11 Runtime Frozen** | **Frozen (2026-07-25)** |
| v6.17.0-alpha | **Phase 3.10 Presentation Frozen** | **Frozen (2026-07-25)** |
| v6.18.0-alpha | **Phase 3.11 Finalization HEAD** | **Active (current)** |

### 6.3 Tag Ordering Note

> Tag ordering reflects commit order, not architectural phase order.
> 
> Example: v6.16.0-alpha = Phase 3.11 Runtime Frozen (latest frozen), v6.17.0-alpha = Phase 3.10 Presentation Frozen (previous). Phase 3.10 was architecturally earlier but the tag was created later to keep `main` (v6.12.0-beta.15) untouched.

---

## Part 7 — Boundary Rules (边界规则)

### 7.1 Forbidden Imports (Phase 3+)

```python
PHASE_3_14_PLUS_FORBIDDEN = (
    # Runtime 写边界
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    # v6.9.6 Capability Frozen
    "agent_workbench.runtime.capability",
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
    # Frozen Presentation
    "v6.presentation.models",
    "v6.presentation.contracts",
)
```

### 7.2 Runtime Anti-Patterns (DO NOT)

- ❌ Add `observation/`, `insight/`, `decision_support/`, `memory/`, `harness/` to `v6/runtime/`
- ❌ Modify Runtime without ADR (after v6.16.0-alpha)
- ❌ Allow Cognitive Layer to write Runtime State
- ❌ Bypass Human Approval Boundary (requires_human_approval=True)

### 7.3 Cognitive Layer Rules

- ✓ Read Runtime via `RuntimeEvent` (read-only)
- ✓ Emit `DecisionSupportArtifact` (requires Human Approval)
- ✗ Write to Runtime State directly
- ✗ Mutate Runtime Context

---

## Part 8 — Active Modules (活动模块)

| Module | Path | Status |
|--------|------|--------|
| Runtime Foundation | `v6/runtime/` | **FROZEN** (v6.9.6-foundation) |
| Runtime Execution Kernel | `v6/runtime/` | **FROZEN** (v6.16.0-alpha, Phase 3.11) |
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Active |
| Presentation Runtime | `agent_workbench/presentation/runtime.py` | Active |
| Renderer Registry | `agent_workbench/presentation/renderers/registry.py` | Active |
| v6/ui Foundation | `v6/ui/` (22 files) | **FROZEN** (Phase 2-B.2) |
| V6UIRenderer | `agent_workbench/presentation/renderers/v6_ui/` | Active |
| CLI Renderer | `agent_workbench/presentation/renderers/cli_renderer.py` | Active |
| Application Layer | `agent_workbench/application/` | Active |
| Agent Packages | `packages/` (3 agents) | Active |
| Provider Integrations | `agent_workbench/services/` (7 providers) | Active |
| Cognitive Layer (3.12-3.15) | `tools/observation/`, etc. | 🟡 Designed, Asset uncommitted |
| Memory + Harness (Phase 3.16) | `tools/memory/`, `tools/harness/`, `tools/context/` | ⏸ Architecture Review only |

---

## Part 9 — Known TODO (2026-07-25)

| # | Item | Priority | Phase |
|---|------|----------|-------|
| 1 | Phase 3.12-3.15 Asset Sync (commit untracked `tools/`, `tests/tools/`, `v6/presentation/observation/`, ADRs, docs) | **High** | Phase 3.12-3.15 |
| 2 | Phase 3.12 Observation Layer Implementation | High | Phase 3.12 |
| 3 | Phase 3.16 Memory + Harness (Architecture Review only) | Medium | Phase 3.16 |
| 4 | Stash cleanup (3 → 0) | Low | Post-Phase 3.12 |
| 5 | Working Tree cleanup (Phase 2-D vs Phase 3.12-3.15 split) | Low | Post-Phase 3.12 |
| 6 | v6/ui legacy worktree changes commit | Low | Post-Phase 3.12 |

---

## Part 10 — Reading Order (How to Use This Blueprint)

For an AI Agent or new contributor:

```
1. README.md                ← Quick start, branch strategy
2. ROOT_INDEX.md            ← Repository Router
3. FOUNDATION.md            ← CENTRE ecosystem worldview
4. AGENT_ENTRY.md           ← Mandatory onboarding
5. PROJECT_DECLARATION.md   ← Workbench v6 CONSTITUTION (frozen)
6. PROJECT_STATE.md         ← Current development snapshot
7. THIS FILE (BLUEPRINT)    ← Architecture charter (you are here)
8. PROJECT_LINEAGE.md       ← Version lineage
9. ARCHITECTURE.md          ← Architecture navigation
10. ADR-XXX                  ← Specific ADRs (in /.project/decisions/)
```

---

## Part 11 — Related Documents

| Document | Purpose |
|----------|---------|
| [FOUNDATION.md](./FOUNDATION.md) | **Shared ancestor — CENTRE ecosystem** |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Workbench v6 Constitution (FROZEN) |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current development snapshot |
| [PROJECT_LINEAGE.md](./PROJECT_LINEAGE.md) | Version lineage map |
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | AI Agent onboarding + target system identification |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) | Construction rules |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |
| [docs/v6/repo-narrative-migration-report.md](./docs/v6/repo-narrative-migration-report.md) | 2026-07-25 Repository Authority Audit |
| [.project/decisions/ADR-013 ~ ADR-020](../.project/decisions/) | Architecture Decision Records |
| [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) | v6/ui freeze contract |
| [.project/handoff/phase3-11-runtime-frozen-handoff.md](./.project/handoff/phase3-11-runtime-frozen-handoff.md) | Phase 3.11 Handoff |

---

## Part 12 — Document Authority Hierarchy

```
FOUNDATION.md                ← CENTRE ecosystem worldview (Tier 0)
PROJECT_DECLARATION.md       ← Workbench v6 Constitution (Tier 1, FROZEN)
PROJECT_BLUEPRINT.md         ← Architecture Charter (Tier 2, this file, ACTIVE)
PROJECT_STATE.md             ← Current Snapshot (Tier 3, ACTIVE)
PROJECT_LINEAGE.md           ← Version History (Tier 4, ACTIVE)
ARCHITECTURE_BOUNDARY.md     ← Construction Rules (Tier 5, ACTIVE)
ADR-XXX                       ← Architecture Decision Records (Tier 6)
docs/v6/                     ← Detailed design / report documents
```

When documents conflict: **higher Tier wins** (Tier 1 Constitution overrides Tier 2 Charter).

---

## Part 13 — Last Update

- **2026-07-25**: Repository Narrative Migration Batch. v6-agent = active, v6.18.0-alpha = current. Runtime Frozen at v6.16.0-alpha (Phase 3.11). 5 source documents + this Blueprint all synchronized.
- **Next**: Phase 3.12 Observation Layer Asset Sync + Implementation.

---

**END OF PROJECT BLUEPRINT**
