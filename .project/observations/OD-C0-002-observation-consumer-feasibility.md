# OD-C0-002 — Observation Consumer Feasibility Record

> **Type**: Capability Probe (NOT Feature Development, NOT Product)
> **Date**: 2026-07-23
> **Scope**: Verify existing ReplayService can answer three Diagnostic Questions
> **Status**: PROBE COMPLETE

---

## Title

Observation Consumer Feasibility Probe (Phase 2-E.2)

## Purpose

Answer three diagnostic questions about whether `v6/runtime/replay.py` (Passive Observation Consumer, location-bound) can serve as the basis for a future Debugger Consumer, **WITHOUT** modifying Runtime.

This is **NOT**:
- A debugger product design.
- A consumer architecture extraction.
- A trace schema freeze.

This IS:
- A probe of existing capability.
- A record of feasibility evidence.
- A record of remaining gaps (for future consumer-side resolution).

## Method

1. **Inspect** `v6/runtime/replay.py` API surface.
2. **Reconstruct** a hypothetical Task Timeline from the existing API.
3. **Identify** gaps that would force Runtime modification.

No code is written. No consumer directory is created.

---

## Existing Capability: `v6/runtime/replay.py`

### API Surface (only public / intended-for-use methods)

| Method | Returns | Purpose |
|--------|---------|---------|
| `ReplayService.attach(event_bus)` | None | Bind to EventBus, subscribe to all RuntimeEventType |
| `ReplayService.log` | `ReplayLog` | Access log |
| `ReplayService.import_from_trace(trace, task_id)` | `int` | Import existing RuntimeTrace steps |
| `ReplayLog.records()` | `List[ReplayRecord]` | Snapshot all records |
| `ReplayLog.filter(task_id, component, event_type)` | `List[ReplayRecord]` | Filter records |
| `ReplayLog.timeline(task_id)` | `List[Dict]` | Sort by timestamp, return dicts |
| `ReplayLog.export()` | `Dict` | Full export |
| `ReplayLog.clear()` | None | Wipe log |
| `ReplayRecord.from_event(event)` | `ReplayRecord` | Convert RuntimeEvent to record |
| `ReplayRecord.to_dict()` | `Dict` | Serialize |

### Behavior

- `attach()` subscribes to ALL 24 RuntimeEventType values (covers full lifecycle).
- `_on_event()` converts each event to ReplayRecord (immutable).
- `import_from_trace()` reads RuntimeTrace steps as historical evidence.
- `timeline()` returns sorted by timestamp.
- NO Engine invocation. NO Session mutation. NO EventBus modification.

**Capability Profile**:
- ✅ Passive subscriber
- ✅ Per-task evidence collection
- ✅ Snapshot + timeline + filter + export
- ✅ Cross-task aggregation (consumer-side, via filter)
- ❌ Real-time UI rendering (no built-in view layer)
- ❌ Persistent storage (consumer responsibility, NOT in file)

---

## Diagnostic Question 1: Event Stream Is Enough?

**Question**: Can the existing Event Stream produce a Task Timeline like:
```
00:01 Request
00:02 Decision
00:03 Tool
00:05 Response
```

**Probe result**: **YES (with one caveat)**

**Evidence**:

`ReplayRecord` carries:
- `timestamp` (epoch float, sorted by `timeline()`)
- `event_type` (e.g., `task.started`, `engine.selected`, `tool.started`, `task.completed`)
- `component` (e.g., `engine:llm`, `runtime`, `tool:search`)
- `task_id` (filter key)
- `input_snapshot` / `output_snapshot` / `metadata` (from payload)

A consumer can reconstruct:
```
[t] 00:01.000  task.started          runtime          request_id=...
[t] 00:01.050  user_message         runtime          text="..."
[t] 00:01.100  capability.resolved  runtime          capability=chat
[t] 00:01.150  engine.selected      engine:llm       engine=openai
[t] 00:01.200  engine.started       engine:llm
[t] 00:01.500  ai_chunk             engine:llm       text="Hello"
[t] 00:02.000  ai_chunk             engine:llm       text=" world"
[t] 00:02.500  ai_end               engine:llm       text="Hello world"
[t] 00:02.550  engine.completed     engine:llm
[t] 00:02.600  task.completed       runtime
```

**Caveat (from OD-R0-004 Q5)**:
- `trace_id` field on ReplayRecord falls back to `event.task_id` if `event.trace_id` is empty (`replay.py:70`).
- Per-event `parent_id` not present in `ReplayRecord` (RuntimeTrace keeps it; ReplayRecord does not propagate).
- `phase` not surfaced (consumer would need to infer from `event_type`).

These caveats are **consumer-side solvable** without Runtime modification.

**Result**: PASS — Event Stream + ReplayRecord is sufficient to reconstruct Task Timeline. Caveats are consumer-absorbable.

---

## Diagnostic Question 2: Does Runtime Need New Fields?

**Question**: Are there gaps in current Runtime evidence that would force Runtime modification to build a Debugger Consumer?

**Probe result**: **NO new Runtime field needed (yet).**

**Gap inventory** (consumer-side resolvable):

| Gap | Source | Consumer-Side Resolution |
|-----|--------|---------------------------|
| `trace_id` empty in many events | OD-R0-004 Q5 Gap 1 | Use `task_id` as trace proxy |
| `parent_id` partial | OD-R0-004 Q5 Gap 2 | Reconstruct tree from `event_type` precedence rules |
| `phase` free-form | OD-R0-004 Q5 Gap 3 | Map known events to canonical phase table |
| `payload` schema drift | OD-R0-004 Q5 Gap 4 | Defensive access (`payload.get("key", default)`) |
| No real-time subscription for Debugger View | Runtime limitation | Polling `timeline()` is acceptable for human-rate debug |

**Decision matrix**:

| Resolution Path | Requires Runtime Modification? |
|-----------------|-------------------------------|
| Use `task_id` as trace proxy | No |
| Reconstruct parent tree from event_type rules | No |
| Maintain consumer-side phase mapping table | No |
| Defensive payload access | No |
| Polling for human-rate debug | No |

**Result**: PASS — All identified gaps are consumer-side resolvable. No Runtime field addition required for Phase 2-E.2 scope.

**Note**: If a future Consumer needs **real-time** Debugger View (sub-second latency), polling may not suffice. That would justify a new Runtime feature (event push to Consumer). Out of Phase 2-E.2 scope.

---

## Diagnostic Question 3: Can Consumer Evolve Independently?

**Question**: Can the Consumer (ReplayService + future Debugger) evolve without Runtime modification?

**Probe result**: **YES**

**Evidence**:

`v6/runtime/event_bus.py` provides:
- `subscribe(event_type: str, callback)` — public, additive.
- `unsubscribe(event_type, callback)` — public.
- `add_trace_hook(task_id, trace)` — public.

`RuntimeEvent` dataclass provides:
- `type`, `payload`, `task_id`, `source`, `trace_id`, `phase`, `timestamp`.

These fields are **stable** for the Consumer side. Consumer can:
1. Subscribe to new event types without Runtime change.
2. Filter and project without Runtime change.
3. Maintain consumer-side index (e.g., task_id → records) without Runtime change.
4. Build consumer-side persistence layer without Runtime change.

**Runtime modification required when?**:
- New event type needed: requires Runtime publish path change (deferred — none needed yet).
- New event payload field: requires Runtime publish path change (deferred — none needed yet).
- Real-time push API: requires Runtime change (deferred — not needed for Phase 2-E.2).

**Result**: PASS — Consumer can evolve independently for the observed scope. Runtime modification only required for features OUT of scope (real-time push, new event types).

---

## Probe Summary

| Diagnostic Question | Result | Required Runtime Change |
|---------------------|--------|-------------------------|
| Q1 Event Stream sufficiency | PASS (with caveat) | None |
| Q2 Runtime new field need | PASS | None (consumer-side resolvable) |
| Q3 Consumer independent evolution | PASS | None for Phase 2-E.2 scope |

---

## Implication for Phase 2-E.3+

### What is now PROVEN (evidence-based)

1. `ReplayService` (existing) is a viable Observation Consumer.
2. Task Timeline reconstruction is feasible WITHOUT Runtime modification.
3. All identified evidence gaps can be absorbed Consumer-side.
4. Consumer evolution can proceed independently.

### What is NOT PROVEN (deferred to future probes)

1. Real-time (push-based) Debugger view — requires EventBus push API.
2. Cross-task aggregation views (e.g., workflow timeline across multiple tasks) — requires consumer-side index, NOT yet implemented.
3. Persisted replay records (current ReplayLog is in-memory) — requires consumer-side storage, NOT yet implemented.
4. ReplayRecord export to debugger-protocol format — NOT yet specified.

### What this probe does NOT justify

- Moving `replay.py` to a new location.
- Creating a `consumer/` directory.
- Designing a Debugger Protocol.
- Freezing a Trace Schema.

---

## Architecture Stabilization Status (Probe Result)

```
Evidence ≠ Authority   : Established (OD-R0-004 v1.1)
Consumer Taxonomy      : v0.x (PROPOSAL, NOT FROZEN, append-only)
ReplayService          : Validated as Passive Observation Consumer
Debugger Consumer      : Feasible WITHOUT Runtime modification
Runtime modification   : None required for Phase 2-E.2

Recommended next       : Phase 2-E.3 (Real-time push feasibility, separate ADR)
  OR                    : End Phase 2-E series; resume Phase 2-D Workbench v6 closure
```

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Capability Probe. Three diagnostic questions answered. ReplayService validated as Observation Consumer baseline. No Runtime modification recommended. |