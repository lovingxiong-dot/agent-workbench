# ADR-008 — Runtime Closure Validation

> **Status**: ACTIVE — In Progress
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Workbench v6 Runtime closure validation before any Foundation Freeze

---

## 1. Purpose

This ADR defines the **validation gate** that must pass before any Foundation Contract can be frozen at v1.0.

**Critical principle**: Protocol must be extracted from real Runtime, not designed ahead of Runtime.

The order is:
```
Reality Implementation
    ↓
Observed Pattern
    ↓
Contract Extraction
    ↓
Freeze
```

This ADR enforces that order.

---

## 2. Validation Gate

Foundation Contract v1.0 Freeze requires **all four validation loops** to close:

### 2.1 Runtime Identity Loop

Validates: `Agent Identity → Agent Runtime → Capability Runtime`

Test criteria:
- Each Agent has a unique, stable Identity (name, type, version, system_prompt)
- Runtime can spawn, pause, resume, terminate individual Agents
- Capabilities can be discovered, invoked, and routed within an Agent context

Pass condition: All four lifecycle operations (spawn/pause/resume/terminate) work end-to-end.

### 2.2 Event Flow Loop

Validates: `InteractionEvent → Gateway → Runtime`

Test criteria:
- Every user interaction produces exactly one InteractionEvent
- Gateway forwards event to correct Runtime instance
- Runtime processes event and produces response events
- Event correlation IDs preserve causality

Pass condition: Multi-turn conversation preserves context across Gateway hops.

### 2.3 Provider Boundary Loop

Validates: `Provider Adapter → Provider Registry → LLM Backend`

Test criteria:
- Provider Adapter wraps any LLM backend (OpenAI / DeepSeek / Claude / etc.)
- Provider Registry discovers and routes to correct Adapter
- Provider lifecycle (register/unregister/health) works without Runtime restart

Pass condition: Switching Provider mid-session does not break Runtime state.

### 2.4 Data Flow Loop

Validates: `Input → Context → Execution → Output`

Test criteria:
- User Input is normalized into Context
- Context drives Execution (single Agent or Workflow)
- Execution produces structured Output
- Output is consumable by both Renderer and other products

Pass condition: Data flow can be replayed end-to-end from Input to Output with deterministic shape.

---

## 3. Where to Validate

The validation happens inside **Workbench v6**. Workbench v6 is the experiment field where these loops are tested against real users.

```
Workbench v6 (experiment field)
    ↓
Real users exercise all four loops
    ↓
Observed patterns inform Foundation Contract
```

If a loop cannot be closed in Workbench v6, it cannot be frozen in Foundation Contract.

---

## 4. Validation Records

Each closed loop must produce a validation record:

| Loop | Status | Record Location |
|------|--------|-----------------|
| 2.1 Runtime Identity | pending | TBD after Phase 2-D.2 |
| 2.2 Event Flow | pending | TBD after Phase 2-D.2 |
| 2.3 Provider Boundary | pending | TBD after Phase 2-D.2 |
| 2.4 Data Flow | pending | TBD after Phase 2-D.2 |

When all four loops have a record marked `closed`, this ADR is complete and `ADR-009 Foundation Contract v1.0 Freeze` can be proposed.

---

## 5. What This ADR Does NOT Do

This ADR does **not** freeze Foundation Contract. It defines the gate, not the contract.

| Concern | This ADR | Foundation Freeze |
|---------|----------|------------------|
| Symbol shapes | No | Yes |
| Runtime name ownership | No | Yes |
| Provider enumeration | No | Yes |
| Data contract unification | No | Yes |

---

## 6. Foundation Status After This ADR

```
Foundation Contract v0.5: Candidate (non-binding)

Authority: NONE
Binding: NON-BINDING
Validation: PENDING (this ADR)
Next Milestone: Phase 2-D.2 Renderer Migration
```

The Foundation Contract at `presentation/protocols/foundation/` is a **candidate**, not a contract. Workbench v6 implementation is the source of truth until validation records close.

---

## 7. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Runtime Closure Validation ADR. |