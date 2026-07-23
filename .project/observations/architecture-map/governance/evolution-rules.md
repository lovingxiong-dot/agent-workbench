# Architecture Evolution Rules

> **Layer**: 1 — Architecture Governance
> **Status**: PROPOSAL — codifying existing discipline

---

## Source

- [OD-G0-001 Architecture Evolution Rule](../../OD-G0-001-architecture-evolution-rule.md)
- OD-EX0-003 Section 5 (refinement)
- Phase 2-D / Phase 2-E observation series (proven application)

## Rule 1: Observation precedes Abstraction

```
1. Observation   (record what exists)
2. Validation    (probe with diagnostic questions)
3. Insight      (synthesize, NOT design)
4. Promotion    (with Tier A evidence, NOT without)
5. Extraction   (only after multiple consumers exist)
```

Anti-pattern (forbidden):
```
Idea → Create folder → Create protocol → Create abstraction
```

## Rule 2: Behavior > File Location

Architecture ownership is determined by:
- What the module produces (evidence vs authority)
- What boundaries it crosses (passive subscriber vs active invoker)
- What state it owns (per-task evidence vs cross-task history)

NOT by:
- Which directory it lives in
- Which package it imports from
- Which import path is used

**Example**: `v6/runtime/replay.py` ReplayService lives in `v6/runtime/` but is Consumer by behavior.

## Rule 3: Existing Capability First

Before creating any new abstraction:

```
1. Search existing implementation
2. Observe actual behavior
3. Validate boundary
4. Extract only if repeated usage appears

No speculative abstraction.
```

Forbidden moves (without Architecture Review):
- `mv v6/runtime/replay.py consumer/` (file location change for already-working Consumer)
- `cp / cat` external implementation
- Renaming without behavior change

## Rule 4: Intent First + Risk Bounded

```
Intent First Principle:
  用户意图 > 流程模板

Risk Boundary (triggers Strict Review):
  - 修改 Runtime Kernel
  - 修改 Protocol Contract
  - 修改 Foundation Boundary
  - 删除历史 Artifact
  - 影响兼容性的架构变化

Default (低风险):
  - 自主完成 + 汇报
```

## Rule 5: Evidence ≠ Authority

Runtime produces evidence (RuntimeEvent / RuntimeTrace).
Consumers build authority (Debugger / Audit / Governance) OUTSIDE Runtime.

Runtime MUST NOT own:
- Cross-task history aggregation
- Persistent storage (cross-task)
- Governance policy

## Rule 6: Governance Tier Discipline

```
Governance Layer:
  Principles    ← Stable (Frozen)
  Role Model    ← 可演进 (Architecture Review)
  Risk Model    ← 可演进 (Normal governance update)

Modifications:
  Principles → ADR (formal)
  Role Model → Architecture Review
  Risk Model → Normal governance update
```

Avoid governance layer self-overflow.

## Rule 7: Missing vs Out of Product Boundary

When identifying gaps, classify properly:

| Type | Meaning |
|------|---------|
| **Missing** | Current design needs but does not exist |
| **Deferred** | Intentionally postponed |
| **Out of Current Product Boundary** | Belongs to other product (e.g., Agent Manager OS) |

Correct framing:
- ❌ "v6 is incomplete"
- ✅ "v6 completed Runtime OS Foundation, leaves Agent Ecosystem Layer as separate product"

## Application

These rules apply to:
- All Agent (architecture agent, research agent, execution agent)
- All decisions, insights, and code modifications

Guardian enforces Rules 1-3. Research applies Rules 1, 3, 7. Execution applies Rule 4.