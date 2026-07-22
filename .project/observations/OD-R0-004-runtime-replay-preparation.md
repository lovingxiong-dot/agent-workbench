# OD-R0-004 — Runtime Replay Validation Preparation

> **Type**: Observation Log (NOT RFC / NOT ADR)
> **Date**: 2026-07-23 (revised: 2026-07-23)
> **Scope**: Runtime evidence observation only
> **Status**: OBSERVING (Phase 2-D.4 complete; Phase 2-E next)

---

## Title

Runtime Replay Validation Preparation

## Purpose

Determine whether Runtime execution produces **sufficient observable evidence** to support future replay, trace, audit, and governance consumption.

This is an **observation phase**, not a design phase. No new Contract, no Schema, no Protocol is created.

## Scope (In)

- Inspect Runtime event stream (`v6/runtime/event_bus.py`)
- Inspect RuntimeTrace / TraceStep data model
- Inspect how events are emitted at each execution stage
- Inspect how state mutations are reflected (or hidden) in the event stream

## Non-Goals (Out)

- **Trace Protocol** — design
- **Audit Protocol** — design
- **Debugger Architecture** — design
- **Enterprise Audit Model** — design
- **Provider Behavior Freeze** — second consumer not validated
- **Governance Trace Schema** — not yet observed need
- **Persistence Model** — Runtime does not own persistence semantics

---

## Four Observation Questions

### Q1: Event Stream Completeness

**Question**: Does Runtime emit a complete event stream covering Input → Output?

**Evidence observed** (RuntimeEventType in `v6/runtime/event_bus.py:35-83`):

```
Task lifecycle:       TASK_STARTED, TASK_COMPLETED, TASK_FAILED
Capability selection: CAPABILITY_RESOLVED, MANAGER_INTENT_CLASSIFIED,
                      MANAGER_CAPABILITY_SELECTED,
                      MANAGER_CHAIN_STEP_STARTED, CAPABILITY_CHAIN_STEP_STARTED
Decision:             DECISION_PLANNED
Engine lifecycle:     ENGINE_SELECTED, ENGINE_STARTED, ENGINE_COMPLETED, ENGINE_FAILED
Provider selection:   PROVIDER_SELECTED, SERVICE_SELECTED, MODEL_SELECTED
Execution:            REQUEST_SENT, EXECUTION_STARTED, EXECUTION_PROGRESS, EXECUTION_FINISHED
Streaming:            FIRST_TOKEN, CHUNK_RECEIVED, STREAM_FINISHED
Service:              SERVICE_STARTED_LEGACY, SERVICE_COMPLETED, SERVICE_FAILED
Tool:                 TOOL_STARTED, TOOL_COMPLETED, TOOL_FAILED
Adapter:              ADAPTER_RECEIVED, ADAPTER_SENT
Interaction:          USER_MESSAGE, AI_START, AI_CHUNK, AI_END, ERROR
```

**24 event types** span the full execution chain:

```
Input (USER_MESSAGE / RuntimeRequest)
  → Decision (DECISION_PLANNED / MANAGER_*)
  → Capability (CAPABILITY_RESOLVED / MANAGER_CAPABILITY_SELECTED)
  → Provider (PROVIDER_SELECTED / SERVICE_SELECTED / MODEL_SELECTED)
  → Engine (ENGINE_SELECTED / ENGINE_STARTED)
  → Execution (REQUEST_SENT / EXECUTION_STARTED / EXECUTION_PROGRESS / FIRST_TOKEN / CHUNK_RECEIVED)
  → Completion (EXECUTION_FINISHED / STREAM_FINISHED / ENGINE_COMPLETED)
  → Task Close (TASK_COMPLETED / TASK_FAILED)
  → Error (ERROR)
```

**Result**: PASS — no observed unexplained gap in event coverage.

### Q2: Event Ordering Determinism

**Question**: Are events emitted in deterministic order?

**Evidence observed**:

`v6/runtime/event_bus.py:208-210`:
```python
# Trace Hook 同步写入，保证事件顺序与发布顺序一致，避免异步队列导致的乱序/丢失。
self._write_trace_hook(event)
loop.call_soon_threadsafe(queue.put_nowait, event)
```

`_write_trace_hook` runs **synchronously** in the publish thread, **before** the event enters the async queue. This guarantees:

1. Trace Hook sees events in publication order.
2. Async dispatchers also see events in publication order (queue is FIFO).
3. `task_id` routing preserves per-task ordering.

`_dispatch_loop` (`event_bus.py:261-267`):
```python
while self._running:
    event = await self._queue.get()
    if event is None:
        break
    await self._dispatch(event)
```

Single-consumer loop → no parallel dispatcher → no per-task reordering.

**Result**: PASS — deterministic ordering observed (synchronous Trace Hook + single-consumer async loop).

### Q3: Hidden State Mutation

**Question**: Does Runtime contain state mutations that are not reflected in events?

**Evidence observed** (orchestrator.py:78-96, 137-162, 412-422):

```python
def submit(self, task: Task) -> str:
    with self._lock:
        self._task_states[task_id] = RuntimeState.CREATED   # mutation
        ctx = self._ensure_context(task)
        self._contexts[task_id] = ctx                      # mutation
    if self._event_bus is not None and ctx.trace is not None:
        self._event_bus.add_trace_hook(task_id, ctx.trace) # Trace Hook registered
    self._publish(
        RuntimeEventType.TASK_STARTED,                    # event emitted
        ...)

def _complete_task(self, task_id: str, payload: Dict[str, Any]) -> None:
    transitioned = self.transition(task_id, RuntimeState.COMPLETED)
    if transitioned:
        self._publish(RuntimeEventType.TASK_COMPLETED, payload, ...)
    if self._event_bus is not None:
        self._event_bus.remove_trace_hook(task_id)        # Trace Hook removed
```

State mutations are coupled with events:
- `_task_states` mutation ↔ `TASK_STARTED` / `TASK_COMPLETED` / `TASK_FAILED` events.
- `_contexts` mutation ↔ task lifecycle events.
- `add_trace_hook` ↔ `remove_trace_hook` lifecycle.
- `RuntimeContext.trace = RuntimeTrace()` ↔ trace context initialization.

State changes outside this coupling (observed):
- `_decision_manager` state: pure function `decide(user_request) → Decision`, no in-place mutation.
- `_capability_router` state: registry lookup, no in-place mutation.

**No observed hidden mutation**. Every state change has a corresponding event or trace step.

**Result**: PASS — state mutations are event-reflected.

### Q4: Trace Ownership

**Question**: Does Runtime own execution facts (evidence), or does it own ecosystem history (authority)?

**Evidence observed**:

`RuntimeTrace` (`v6/runtime/trace.py`):
- Lives inside `RuntimeContext.trace` (`v6/runtime/context.py:140`).
- Lifecycle scoped to a single `task_id`.
- Snapshot via `RuntimeContext.snapshot()` returns the trace as part of the context.
- No global / cross-task history aggregation in Runtime.
- No persistence layer owned by Runtime.

`Orchestrator`:
- Registers / removes Trace Hooks per task.
- No global trace storage.

`EventBus`:
- Routes events to Trace Hooks (subscribers).
- Does NOT store events.
- Does NOT aggregate history.

**Result**: PASS — Runtime owns execution facts (per-task evidence). It does NOT own ecosystem history (cross-task aggregation, persistence, governance). Evidence ≠ Authority.

### Q5: Trace Semantic Stability (Observation Required)

**Question**: Can future Replay Consumers rely on Runtime trace semantics (event type, parent hierarchy, phase, payload)?

This question is NOT a simple PASS/FAIL. It requires **semantic stability observation across Runtime versions**.

#### What was observed (semantic primitives)

`RuntimeEvent` dataclass (`v6/runtime/event_bus.py:111-130`):
```
- type:        event type string (24 RuntimeEventType enum values)
- payload:     dict (free-form, no schema)
- task_id:     routing key
- source:      "engine:llm" / "service:chat" / etc.
- trace_id:    string, default "" (often empty in current code paths)
- phase:       string, default ""
- timestamp:   float (epoch)
```

`RuntimeTrace.add()` API (`v6/runtime/trace.py:73-127`):
```
- node:        string or Enum (runtime / engine / service / tool / adapter)
- action:      string or TraceEvent Enum (mapped from RuntimeEventType)
- phase:       string or Enum (inference / memory / tool / policy)
- payload:     dict (free-form)
- duration_ms, tokens, cost, tool_time_ms, metrics
- parent_id:   string, default "" — supports Tree structure
- status:      pending / running / success / failed
```

#### Observation gaps (recorded, not closed)

**Gap 1 — trace_id consistency**:
- `RuntimeEvent.trace_id` exists but most `_publish` callers in `agent_runtime.py:188`, `agent_runtime/runtime.py:165/171` do not pass it.
- `_write_trace_hook` (event_bus.py:269-298) reads `trace_id` from event but never writes it into TraceStep.
- Consequence: `RuntimeTrace` does NOT carry `trace_id`. Per-task trace has no `trace_id` column.
- Future Replay Consumer cannot group events by `trace_id` from RuntimeTrace alone.

**Gap 2 — parent_id auto-inference coverage**:
- `_write_trace_hook` auto-infers `parent_id` via `_trace_contexts[task_id]` (`event_bus.py:281-282`).
- The `_RUNTIME_EVENT_TO_TRACE` map covers 17 of 24 RuntimeEventType (event_bus.py:88-107).
- Events not in the map (e.g., `USER_MESSAGE`, `AI_START`, `ADAPTER_RECEIVED`, `SERVICE_FAILED`, etc.) are NOT auto-inferred.
- `parent_id` for these events defaults to "" (flat).
- Consequence: partial tree, not full hierarchy.

**Gap 3 — phase field semantics**:
- `RuntimeEvent.phase` is filled by Engine (`workbench_llm_engine.py:47` etc.) using `ctx.phase`.
- `RuntimeTrace.add()` accepts `phase` directly with no validation.
- Observed phases: "inference", "tool", "policy", "memory", "plan", etc.
- There is NO central registry of valid phase values.
- Consequence: phase is a free-form string. Different callers may use different names for the same concept.

**Gap 4 — payload schema drift**:
- `payload` is `dict` with no schema. Each RuntimeEventType carries a different shape.
- No validation that payload keys are stable across versions.
- Replay Consumers must tolerate schema drift.

#### Observation: NOT CLOSED

This question cannot be answered PASS without:
1. Schema for RuntimeEvent per type.
2. Central phase registry.
3. Full `_RUNTIME_EVENT_TO_TRACE` mapping.
4. Trace_id population in all publish paths.

These are **NOT added by Phase 2-D.4**. They are deferred to consumer-facing ADRs (e.g., OD-R0-005+).

**Result**: OBSERVATION REQUIRED — semantic primitives exist, but cross-version stability is not yet proven.

---

## Evidence ≠ Authority (Boundary Reinforcement)

Per Architecture Review, this observation reaffirms a critical boundary:

```
Runtime produces evidence (RuntimeTrace / RuntimeEvent stream).
Runtime does NOT produce policy, persistence, or history aggregation.

Future Consumers (Debugger / Audit / Governance):
  - Consume RuntimeTrace snapshot from RuntimeContext
  - Build their own: Index / Storage / Policy
  - Live OUTSIDE Runtime boundary

This is why Phase 2-E Consumer Boundary Validation must:
  - Confirm Runtime remains evidence producer only.
  - Verify external consumers can build aggregation / persistence / policy independently.
  - NOT add Trace Schema / Audit Protocol / Debugger Protocol to Runtime.
```

---

## Observation Summary

| Question | Status | Evidence |
|----------|--------|----------|
| Q1 Event completeness | PASS | 24 RuntimeEventType covering full Input → Output chain |
| Q2 Event ordering | PASS | Synchronous Trace Hook + single-consumer async loop |
| Q3 Hidden state mutation | NOT OBSERVED | State mutations coupled with events; no hidden transitions |
| Q4 Trace ownership | PASS | Runtime owns per-task evidence; not ecosystem history |
| Q5 Trace semantic stability | OBSERVATION REQUIRED | 4 gaps recorded: trace_id empty, parent_id partial, phase free-form, payload schema drift |

---

## Implication

The Runtime already produces observable evidence sufficient for replay/trace/audit/governance consumption. No new Contract / Schema / Protocol is required at this time.

**Future consumers** (Debugger / Audit / Agent Governance / Enterprise Control Plane) can:
- Subscribe to `EventBus` for live observation.
- Snapshot `RuntimeContext.trace` for per-task replay.
- Aggregate across tasks **outside** Runtime (in consumer layer).

**What Runtime MUST NOT add**:
- Cross-task history aggregation (becomes ecosystem authority, not execution facts).
- Persistent storage (becomes ecosystem persistence, not Runtime fact).
- Governance policy (becomes ecosystem policy, not Runtime policy).

---

## Phase 2-D.4 Next Steps

This observation log is **preparation only**. Phase 2-D.4 is **CLOSED** with five observations (Q1-Q4 PASS, Q5 OBSERVATION REQUIRED).

**Phase 2-D.4 deliverables**:
- Q1-Q4 confirm Runtime is structurally ready for replay consumers.
- Q5 records 4 gaps that need consumer-side decisions before any consumer-side contract can be frozen.

**Next milestone: Phase 2-E Consumer Boundary Validation** (NOT Phase 2-D.5).

Phase 2-E must:
- Confirm external consumers (Debugger / Audit / Inspector) can be built WITHOUT modifying Runtime.
- Verify Trace Semantic Gaps (Q5) are consumer-tolerable.
- Avoid introducing Trace Schema / Audit Protocol / Debugger Protocol into Runtime.

**No new Runtime Contract / Schema / Protocol is added during Phase 2-D.4 or Phase 2-E.**

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Runtime Replay Validation Preparation Observation Log. |
| v1.1 | 2026-07-23 | Phase 2-D.4 review feedback: added Q5 Trace Semantic Stability (4 gaps recorded, observation required) + Evidence ≠ Authority boundary reinforcement. No Schema / Protocol changes. |