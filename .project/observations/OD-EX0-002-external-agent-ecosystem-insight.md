# OD-EX0-002 — External Agent Ecosystem Architecture Insight

> **Type**: Architecture Insight Report (NOT ADR, NOT RFC)
> **Date**: 2026-07-23
> **Scope**: Strategic insight from external product pattern observation
> **Status**: INSIGHT RECORDED
> **Authorization**: Research-capable Guardian mode (intent-first, risk-bounded)

---

## Purpose

Provide a **Chief Architect / Engineering Lead style insight** on what Workbench v6 can learn from external agent ecosystem patterns (minimax-style). This is NOT a Workbench v6 change proposal. It is a **strategic input** for future v6.10+ Roadmap.

This report respects:
- ✅ Existing Capability First (OD-G0-001)
- ✅ Evidence ≠ Authority
- ✅ Intent First Principle
- ✅ Three Guardrails (Runtime Kernel / Protocol Contract / Foundation Boundary modification)

---

## 1. External Product Patterns (Summary)

From [OD-EX0-001](../observations/OD-EX0-001-external-agent-ecosystem-pattern.md):

```
.minimax/
├── agents/             # 4 built-in roles (orchestrator + workers)
│   └── <name>/
│       ├── config.yaml     # Identical across agents
│       ├── memory/daily/   # Per-agent isolated
│       ├── sessions/       # Runtime-filled
│       ├── skills/         # Empty (uses system skills)
│       └── workspace/      # Runtime-filled
├── .builtin-skills/    # 16 system skills
│   └── <name>/
│       ├── SKILL.md         # Standard metadata
│       ├── references/      # Documentation
│       ├── scripts/         # Executable helpers
│       └── (assets / docs / steps / cli-skills per skill type)
├── memory/tracking/    # Cross-agent tracking JSON
├── bin/                # CLI utilities
└── workspace/          # Shared runtime workspace
```

### Confirmed Patterns (13 total)

| # | Pattern | Implication |
|---|---------|-------------|
| 1 | Two-tier skill architecture | Skills are composed, not assigned |
| 2 | Memory split (per-agent + cross-agent) | Memory has privacy boundaries |
| 3 | Workspace per-agent | Workspace is side-effect area |
| 4 | 4 agents: 1 orchestrator + 3 workers | Role taxonomy exists |
| 5 | Naming distinguishes role type | Role is semantic, not file-level |
| 6 | Identical config.yaml | Differentiation in runtime, not file |
| 7 | 3-layer skill taxonomy | Meta / Primitive / Domain / Integration |
| 8 | Self-extension built-in | 19% of skills are meta-skills |
| 9 | Two-layer memory | Semantic (MD) + Structural (JSON) |
| 10 | Append-only by date | Daily log immutable |
| **11** | **Skill is filesystem module** | Self-contained directory with SKILL.md |
| **12** | **Skill has dual layer (refs + scripts)** | Static + executable |
| **13** | **Skill size varies (2-20KB)** | Heterogeneous capability bundle |

---

## 2. Workbench v6 Current State (Reference)

| Layer | Status | Evidence |
|-------|--------|----------|
| Foundation Runtime | **Frozen** | v6.9.6 kernel boundary |
| Runtime Event Stream | ✅ Validated | RuntimeEventType 24 种 |
| Workbench Renderer | ✅ Closed | Phase 2-D.2 |
| InteractionLayer (Adapter) | ✅ Validated | OD-C0-001 |
| ReplayService (Observation) | ✅ Capability | OD-C0-002 |
| Consumer Diversity | ⚠️ Low (3 found, 6 absent) | OD-C0-003 |
| Foundation Contract v0.5 | ⚠️ Candidate | ADR-007 + ADR-009 |
| A1 Validation | ⏳ Waiting | AD-A1-005 |

---

## 3. Architecture Insight: What Workbench v6 Already Has

Checking Workbench v6 against the 13 external patterns:

| External Pattern | Workbench v6 Coverage |
|------------------|----------------------|
| 1 Two-tier skill | ✅ Capability Layer (`v6/runtime/capability_registry.py`, `agent_workbench/runtime/capability_router.py`) |
| 2 Memory split | ⚠️ Partial — SessionModule exists, but no per-agent memory distinction yet |
| 3 Workspace per-agent | ✅ WorkspaceHost (`v6/runtime/workspace_host.py` — legacy UI controller uses it) |
| 4 Orchestrator + workers | ✅ Runtime Kernel has Orchestrator + Worker pattern (v6.9.x) |
| 5 Naming distinguishes role | ✅ Worker / Orchestrator distinction in Runtime |
| 6 Differentiation in runtime | ✅ Identity / State in Runtime (not file) — **ahead of external product** |
| 7 3-layer skill taxonomy | ⚠️ Capability Layer exists, no explicit meta-skill taxonomy |
| 8 Self-extension built-in | ⏳ Future (v6.10+ Skill Ecosystem) |
| 9 Two-layer memory | ⚠️ RuntimeContext has trace + snapshot, but no semantic/structural separation |
| 10 Append-only by date | ⚠️ SessionModule has append pattern, but no YYYY-MM-DD naming |
| 11 Skill as filesystem module | ⚠️ Capability is code-level, not filesystem-level |
| 12 Skill dual layer | ⏳ Capability has metadata but no separate scripts/ |
| 13 Heterogeneous skill bundle | ⚠️ All capabilities are uniform Python objects |

**Summary**: Workbench v6 has solid Foundation (Pattern 1, 4, 5, 6) but lags on User-facing patterns (Pattern 7, 8, 11, 12, 13).

---

## 4. Insight: Three Strategic Opportunities

### Opportunity 1: Skill Ecosystem (Patterns 7, 8, 11, 12)

**Observation**: External product treats Skill as a **first-class filesystem module** with self-describing metadata (SKILL.md) + dual-layer content (references + scripts). This makes skills **discoverable, composable, and self-extending**.

**Workbench v6 Gap**: Capability exists but is code-level only. No SKILL.md equivalent. No discovery via filesystem scan.

**Strategic Value**: Skill-as-Filesystem would enable:
- User-contributed skills (no Python required).
- Cold-start capability scanning.
- Skill marketplace foundation.

**Risk Boundary**: ⚠️ This affects Capability Layer, NOT Runtime Kernel. Pattern 7/8/11/12 belong to **Skill Ecosystem (v6.10+)** per Roadmap, NOT Foundation Runtime.

**Recommended Phase**: v6.10 (Skill Ecosystem), not v6.9.x Foundation.

---

### Opportunity 2: Per-Agent Memory Isolation (Patterns 2, 9, 10)

**Observation**: External product has **physically isolated** per-agent memory directories. Memory has time dimension (YYYY-MM-DD). Two-layer split (semantic MD vs structural JSON).

**Workbench v6 Gap**: `SessionModule` is **session-scoped**, not **agent-scoped**. If multi-agent arrives, memory ownership becomes ambiguous.

**Strategic Value**: Per-agent memory isolation enables:
- Clear privacy boundary between user-defined agents.
- Append-only-by-time audit trail.
- Multi-agent coordination without state leakage.

**Risk Boundary**: ⚠️ This affects Memory Layer, which is **post-Foundation** per Roadmap. v6.10+ (Knowledge & Memory).

**Recommended Phase**: v6.10 (Knowledge & Memory), not v6.9.x Foundation.

---

### Opportunity 3: Identity Layer (Pattern 4)

**Observation**: External product has clear **orchestrator vs worker** taxonomy. Naming convention (`mavis` as root) signals role type.

**Workbench v6 Reality**: Already has **Orchestrator + Worker** semantics in Runtime Kernel (v6.9.x). This is **ahead of** external product.

**Strategic Value**: This is a **competitive advantage**, not a gap. Workbench v6 should:
- Document existing Orchestrator/Worker boundary clearly.
- Enable user-defined worker types (v6.10+ Persona).
- Keep Orchestrator as a singleton (Foundation invariant).

**Risk Boundary**: ✅ No Foundation change needed. This is **clarification, not addition**.

**Recommended Phase**: Phase 2-D Closure (documentation only).

---

## 5. What Workbench v6 Should NOT Adopt

Three patterns look attractive but contradict Foundation principles:

### Anti-Pattern A: Per-agent skills (Pattern 1 inverse)

External product: per-agent `skills/` is **empty**, all skills are system-wide.
Workbench v6: Capabilities are already **runtime-composed** (Capability / CapabilityChain).
- ✅ No change needed. Capability composition is **already better** than external product's empty per-agent skills.

### Anti-Pattern B: File-based Identity (Pattern 6 inverse)

External product: config.yaml is identical across agents, differentiation in runtime DB.
Workbench v6: Differentiation is already in **Runtime state**, not files.
- ✅ No change needed. Runtime-first identity is **already better**.

### Anti-Pattern C: Tight skill binding to agents

External product: empty per-agent skills suggests skills are **runtime-resolved**, not statically bound.
Workbench v6: Capability is already **runtime-resolved** via CapabilityRouter.
- ✅ No change needed. Capability Router pattern is **already aligned**.

---

## 6. Strategic Recommendation (For Future Roadmap)

**No immediate change required to Workbench v6.**

The current Foundation is **structurally sound** and in some dimensions **ahead of** the external reference product (Pattern 4, 6, Anti-Pattern A/B/C).

**Three future enhancements** (NOT now):

| Phase | Enhancement | Patterns Addressed |
|-------|-------------|-------------------|
| v6.10 | Skill Ecosystem (filesystem-level SKILL.md) | 7, 8, 11, 12, 13 |
| v6.10 | Knowledge & Memory (per-agent isolation, two-layer) | 2, 9, 10 |
| Phase 2-D Closure | Documentation (Orchestrator/Worker boundary clarity) | 4 |

**Trigger Conditions** (when to enter these phases):
- v6.10 starts when Workbench v6.9.x reaches stable user adoption.
- Phase 2-D Closure can start immediately (docs only, no code change).

---

## 7. Risk Re-Assessment

| Risk | Before | After (This Insight) |
|------|--------|----------------------|
| Premature Foundation Freeze | LOW | LOW (no change proposed) |
| External Pattern Adoption | MEDIUM | LOW (insight only, no adoption) |
| Runtime Boundary Drift | LOW | LOW (no Runtime change) |
| Identity Layer Pollution | LOW | LOW (clarification, not addition) |
| Capability Layer Over-design | MEDIUM | LOW (composition > assignment) |

---

## 8. Open Questions (For Future Architecture Review)

1. **Skill Ecosystem Entry Point**: When v6.10 starts, where does the first filesystem-level skill definition live? (`v6/skills/`? `v6.10/skills/`? `agent_workbench/skills/`?)
2. **Per-Agent Memory Schema**: What is the canonical schema for `memory/daily/YYYY-MM-DD.md`?
3. **Identity Singleton Invariant**: Should `orchestrator` be a hardcoded name, or user-configurable?
4. **Multi-Agent Routing**: When `mavis` is the only orchestrator, how do user-defined agents interact? (Routing table? Default orchestrator = user-defined orchestrator?)

These are **NOT blockers** for current Workbench v6. They are **future Architecture Review** topics.

---

## 9. Conclusion

Workbench v6 has a **structurally sound Foundation** that, in some dimensions (Orchestrator/Worker semantics, Runtime-first identity, Capability composition), is **ahead of** external reference product patterns.

External patterns observed provide **future direction signals** but do NOT trigger immediate change. The three opportunities (Skill Ecosystem, Per-Agent Memory, Identity Documentation) align with the **already-planned v6.10+ Roadmap** (Skill Ecosystem + Knowledge & Memory + Phase 2-D Closure).

**Strategic Verdict**: ✅ Workbench v6 architecture is **healthy and future-ready**. No urgent adoption required.

---

## 10. What This Insight Does NOT Do

- ❌ Does NOT propose Workbench v6 changes.
- ❌ Does NOT freeze Skill Ecosystem / Memory Layer direction.
- ❌ Does NOT trigger AD-A1-005.
- ❌ Does NOT modify Foundation Runtime.
- ❌ Does NOT introduce new Contract.
- ❌ Does NOT migrate or adopt external implementation.

---

## 11. Recommended Follow-Up (Optional, Low Priority)

If user wants to deepen the research:

1. **Workbench v6 Capability Audit** — list current capabilities, classify by external taxonomy (Meta / Primitive / Domain / Integration / Workflow).
2. **Future Skill Skeleton** — design SKILL.md-like metadata schema (NOT adoption, just design).
3. **Memory Layer Pre-Design** — sketch how per-agent memory would integrate with existing SessionModule.

These are **optional**, not blockers.

---

## 12. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Architecture Insight Report. 13 external patterns + Workbench v6 mapping + 3 opportunities + 3 anti-patterns + future Roadmap alignment. No change proposed. |

---

**Reviewed by**: Architecture Guardian (Research-capable mode)
**Mode**: Intent First + Risk Bounded + Existing Capability First
**Status**: Insight recorded, awaiting user direction