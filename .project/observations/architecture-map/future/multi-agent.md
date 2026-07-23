# Multi-Agent (Deferred)

> **Type**: Deferred (NOT part of current Workbench v6)
> **Status**: NOT IN SCOPE

---

## Classification

| Aspect | Classification |
|--------|----------------|
| Multi-Agent Coordination | **External Scope (Agent Manager OS)** |
| Multi-Agent Switching | **External Scope (Agent Manager OS)** |
| Multi-Agent Routing | **External Scope (Agent Manager OS)** |

## Why Deferred (NOT Missing)

Workbench v6 has a single Agent Runtime Kernel with Capability composition. Multi-Agent support is:
- ❌ Not part of current product scope.
- ✅ Intentionally left to Agent Manager OS (separate product).

Workbench v6 is a **Runtime Validation Platform**. It validates that a single Agent can run with various Capabilities. Multi-Agent validation belongs to Agent Manager OS.

## Required Evidence for Future Multi-Agent Design

1. ✅ Tier A evidence from second consumer (per ADR-009)
2. ✅ Multi-round Architecture Review
3. ✅ ADR submission with:
   - 5 Open Questions resolved
   - Multi-Agent Boundary Evidence
   - Agent Switching Evidence
   - Routing State Machine Evidence

## Position in 5-Layer Model

```
Workbench v6 Runtime Kernel (single-agent)
    ↓
[Future: Agent Manager OS (multi-agent layer)]
    ↓
Multi-Agent State Machine (NOT YET DESIGNED)
```

## Reference

- [OD-EX0-003 v6 Constitution + External Synthesis §Section 3 Potential Future Boundary](../../OD-EX0-003-v6-constitution-external-synthesis.md)
- [ADR-DRAFT-010 (NOT SUBMITTED)](../../OD-EX0-003-v6-constitution-external-synthesis.md#section-5-candidate-adr-draft-draft-only-not-submitted)

## What This File Does NOT Do

- ❌ Does NOT propose Multi-Agent design.
- ❌ Does NOT prescribe routing algorithm.
- ❌ Does NOT define Agent-to-Agent protocol.
- ❌ Does NOT modify Workbench v6.