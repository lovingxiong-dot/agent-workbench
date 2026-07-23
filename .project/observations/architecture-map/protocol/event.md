# Event Protocols (InteractionEvent + RuntimeEvent)

> **Layer**: 1.5 — Protocol Contracts
> **Type**: Output boundary protocols

---

## Two-Level Event Architecture

```
RuntimeEvent (internal, detailed, 24 types)
    ↓
RuntimeEventMapper (single translation point)
    ↓
InteractionEvent (external, clean, renderer-ready)
    ↓
Renderer (UI Shell consumption)
```

## RuntimeEvent (Internal)

| Field | Description |
|-------|-------------|
| type | RuntimeEventType enum value (24 types) |
| payload | dict (free-form) |
| task_id | Routing key |
| source | Component identifier |
| trace_id | Optional trace grouping (often empty) |
| phase | Optional phase label (often empty) |
| timestamp | Epoch float |

Validation: [ADR-008.4.3 Event Emission Discipline](../../decisions/ADR-008-runtime-closure-validation.md#adr-00843--event-emission-discipline)

## InteractionEvent (External)

| Field | Description |
|-------|-------------|
| type | InteractionEventType (mapped subset) |
| request_id | Causality token |
| source | Original source |
| task_id | Task routing |
| payload | Clean dict for renderer |

Validation: [ADR-008.2.2 Renderer Event Consumption](../../decisions/ADR-008-runtime-closure-validation.md#adr-00822--renderer-event-consumption)

## Mapper (Single Translation Point)

`runtime/interaction/mapper.py:18-124` — `class RuntimeEventMapper`

Validation: [ADR-008.2.3 RuntimeEventMapper as Single Translation Point](../../decisions/ADR-008-runtime-closure-validation.md#adr-00823--runtimeeventmapper-as-single-translation-point)

- Single class definition
- No other file defines RuntimeEvent → InteractionEvent translation
- All rendering flows through this single point

## Q5 Gaps (Recorded)

| Gap | Consumer-Side Resolution |
|-----|-------------------------|
| trace_id empty | Use task_id as trace proxy |
| parent_id partial | Reconstruct tree from event_type precedence |
| phase free-form | Consumer-side mapping table |
| payload schema drift | Defensive access (`.get("key", default)`) |

## Position in 5-Layer Model

```
Layer 0 Runtime (RuntimeEvent emit)
    ↓
Layer 1.5 Protocol Contract (Mapper → InteractionEvent)    ← THIS
    ↓
Layer 4 Application (Renderer consumes InteractionEvent)
```

## Boundary Principle

```
Allowed:
    InteractionEvent stream                          (Renderer consumption)

Forbidden:
    consume RuntimeEvent (internal)                  (implementation leak)
    replay SessionModule raw state                  (state reach-around)
```