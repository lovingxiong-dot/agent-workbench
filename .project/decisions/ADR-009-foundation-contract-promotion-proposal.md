# ADR-009 — Foundation Contract Promotion Proposal

> **Status**: PROPOSAL (NOT Freeze)
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Promotion path from Candidate → Frozen for Foundation Contract

---

## 1. Purpose

This ADR defines the **promotion path** for Foundation Contract symbols. It does **not** freeze any contract. It records:

- Which contracts have been **Workbench-validated** (per ADR-008)
- Which contracts remain **Candidate** (only structurally checked)
- What a second product (e.g., Agent Manager OS) must validate before any Freeze

This ADR enforces the principle that **Foundation must be proven by multiple consumers**, not designed ahead of any consumer.

---

## 2. Promotion Tiers

Foundation Contract symbols are classified into three tiers:

### Tier A — Workbench-Validated (Behavior + Structure)

These symbols have behavioral evidence in Workbench v6 Runtime Closure (ADR-008).

| Symbol | Validation Evidence | Promotable |
|--------|---------------------|------------|
| `InteractionEvent` (data shape) | ADR-008.4.3, 008.4.4 — emitted by `RuntimeEventMapper`, consumed by all Renderers | Yes |
| `RuntimeRequest` (data shape) | ADR-008.4.1, 008.4.2 — single Input boundary via `submit_request` | Yes |
| `_task_to_request` request-id mapping | ADR-008.4.1, 008.4.4 — interaction-layer-local state | Yes |
| `RuntimeEventMapper` (translation point) | ADR-008.2.3 — single translation, no duplicates | Yes (as concept, not exact symbol) |

### Tier B — Structurally Checked Only

These symbols have structural evidence but lack behavioral validation.

| Symbol | Structural Evidence | Promotable |
|--------|---------------------|------------|
| `ProviderProtocol` enum | ADR-008.4.5 — exists in code, never behaviorally tested | No |
| `ProviderEndpoint` | ADR-008.4.5 — Provider Adapter shape | No |
| `GatewayMode` enum | ADR-008.4.5 — single_runtime / multi_runtime / federation | No |
| `EventEnvelope` | ADR-008.4.3 — Mapper emits InteractionEvent, not EventEnvelope directly | No |
| `AgentIdentity` / `AgentSession` / `AgentMessage` | Overlaps with `shell/protocol.py` (ADR-007 §3.1 HIGH risk) | No |
| `WorkflowState` / `WorkflowStep` | Overlaps with internal Orchestrator state | No |
| `CapabilityDefinition` / `CapabilityParameter` / `CapabilityCategory` | CapabilityRegistry exists, but Registry → Foundation dataclass mapping not validated | No |

### Tier C — Not Yet Defined

These concepts exist in Workbench but have not been extracted into `presentation/protocols/foundation/` because Workbench's internal shape is sufficient.

| Concept | Workbench Location | Status |
|---------|---------------------|--------|
| `ExecutionContext` (Task context) | `runtime.context.RuntimeContext` | Workbench-internal |
| `RuntimeTrace` | `Orchestrator` + EventBus hooks | Workbench-internal |
| Capability routing policy | `Orchestrator._resolve_capability` + `CapabilityRouter` | Workbench-internal |
| Provider health / retry / fallback | `services/*_provider.py` | Workbench-internal |

---

## 3. Promotion Criteria (for Tier A → Frozen)

A Tier A symbol becomes **Frozen** only when:

1. **Workbench behavioral validation** is complete (ADR-008 evidence).
2. **Second consumer** (Agent Manager OS, IDE Plugin, Mobile, etc.) consumes the same symbol without modification.
3. **Cross-product stability** holds for at least one minor version cycle.
4. **No pending deprecation** in Workbench.

Until all four conditions hold, the symbol remains **Candidate**.

---

## 4. Promotion Criteria (for Tier B → Tier A)

A Tier B symbol moves to Tier A only when:

1. **Behavioral test** exercises the symbol in a real scenario.
2. **Test result** is recorded in ADR-008 (or successor ADR).
3. **Behavior** matches the structural description (no surprise semantics).
4. **Second consumer** agrees to consume the symbol.

Until behavioral testing is recorded, Tier B symbols stay in `presentation/protocols/foundation/` as **Candidate** (non-binding, may be removed or renamed).

---

## 5. What This ADR Does NOT Do

This ADR does **NOT** freeze any Foundation Contract symbol. It only defines the promotion path.

| Concern | This ADR | A real Freeze ADR would |
|---------|----------|--------------------------|
| Define promotion criteria | Yes | n/a |
| Freeze symbols | No | Yes |
| Replace Workbench-internal types | No | Yes |
| Allow consumer-side modification of frozen symbols | No | Yes (read-only after freeze) |

---

## 6. Cross-Product Validation Requirement

The current Workbench v6 Runtime Closure (ADR-008) proves:

```
Workbench v6
    |
    |
Runtime
```

is stable.

It does **NOT** prove:

```
Workbench v6
    \
     Foundation
    /
Agent Manager OS
```

is stable.

The second leg requires:
- Agent Manager OS consumes Foundation Contract (Tier A symbols).
- Agent Manager OS does NOT fork or modify Tier A symbols.
- Agent Manager OS exposes additional Capability/Provider needs → recorded as Tier B → promoted to Tier A.

This is the **missing leg** before any Freeze.

---

## 7. Recommended State

| Asset | Recommended Status | Why |
|-------|-------------------|-----|
| `FOUNDATION.md` | Frozen (Identity) | Defines what is shared, not how |
| `presentation/protocols/foundation/` | Candidate v0.5 | Symbols may change without notice |
| `AgentRuntime` / `Gateway` Protocol | Candidate v0.5 | Tier B — no second consumer |
| `InteractionEvent` shape | Candidate v0.5 | Tier A structurally, but Provider coexistence not tested |
| `ProviderProtocol` enum | Candidate v0.5 | Tier B — behavioral untested |
| Workbench v6 internal types | Workbench-internal | NOT promoted to Foundation |

---

## 8. Next Steps

1. **Phase 2-D.4**: Runtime Replay / Trace Validation (see ADR-008 §7 next milestone).
2. **Behavioral Provider Validation** (separate ADR, after Phase 2-D.4).
3. **Agent Manager OS** (or second consumer) starts consuming Tier A symbols only.
4. **After one minor cycle**: re-evaluate Tier A → Frozen candidates.

Foundation Contract Freeze is **deferred** until both legs of the cross-product validation are evidenced.

---

## 9. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Foundation Contract Promotion Proposal. Three-tier classification. Freeze deferred to second consumer. |