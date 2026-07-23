# OD-EX0-003 — v6 Constitution + External Pattern Architecture Insight

> **Type**: Architecture Insight Report (NOT ADR, NOT RFC, NOT Decision)
> **Date**: 2026-07-23
> **Scope**: Track A (v6 Constitution Deep Read) + Track B (minimax Comparative) Synthesis
> **Status**: INSIGHT RECORDED
> **Mode**: R0 Research (Architecture Agent + Guardian)
> **Authorization**: Intent First, Risk Bounded, Existing Capability First

---

## Output Format (As Required)

```
Section 1: Existing Strength
Section 2: External Gap
Section 3: Potential Future Boundary
Section 4: No Decision Yet
Section 5: Candidate ADR (DRAFT ONLY, NOT SUBMITTED)
```

---

## Section 1: Existing Strength (v6 Constitution Internal Strengths)

Track A — v6 Constitution v6.13-frozen (2026-07-21) observed:

### 1.1 Five Principles Already Established

| Principle | Status | Notes |
|-----------|--------|-------|
| **P1**: Workbench OS Identity | Frozen | "AI Agent OS, Desktop UI is one Shell" |
| **P2**: Runtime Kernel Freeze | Frozen | 14 modules + 12 RuntimeModules all frozen since v6.9.6 |
| **P3**: Presentation Contract | Frozen | Protocol + ViewModel + Adapter (3-layer) |
| **P4**: UI Shell Boundary | Frozen | UI Shell consumes Presentation Contract only |
| **P5**: Configuration-Driven Workbench | Frozen | All extensions via UI registration, no code change |

### 1.2 Irreversible Dependency Direction (Already Defined)

```
Agent → Skill → Capability → Engine → Provider → Tool
```

**Significance**: This is **architecturally ahead of** minimax's "Agent → Skill → Tool" pattern. v6 has already introduced an abstraction layer (Capability) that allows Skills to compose without binding to specific Tools.

### 1.3 Layered Architecture (Already Defined)

```
Workbench OS
├── Runtime Kernel (frozen)
├── Core Foundation (frozen)    Agent/Capability/Event/Registry/Lifecycle
├── Presentation Layer
│   ├── Protocol   (capability contract)
│   ├── ViewModel  (data structure)
│   └── Adapter    (translation logic)
├── UI Shell (replaceable)
│   ├── shells/qt/    (current)
│   ├── shells/web/   (future)
│   ├── shells/mobile/(future)
│   └── shells/cli/   (future)
└── Adapter Ecosystem
```

### 1.4 Configuration-Driven Loop (Already Proven)

```
UI → ConfigManager → Registry Reload → Capability Update → Agent Ready
```

vs. anti-pattern:
```
UI → 修改代码 → 重新编译 → 重新启动
```

This is a **mature product boundary** that minimax has not yet exposed.

### 1.5 Recent Constitution State (v6.14.0-alpha)

- Presentation Boundary Freeze
- Renderer Layer independent
- v6/ui Foundation Frozen

### 1.6 Existing Capability Inventory (Workbench v6)

From [OD-EX0-002](../observations/OD-EX0-002-external-agent-ecosystem-insight.md) mapping:

| External Pattern | Workbench v6 Coverage |
|------------------|----------------------|
| Pattern 1-6 (Foundation) | ✅ **Aligned or ahead** |
| Runtime Kernel freeze | ✅ Stronger than minimax |
| Orchestrator + Worker | ✅ Runtime-internal |
| Differentiation in Runtime | ✅ Ahead of external file-based |
| Capability composition | ✅ Ahead of external skill assignment |

---

## Section 2: External Gap (Where v6 Lags Behind minimax Pattern)

Track B — comparison against minimax's 13 patterns.

### 2.1 Missing Dimension: Personal Assistant Agent Layer

**minimax pattern**: 1 orchestrator (`mavis`) + N workers (`coder/verifier/general`). User has long-term identity with the orchestrator.

**Workbench v6 reality**: v6 Constitution has NO concept of:
- ❌ Personal Assistant Agent
- ❌ Multi-Agent coordination
- ❌ Agent Switching / Routing
- ❌ Orchestrator Agent as user-facing entity

**Grep result** (validated):
```
$ grep -r "Multi-Agent\|Personal Assistant\|Agent Manager" docs/v6/
  → No matches

$ grep "orchestrat\|Personal\|Manager\|Switching" docs/v6/
  → Only "DecisionManager" (Runtime-internal, NOT user-facing)
```

### 2.2 Missing Dimension: Per-Agent Memory Isolation

**minimax pattern**: Each agent has own `memory/daily/YYYY-MM-DD.md`. Two-layer split (semantic MD + structural JSON).

**Workbench v6 reality**: 
- `SessionModule` is **session-scoped**, not agent-scoped.
- No physical isolation between potential agents.
- No append-only-by-date memory convention.

### 2.3 Missing Dimension: Skill-as-Filesystem-Module

**minimax pattern**: Skill is a self-describing directory with `SKILL.md` (standard skeleton) + `references/` + `scripts/`.

**Workbench v6 reality**: Capability is **code-level Python object** in `agent_workbench/runtime/capability/`. No filesystem-level skill definition. No user-contributed skills (yet).

### 2.4 Missing Dimension: Self-Extension via Meta-Skills

**minimax pattern**: 3 of 16 skills are meta-skills (`create-agent`, `skill-creator`, `skill-refiner`). System can extend itself.

**Workbench v6 reality**: `RuntimeModule` is **frozen** (P2). No runtime self-extension path. Configuration-driven (P5) is the extension mechanism, but it operates on existing object types.

### 2.5 Missing Dimension: Workspace per Agent

**minimax pattern**: Each agent has own `workspace/` (side-effect area).

**Workbench v6 reality**: `WorkspaceHost` exists for **UI workspaces** (chat, provider, skill, tool), not for per-Agent workspaces.

---

## Section 3: Potential Future Boundary (NOT Design, Just Insight)

These are **observations**, not proposals. They might inform future v6.10+ planning.

### 3.1 Possible Boundary Position (For Future Discussion)

```
                    Workbench OS
                          |
        +-----------------+-----------------+
        |                                   |

   Runtime + Capability              Future Layer
   + Renderer (current)            (NOT YET DEFINED)
                                          |
                                  +-------+-------+
                                  |               |
                            Agent Identity    Multi-Agent
                              Layer           Orchestration
                                                |
                                          +-----+-----+
                                          |           |
                                      Personal    Specialized
                                      Assistant   Agent Pool
```

**Critical observation**: The "Future Layer" **does not exist** in v6 Constitution. It is a **gap**, not a design.

### 3.2 Possible Position for Memory Layer

If Memory Layer is ever added:
```
Possible location:
  Memory Service (Runtime-coupled)
  vs.
  Memory System (Agent-coupled, Runtime-agnostic)

v6 Constitution favors:
  Runtime-coupled services (P2 freeze)

External product favors:
  Agent-coupled, Runtime-agnostic

Insight:
  - Runtime-coupled: easier Foundation, harder multi-agent
  - Agent-coupled: harder Foundation, easier multi-agent

  v6 already chose easier-Foundation path.
  Multi-Agent is a LATER concern.
```

### 3.3 Possible Position for Personal Assistant Agent

If Personal Assistant Agent is ever added:
```
Candidates:
  Option A: Personal Assistant = new Runtime-level module  ← violates P2
  Option B: Personal Assistant = Application-level entry      ← consistent with P3
  Option C: Personal Assistant = Identity Configuration       ← consistent with P5

Observation: 
  Option B or C aligns with v6 Constitution principles.
  Option A would require Constitution revision.
```

---

## Section 4: No Decision Yet (Explicit Deferral)

The following questions **remain open** and **must NOT be answered in this Observation**:

1. ❌ Should Workbench v6 add Multi-Agent support?
2. ❌ Should Workbench v6 add Personal Assistant Agent?
3. ❌ Should Memory Layer be Runtime-coupled or Agent-coupled?
4. ❌ Should Skills become filesystem modules?
5. ❌ Should Agent Manager OS be a separate product or integrated?

These are **future Architecture Review topics**, deferred to:
- v6.10+ Roadmap (when current A/B-line tasks complete)
- Multi-round Architecture Review (not yet started)
- ADR process (when Tier A evidence is collected per ADR-009)

**Current Verdict**: ✅ **No Decision Yet.** This Observation is evidence only.

---

## Section 5: Candidate ADR Draft (DRAFT ONLY, NOT SUBMITTED)

If a future ADR were to be drafted, here is a **skeleton**. **NOT** to be submitted until:
- Multi-round Architecture Review.
- Tier A evidence collected (per ADR-009).
- Explicit user authorization.

---

### ADR-DRAFT-010 (NOT SUBMITTED) — Personal Assistant Agent & Multi-Agent Orchestration

#### Status: DRAFT ONLY (NOT SUBMITTED)

#### Background (For Future Reference)

- OD-EX0-001: External Pattern Observation
- OD-EX0-002: External Architecture Insight
- OD-EX0-003: v6 Constitution + External Synthesis (this document)

#### Proposed 5 Design Questions (Open)

1. **Personal Assistant 是否是 Workbench 的唯一入口？**
   - Candidate answer: NOT necessarily — depends on user context
   - Status: OPEN

2. **Agent Manager 放在哪一层？**
   - Candidate: Application-level entry (P3-aligned)
   - Status: OPEN

3. **Agent 与 Skill 的边界？**
   - Candidate: Agent = Persona + Capability Composition
   - Status: OPEN

4. **Memory 如何绑定 Agent？**
   - Candidate: Per-Agent Memory (external pattern) vs Session-coupled (current)
   - Status: OPEN

5. **自动委派的状态机如何设计？**
   - Candidate: DecisionManager extension? New Orchestrator Runtime?
   - Status: OPEN

#### Submission Requirements (NOT YET MET)

- [ ] Multi-round Architecture Review (currently 0/3)
- [ ] Tier A evidence from second consumer (per ADR-009)
- [ ] Explicit user authorization to draft
- [ ] Resolution of 5 open questions above

#### Risks

- **R1**: Runtime Kernel pollution if Agent Manager becomes Runtime-level (violates P2).
- **R1**: Constitution violation if Personal Assistant Agent becomes Runtime-level.
- **R2**: Speculative abstraction without evidence (violates OD-G0-001).
- **R0**: No immediate need (current Foundation is structurally sound).

---

## What This Insight Does NOT Do

- ❌ Does NOT propose Workbench v6 changes.
- ❌ Does NOT freeze any future direction.
- ❌ Does NOT submit ADR-010.
- ❌ Does NOT modify Runtime / Protocol / Foundation.
- ❌ Does NOT trigger AD-A1-005.
- ❌ Does NOT adopt external implementation.
- ❌ Does NOT bypass Observation precedes Abstraction principle.

---

## Observations precede Abstraction (Long-term Rule)

This Insight demonstrates the rule:

```
1. Observation   (OD-EX0-001: pattern extraction)
2. Validation    (OD-EX0-002: Workbench v6 mapping)
3. Insight      (OD-EX0-003: this document)
4. ADR (future)  (only after Tier A evidence)
5. Implementation (only after ADR)
```

Without this sequence, the project would risk:
- ❌ Idea → Create folder → Create protocol → Create abstraction (the anti-pattern loop)

---

## Strategic Verdict

```
Workbench v6 Constitution:    ✅ HEALTHY (v6.13-frozen, 5 Principles established)
Foundation:                  ✅ SOUND (Runtime Kernel frozen since v6.9.6)
External Patterns:           ✅ OBSERVED (13 patterns, mapped, gaps named)
Multi-Agent Layer:           ⚠️ NOT YET (gap recorded, not design)
Personal Assistant Agent:    ⚠️ NOT YET (gap recorded, not design)
Memory Layer:                ⚠️ NOT YET (Runtime-coupled vs Agent-coupled pending)
Skill Ecosystem:             ⚠️ PARTIAL (Capability exists, filesystem-level not yet)
Configuration-Driven:        ✅ STRONG (P5 proven via v6.10)

No Decision Yet.
No ADR Submitted.
No Change Proposed.
Insight Recorded.
```

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Architecture Insight Report. Section 1-5 format. Track A (v6 Constitution) + Track B (minimax comparative) synthesis. No decision, no ADR, no proposal. |