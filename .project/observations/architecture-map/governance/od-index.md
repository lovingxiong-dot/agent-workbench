# OD (Observation Log) Index

> **Layer**: 1 — Architecture Governance
> **Type**: Observation records (NOT decisions, NOT contracts)

---

## Index

| OD | Title | Domain | Status |
|----|-------|--------|--------|
| [OD-R0-004](../../OD-R0-004-runtime-replay-preparation.md) | Runtime Replay Validation Preparation | Runtime Replay | 4 PASS + Q5 OBSERVATION REQUIRED |
| [OD-C0-001](../../OD-C0-001-consumer-boundary-observation.md) | Consumer Boundary Observation | Consumer | v1.1, 4 questions PASS, low diversity |
| [OD-C0-002](../../OD-C0-002-observation-consumer-feasibility.md) | Observation Consumer Feasibility | Consumer | v1.1, 3 questions PASS |
| [OD-C0-003](../../OD-C0-003-consumer-diversity-observation.md) | Consumer Diversity Observation | Consumer | v1.0, 3 found / 6 absent |
| [OD-G0-001](../../OD-G0-001-architecture-evolution-rule.md) | Architecture Evolution Rule | Governance | PROPOSAL |
| [OD-EX0-001](../../OD-EX0-001-external-agent-ecosystem-pattern.md) | External Agent Ecosystem Pattern | External Pattern | Observation complete |
| [OD-EX0-002](../../OD-EX0-002-external-agent-ecosystem-insight.md) | External Agent Ecosystem Insight | Architecture Insight | Insight recorded |
| [OD-EX0-003](../../OD-EX0-003-v6-constitution-external-synthesis.md) | v6 Constitution + External Synthesis | Architecture Insight | v1.0, No decision |

## Coverage Map

| Domain | Coverage |
|--------|----------|
| Runtime Event Stream | OD-R0-004 ✅ |
| Consumer Boundary | OD-C0-001/002/003 ✅ |
| Architecture Discipline | OD-G0-001 ✅ |
| External Pattern | OD-EX0-001/002/003 ✅ |
| Provider Boundary | NOT in OD series (deferred to behavioral ADR) |
| Foundation Contract | ADR-009 covers promotion tier |
| A1 Validation | NOT YET (Step 1 pending authorization) |
| Architecture Knowledge Map | THIS consolidation (EX-1) |

## Long-term Rule

> **Observation precedes Abstraction.**
>
> Sequence: Observation → Validation → Promotion → Extraction.

Anti-pattern to avoid:
```
Idea → Create folder → Create protocol → Create abstraction
```

## What This Index Does NOT Do

- ❌ Does NOT propose new observation.
- ❌ Does NOT close gaps prematurely.
- ❌ Does NOT modify past observations.