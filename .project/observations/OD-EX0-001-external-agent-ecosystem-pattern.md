# OD-EX0-001 — External Agent Ecosystem Pattern Observation

> **Type**: External Pattern Observation Log (NOT RFC, NOT ADR)
> **Date**: 2026-07-23
> **Scope**: External product pattern observation only
> **Status**: OBSERVATION COMPLETE
> **Authorization**: OD-EX0-001 explicitly granted (READ-ONLY, structural metadata only)

---

## Authorization Boundaries (As Authorized)

**Allowed**:
- Agent configuration structure (paths, directory layout, file presence)
- Agent directory inventory (memory / sessions / skills / workspace)
- Capability / skill description (names only, no content)
- Memory architecture metadata (directory structure, not content)
- Routing configuration patterns (structural)
- User-facing workflow patterns (structural)

**Forbidden**:
- Source code inspection
- Credential / token / API key access
- Personal data extraction (session content, user memory content)
- Copying implementation
- Migration design
- Workbench modification

---

## 1. Observation Source

Observed filesystem: `C:\Users\lovin\.minimax\`

Note: `C:\Users\lovin\.minimax-agent-cn` and `C:\Users\lovin\.mavis` do not exist on this system (verified). Only `.minimax` is the canonical external product directory.

---

## 2. Top-Level Layout (External Product)

```
.minimax/
├── .builtin-skills/     # 16 system-level skills (shared across agents)
├── agents/              # 4 built-in agent roles
├── bin/                 # CLI utilities
├── memory/              # Cross-agent memory layer
│   └── tracking/        # Session tracking JSON
├── v2/                  # Versioned internals (migration / observability / sessions / sqlite)
└── workspace/           # Shared runtime workspace
```

**Observation Pattern 1**: Two-tier skill architecture.
- System skills in `.builtin-skills/` (shared).
- Per-agent `skills/` directories are empty (no duplication).
- This implies skills are **composed**, not **assigned to agents**.

**Observation Pattern 2**: Memory split between per-agent and global.
- `agents/<name>/memory/` — per-agent isolated.
- `.minimax/memory/` — cross-agent tracking.

---

## 3. Built-in Agent Inventory

4 built-in agent roles (confirmed via directory listing):

| Agent | Directory | Role Indicator (Inferred) |
|-------|-----------|---------------------------|
| `coder` | `agents/coder/` | Code-focused worker |
| `verifier` | `agents/verifier/` | Verification worker |
| `general` | `agents/general/` | Generic worker |
| `mavis` | `agents/mavis/` | Root orchestrator (named differently from system name) |

**Observation Pattern 3**: Naming convention distinguishes role type.
- `mavis` is the root / orchestrator (singleton).
- `coder / verifier / general` are workers (specialized + generic).
- Each agent gets its own directory but **identical layout**.

---

## 4. Per-Agent Layout (Identical Across All 4 Agents)

```
agents/<name>/
├── config.yaml         # 55 bytes — only workspace dir
├── memory/             # Per-agent isolated memory
│   └── daily/          # Daily log files (e.g., 2026-07-23.md, 125 bytes)
├── sessions/           # Runtime-filled (empty at install time)
├── skills/             # Empty — uses system skills only
└── workspace/          # Runtime-filled (empty at install time)
```

**Observation Pattern 4**: `config.yaml` is **structural metadata only**.
- All 4 agents have **identical** config.yaml content.
- Only contains `defaultWorkspaceDir: C:\Users\lovin\.minimax/workspace`.
- **No per-agent differentiation in config.yaml**.
- Implies persona / systemPrompt / role differentiation lives elsewhere (likely runtime DB).

**Observation Pattern 5**: Per-agent memory isolation.
- `agents/coder/memory/` and `agents/verifier/memory/` are physically separate.
- No symbolic links or shared directory.
- Each agent writes its own `daily/YYYY-MM-DD.md`.
- This enforces the **Agent-isolated memory layer** observed earlier.

**Observation Pattern 6**: Skills are NOT bound to agents.
- `agents/<name>/skills/` is empty for all 4 agents.
- All skills live in `.builtin-skills/` (system-wide).
- Implies capability composition is dynamic (selected at runtime, not statically bound).

---

## 5. Built-in Skills Inventory (16 Skills)

| Skill | Type (Inferred) |
|-------|-----------------|
| `control-in-app-browser` | Integration |
| `create-agent` | **Meta-skill** (creates new agents) |
| `cu-desktop` | Integration |
| `deep-research` | Domain |
| `docx` | Format |
| `init` | Bootstrap |
| `lark-tools` | Integration |
| `llm-call` | **Primitive** (LLM invocation wrapper) |
| `mavis` | Internal coordination |
| `pdf` | Format |
| `plan-mode` | Workflow mode |
| `pptx` | Format |
| `skill-creator` | **Meta-skill** (creates new skills) |
| `skill-refiner` | **Meta-skill** (refines existing skills) |
| `visual-page` | Domain |
| `xlsx` | Format |

**Observation Pattern 7**: Skill taxonomy has **3 layers**.
1. **Meta-skills**: `create-agent`, `skill-creator`, `skill-refiner` — self-extension.
2. **Primitives**: `llm-call` — atomic capability.
3. **Domain skills**: `docx`, `pdf`, `pptx`, `xlsx`, `deep-research`, `visual-page` — task-specific.
4. **Integration skills**: `control-in-app-browser`, `cu-desktop`, `lark-tools` — external system hooks.
5. **Workflow modes**: `plan-mode`, `init` — control flow patterns.
6. **Internal**: `mavis` — coordination (not user-facing).

**Observation Pattern 8**: Self-extension is built-in.
- 3 of 16 skills are **meta-skills** (19%).
- This implies the product supports runtime capability expansion without code release.

---

## 6. Memory Architecture Pattern

Observed directories:

| Path | Visibility | Type |
|------|------------|------|
| `agents/<name>/memory/daily/YYYY-MM-DD.md` | Per-agent | Daily journal |
| `.minimax/memory/tracking/YYYY-MM-DD.json` | Cross-agent | Session tracking |

**Observation Pattern 9**: Two-layer memory split.
- **Per-agent layer**: agent-specific experience (does not leak across agents).
- **Cross-agent layer**: tracking metadata (shared but read-only nature).
- No shared user preference file observed at this directory level.

**Observation Pattern 10**: Memory is **append-only by date**.
- Filename pattern `YYYY-MM-DD.md` / `.json`.
- Implies immutable daily logs, not mutable global state.
- Cross-day aggregation must happen at query time, not write time.

---

## 7. Cross-Product Pattern Extraction

This observation does NOT design Workbench v6. It only records patterns for future review.

### Pattern A: Identity Differentiation Outside Filesystem

External product: 4 agents share identical config.yaml. Differentiation lives in **runtime DB**, not filesystem.
- Implication for Workbench: Agent identity can be Runtime-state, not file-state. Aligns with our Runtime = Evidence Producer principle.

### Pattern B: Skill Composition, Not Assignment

External product: Skills live in shared `.builtin-skills/`, per-agent `skills/` is empty.
- Implication for Workbench: Capability layer should be runtime-composed, not statically attached to a "type of Agent". Aligns with our Capability / CapabilityChain pattern.

### Pattern C: Per-Agent Memory Isolation

External product: Each agent has own `memory/` directory, no cross-agent sharing.
- Implication for Workbench: If multi-agent is added, memory must be **physically isolated**, not just logically tagged. Aligns with Evidence ≠ Authority (memory is Agent authority, Runtime provides storage).

### Pattern D: Memory Has Time Dimension

External product: Memory files are `YYYY-MM-DD` named.
- Implication for Workbench: If memory is added, prefer append-only-by-time, not mutable global. Aligns with our Foundation Runtime producing facts.

### Pattern E: Self-Extension via Meta-Skills

External product: `create-agent`, `skill-creator`, `skill-refiner` are first-class skills.
- Implication for Workbench: Runtime evolution can be **driven by skills**, not just by code release. Aligns with our Skill / Provider Ecosystem direction (v6.10+ roadmap).

### Pattern F: Tracking vs Memory Distinction

External product: `memory/tracking/` (JSON, cross-agent, structural) vs `memory/daily/` (MD, per-agent, semantic).
- Implication for Workbench: Two-layer memory is consistent — structural tracking + semantic daily journal.

### Pattern G: Workspace Per-Agent

External product: `agents/<name>/workspace/` is runtime-filled.
- Implication for Workbench: Workspace is a **side-effect area** for Agent, separate from config / memory / skills.

---

## 8. What This Observation Does NOT Do

- ❌ Does NOT propose Workbench v6 changes.
- ❌ Does NOT read external source code.
- ❌ Does NOT access personal data (session content, user memory content).
- ❌ Does NOT copy implementation.
- ❌ Does NOT create Architecture Decision.
- ❌ Does NOT modify Workbench v6 / Runtime / Protocol / Contract.
- ❌ Does NOT trigger AD-A1-005.
- ❌ Does NOT change Guardian Mode (still ACTIVE).

---

## 9. Architecture Mapping (Deferred to Separate ADR)

Mapping external patterns to Workbench v6 architecture will happen in a **separate ADR** (NOT this OD) and only after:
1. Multi-round Architecture Review.
2. v6.10+ Roadmap formal proposal.
3. Cross-product Tier A evidence collection (per ADR-009).

Until then, OD-EX0-001 is **Observation evidence only**.

---

## 10. Recommended Next

1. **Architecture Mapping ADR** — separate document, not OD.
2. **Pattern Validation** — for each Pattern A-G, verify whether Workbench v6 already covers it.
3. **Future Roadmap Re-entry** — only when v6.10+ planning formally opens.

---

## 11. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial External Pattern Observation. 4 built-in agents + 16 system skills + 2-layer memory pattern observed. No source code accessed. No personal data extracted. Pattern A-G recorded for future Architecture Mapping (separate ADR). |