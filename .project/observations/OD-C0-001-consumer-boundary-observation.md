# OD-C0-001 — Consumer Boundary Observation

> **Type**: Observation Log (NOT RFC / NOT ADR)
> **Date**: 2026-07-23
> **Scope**: Runtime Event Consumer boundary observation only
> **Status**: OBSERVING (Phase 2-E.1)

---

## Title

Consumer Boundary Validation Preparation

## Purpose

Verify whether external Consumers (Debugger / Audit / Governance) can be built **without modifying Runtime** — confirming Runtime as **Evidence Producer**, not **Authority Builder**.

This observation does NOT create Consumers. It only records what currently exists and what the boundary state is.

## Scope (In)

- Inspect existing Event consumers in Runtime / Application / Presentation.
- Inspect Event stream accessibility.
- Inspect Trace / State reconstruction feasibility from consumer side.
- Identify consumer-side gaps that would force Runtime modification.

## Non-Goals (Out)

- **Create new Consumer modules** — design
- **Add Trace Schema / Audit Protocol / Debugger Protocol** — design
- **Move ReplayService out of `v6/runtime/`** — only observe the fact that it is currently inside
- **Create `consumer/` directory** — observation only
- **Add Foundation Contract** — deferred to Phase 2-E.2+ (after observation)

---

## Architecture Position

```
                          Runtime Kernel
                          (Evidence Producer)
                                |
                                |
                       RuntimeEvent Stream
                                |
                  ------------------------------
                  |              |              |
                  v              v              v

            Renderer         ReplayService      (Future)
            Consumer         (Runtime internal)   Debugger
            (UI layer)                          | Audit
            UI layer:                          | Governance
              WorkbenchInteractionLayer
              (in agent_workbench/runtime/interaction/layer.py)
```

**Evidence ≠ Authority boundary**:

- Runtime produces evidence (RuntimeEvent / RuntimeTrace / ReplayRecord).
- Runtime does NOT produce policy, persistence, or history aggregation.
- Consumers consume evidence OUTSIDE Runtime.

---

## Four Observation Questions

### Q1: Existing Event Consumers in Runtime / Application / Presentation

**Question**: Who currently consumes Runtime events? What role does each play?

**Evidence observed**:

| Consumer | Location | Subscribes To | Role |
|----------|----------|---------------|------|
| **Orchestrator** | `v6/runtime/orchestrator.py:73-75` | `TASK_STARTED`, `ENGINE_COMPLETED`, `ENGINE_FAILED` | Internal state machine driver (Runtime-internal, NOT Consumer) |
| **RuntimeTrace Hook** | `v6/runtime/event_bus.py:_write_trace_hook` | 17 of 24 RuntimeEventType (via `_RUNTIME_EVENT_TO_TRACE`) | Per-task evidence collector (Runtime-internal) |
| **ReplayService** | `v6/runtime/replay.py:178` | ALL 24 RuntimeEventType (via `_subscribe`) | Replay record collector (Runtime-internal) |
| **WorkbenchInteractionLayer** | `agent_workbench/runtime/interaction/layer.py:196-207` | Runtime EventBus (subscribes to all) | Renderer Consumer (UI layer, Runtime boundary adapter) |

**Classification**:

| Class | Consumers |
|-------|-----------|
| Runtime-internal evidence collector | Orchestrator, RuntimeTrace Hook |
| Passive Consumer (location-bound) | ReplayService (subscribes to all events, but lives in `v6/runtime/`) |
| External Consumer (boundary adapter) | WorkbenchInteractionLayer (RuntimeEvent → InteractionEvent) |
| External Renderer Consumer | Renderer (consumes InteractionEvent only) |

**Multi-layer Consumer Classification** (refined per Architecture Review):

```
Runtime Event Consumer
├── Adapter Consumer           # RuntimeEvent → InteractionEvent
│    InteractionLayer          # ✅ Active
├── Observation Consumer       # RuntimeEvent → Timeline / Debug view
│    ReplayService             # ⚠️ Existing, location-bound (v6/runtime/)
│    Debugger                  # ⏳ Future
├── Storage Consumer           # RuntimeEvent → Immutable log
│    Audit                     # ⏳ Future
└── Policy Consumer            # RuntimeEvent → Policy observation
     Governance               # ⏳ Future
```

**Important refinement**: `ReplayService` IS a Passive Consumer by **behavior**, even though it lives in `v6/runtime/`. Architecture is defined by behavior, not file location. The fact that it is currently inside `v6/runtime/` is **a future extraction candidate**, not a reason to deny its Consumer nature.

**Observation**: 1 active external Adapter Consumer (InteractionLayer). 1 existing Passive Observation Consumer (ReplayService). 4 future Consumers untested (Debugger / Audit / Governance).

**Result**: PASS (boundary identifiable, behavior-over-location principle applied).

### Q2: Event Stream Accessibility

**Question**: Can external Consumers access the Runtime Event Stream without modifying Runtime?

**Evidence observed**:

`EventBus` public API (`v6/runtime/event_bus.py:153-180`):
```python
def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
    """订阅指定类型事件。"""

def unsubscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> bool:
    """取消订阅。"""

def add_trace_hook(self, task_id: str, trace: "RuntimeTrace") -> None:
    """为指定 task_id 注册 Trace Hook。"""
```

`WorkbenchInteractionLayer` is **the only existing external Consumer**. It accesses EventBus via:
```python
# agent_workbench/runtime/interaction/layer.py:196-207
event_bus = self._runtime.core_runtime.event_bus
```

**Two access patterns observed**:

1. **Subscribe pattern** — `event_bus.subscribe(event_type, callback)` — used by Renderer Consumer, ReplayService, Orchestrator.
2. **Trace Hook pattern** — `event_bus.add_trace_hook(task_id, trace)` — used by RuntimeTrace.

**Accessibility**:

- EventBus `subscribe` is **public** (no underscore prefix).
- `core_runtime.event_bus` is reachable via Runtime instance.
- New external Consumer can be added with NO Runtime modification.

**Result**: PASS — Event Stream is accessible to external Consumers.

### Q3: Trace Reconstruction Possibility (Consumer-side)

**Question**: Can a Debugger Consumer reconstruct execution timeline from Runtime evidence alone?

**Evidence observed**:

Per-task evidence available:
- `RuntimeTrace.steps()` (`v6/runtime/trace.py:203`) — list of TraceStep with `timestamp`, `phase`, `node`, `action`, `payload`, `parent_id`, `status`.
- `RuntimeTrace.snapshot()` (`v6/runtime/trace.py:208`) — full JSON-like dict.
- `RuntimeContext.trace` (`v6/runtime/context.py:140`) — per-task trace instance.

Timeline reconstruction:
- `ReplayService.timeline(task_id)` (`v6/runtime/replay.py:130`) — sorted by timestamp.

Gap impact (from OD-R0-004 Q5):
- `trace_id` not populated in TraceStep → cannot group across tasks.
- `parent_id` partial (17/24 events auto-inferred) → partial tree.
- `phase` free-form string → semantic ambiguity.

**Consumer-side compensation** (theoretical, not implemented):
- Debugger Consumer can **synthesize its own trace_id** per task_id (one-to-one mapping).
- Debugger Consumer can **infer parent_id from timestamp + type precedence** (e.g., TASK_STARTED > CAPABILITY_RESOLVED > ENGINE_* > EXECUTION_*).
- Debugger Consumer can **normalize phase** to a canonical set (consumer-side mapping table).

**Result**: PASS with Caveats — Timeline reconstruction is feasible WITHOUT Runtime modification. Consumer must absorb the gaps from OD-R0-004 Q5.

### Q4: State Reconstruction Possibility (Consumer-side)

**Question**: Can an Audit Consumer reconstruct execution state without Runtime-side persistence?

**Evidence observed**:

Per-task state available:
- `RuntimeContext.snapshot()` (`v6/runtime/context.py:255`) — returns dict including `messages`, `result`, `trace`, etc.

Cross-task aggregation:
- **NOT provided by Runtime**. No global registry, no session history (only per-task RuntimeTrace).

**Consumer-side compensation** (theoretical):
- Audit Consumer subscribes to ALL RuntimeEventTypes.
- Consumer stores events into its own storage (NOT Runtime storage).
- Consumer builds cross-task views from its own store.
- Audit log is Consumer's persistence, NOT Runtime's.

**Result**: PASS — State reconstruction is feasible WITHOUT Runtime modification, as long as the Consumer maintains its own persistence layer.

---

## Consumer Topology (Future Position)

Per Architecture Review, the Consumer layer should live OUTSIDE Runtime. Future file layout:

```
agent_workbench/
    consumer/                    # NOT created yet (observation only)
        debugger/
            timeline_view.py     # Consumer-side Debugger
        audit/
            execution_log.py     # Consumer-side Audit
        governance/
            policy_observer.py   # Consumer-side Governance
```

**Current reality**:

```
v6/runtime/replay.py               # ReplayService lives INSIDE Runtime (Foundation concept)
                                    # In Phase 2-E+, this may be relocated OUTSIDE Runtime
                                    # No relocation is done in Phase 2-E.1 (observation only)
```

**Observation note**: `ReplayService` is a Foundation-style concept (Replay Record + Log + Service). It lives in `v6/runtime/` but does NOT modify Runtime Kernel — it is a passive subscriber. The "consumer/ vs runtime/" relocation is a future concern, not a current obligation.

---

## Evidence ≠ Authority Boundary Reinforcement

Per Architecture Review:

```
Runtime          = Evidence Producer
  Produces:        RuntimeEvent, RuntimeTrace, ReplayRecord
  DOES NOT own:    Cross-task aggregation, persistence, governance, policy

External Consumer = Authority Builder
  Builds:           Debugger Index, Audit Log, Policy Engine
  Lives:            OUTSIDE Runtime (in consumer/ namespace, future)
```

**Implication**: Phase 2-E.2+ may introduce a `consumer/` namespace. Phase 2-E.1 only **observes** the boundary; it does NOT create the namespace.

---

## Observation Summary

| Question | Status | Evidence |
|----------|--------|----------|
| Q1 Existing Event Consumers | PASS (LOW diversity) | 1 external Consumer (Renderer); Runtime-internal collectors exist |
| Q2 Event Stream Accessibility | PASS | `subscribe()` is public; EventBus reachable via Runtime |
| Q3 Trace Reconstruction | PASS with Caveats | Feasible consumer-side; gaps from OD-R0-004 Q5 absorbed by Consumer |
| Q4 State Reconstruction | PASS | Per-task snapshot available; cross-task aggregation done consumer-side |

---

## Boundary Health

| Boundary | Health | Reason |
|----------|--------|--------|
| Runtime ↔ Adapter Consumer | ✅ Stable | WorkbenchInteractionLayer is established, well-bounded |
| Runtime ↔ Observation Consumer (Replay) | ⚠️ Stable but location-bound | ReplayService behavior is Consumer-like, but file location is `v6/runtime/` |
| Runtime ↔ Observation Consumer (Debugger) | ⏳ Untested | No debugger consumer exists yet |
| Runtime ↔ Storage Consumer (Audit) | ⏳ Untested | No audit consumer exists yet |
| Runtime ↔ Policy Consumer (Governance) | ⏳ Untested | No governance consumer exists yet |

**Refined metric**: **Validated Consumer Pattern** count = 1 (Adapter pattern, proven via InteractionLayer).

**Implication for Phase 2-E.2+**: The next validation target is **Observation Consumer (Debugger)** — observe whether ReplayService's existing capabilities can be extended WITHOUT Runtime modification.

---

## What Phase 2-E.1 Does NOT Do

- Does NOT create `consumer/` directory.
- Does NOT implement Debugger / Audit / Governance modules.
- Does NOT add Trace Schema, Audit Protocol, or Debugger Protocol.
- Does NOT modify Runtime / EventBus / RuntimeTrace.
- Does NOT add Foundation Contract symbols.

Phase 2-E.1 is **observation only**. Implementation is deferred to Phase 2-E.2+ with a separate ADR.

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Consumer Boundary Observation. Four-question observation; one external Consumer (Renderer) identified; three untested Consumer types (Debugger / Audit / Governance) recorded. |
| v1.1 | 2026-07-23 | Architecture Review refinement: applied **behavior > file location** principle. ReplayService reclassified as Passive Observation Consumer (location-bound). Introduced multi-layer Consumer classification (Adapter / Observation / Storage / Policy). Validated Consumer Pattern count = 1 (Adapter pattern). Next validation target: Observation Consumer (Debugger). |