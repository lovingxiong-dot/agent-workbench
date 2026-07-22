# OD-C0-003 — Consumer Diversity Observation

> **Type**: Repository Scan Observation (NOT Feature Development)
> **Date**: 2026-07-23
> **Scope**: Scan existing consumers in repository; classify by Consumer Taxonomy v0.x
> **Status**: OBSERVATION COMPLETE

---

## Title

Consumer Diversity Observation (Phase 2-E.3)

## Purpose

Verify whether Runtime has naturally produced **more consumer patterns** beyond Adapter (InteractionLayer) and Observation (ReplayService). The previous probes (OD-C0-001, OD-C0-002) only established two patterns. Phase 2-E.3 scans the repository for additional consumer evidence.

This is **NOT**:
- Creating new consumers.
- Extracting abstractions.
- Modifying Runtime.

This IS:
- Reading existing source files.
- Classifying found consumers by behavior.
- Recording what exists vs what is missing.

## Scope (In)

- All files under `agent_workbench/` that consume `RuntimeEvent`, `RuntimeTrace`, or `EventBus`.
- Files that subscribe to or replay Runtime events.
- Legacy / deprecated paths if still observable (for historical context only).

## Scope (Out)

- `v6/runtime/*` files that ONLY emit events (they are producers, not consumers).
- `v6/engines/*` that subscribe only to internal lifecycle events.
- Future consumer products.

---

## Scan Method

1. `grep -r "event_bus\.subscribe" agent_workbench/` — find active subscribers.
2. `grep -r "event_bus\.add_trace_hook" agent_workbench/` — find trace hook users.
3. `grep -r "RuntimeContext\.snapshot\|trace\.steps()\|trace\.snapshot" agent_workbench/` — find trace consumers.
4. Glob for `**/audit*.py`, `**/governance*.py`, `**/policy*.py`, `**/monitor*.py`, `**/telemetry*.py` — find storage/policy/monitor modules.

---

## Consumer Inventory (Found Evidence)

### Confirmed Consumers

| # | Consumer | Location | Behavior | Consumer Type |
|---|----------|----------|----------|---------------|
| 1 | `WorkbenchInteractionLayer` | `agent_workbench/runtime/interaction/layer.py:196,211` | Subscribes via `event_bus.subscribe("*", self._callback)`; maps RuntimeEvent → InteractionEvent; pushes to Renderer | **Adapter Consumer** ✅ |
| 2 | `ReplayService` | `v6/runtime/replay.py:178` | Subscribes to ALL 24 RuntimeEventType via `_subscribe()`; converts to ReplayRecord; in-memory log only | **Observation Consumer** (capability, location-bound) ⚠️ |
| 3 | `WorkbenchUIController._on_trace_event` | `agent_workbench/ui/workbench_ui_controller.py:464` | Subscribes to 13 RuntimeEventType (TASK_STARTED, CAPABILITY_RESOLVED, ENGINE_SELECTED, EXECUTION_STARTED, PROVIDER_SELECTED, REQUEST_SENT, FIRST_TOKEN, CHUNK_RECEIVED, STREAM_FINISHED, EXECUTION_FINISHED, ENGINE_COMPLETED, TASK_COMPLETED, TASK_FAILED); appends to `TraceWorkspaceItem` UI panel | **Observation Consumer (Trace View)** ⚠️ (legacy UI embedded) |

### Producer / Internal (NOT Consumer)

| Module | Location | Why Not Consumer |
|--------|----------|------------------|
| `Orchestrator` | `v6/runtime/orchestrator.py:73-75,412-422` | Internal state machine driver (subscribes to drive its own state, NOT external observation) |
| `RuntimeTrace` | `v6/runtime/event_bus.py:_write_trace_hook` | Per-task evidence collector, internal to RuntimeContext |
| `RuntimeMetrics` | `v6/runtime/metrics.py:20` | Statistics container embedded in RuntimeContext, NOT a subscriber |
| `Policy` | `agent_workbench/runtime/decision/policy.py:22-31` | Policy check stub, default allow, does NOT subscribe to EventBus |
| `DecisionPolicy` | `v6/runtime/decision_policy.py` | Same as above, stub policy |

### Not Found (Search Confirmed Absent)

| Module Pattern | Search Result | Implication |
|----------------|---------------|-------------|
| `**/audit*.py` (agent_workbench) | Not found | No Storage Consumer exists |
| `**/governance*.py` (agent_workbench) | Not found | No Policy Consumer exists |
| `**/monitor*.py` (agent_workbench) | Not found | No Monitoring Consumer exists |
| `**/telemetry*.py` (agent_workbench) | Not found | No Telemetry Storage Consumer exists |
| `**/metric*.py` (agent_workbench) | Not found (only `v6/runtime/metrics.py` exists, NOT a consumer) | No external Metrics Storage exists |

---

## Classification by Consumer Taxonomy v0.x

| Consumer Type | Found | Status |
|---------------|-------|--------|
| **Adapter Consumer** | InteractionLayer (1) | Validated ✅ |
| **Observation Consumer (Replay)** | ReplayService (1) | Capability validated ⚠️ location-bound |
| **Observation Consumer (Trace View)** | WorkbenchUIController._on_trace_event (1) | Found in legacy UI ⚠️ embedded |
| **Storage Consumer** | None | **NOT found** |
| **Policy Consumer** | None | **NOT found** |
| **Coordination Consumer** | None | **NOT found** |
| **Optimization Consumer** | None | **NOT found** |
| **Simulation Consumer** | None | **NOT found** |

**Diversity Score**: 2 out of 8 categories have existing evidence (Adapter, Observation). 6 categories absent.

---

## Per-Consumer Detailed Analysis

### Consumer #3: WorkbenchUIController._on_trace_event (NEW discovery)

**File**: `agent_workbench/ui/workbench_ui_controller.py:846-852`

```python
def _on_trace_event(self, event: RuntimeEvent) -> None:
    """Runtime Trace 事件 → Trace Workspace 追加最新步骤。"""
    if self._trace_workspace is None or not event.task_id:
        return
    timeline = self._workbench.trace_timeline(event.task_id)
    if timeline:
        self._trace_workspace.append_event(timeline[-1])
```

**Subscribes to** (13 event types, workbench_ui_controller.py:450-464):
- TASK_STARTED
- CAPABILITY_RESOLVED
- ENGINE_SELECTED
- EXECUTION_STARTED
- PROVIDER_SELECTED
- REQUEST_SENT
- FIRST_TOKEN
- CHUNK_RECEIVED
- STREAM_FINISHED
- EXECUTION_FINISHED
- ENGINE_COMPLETED
- TASK_COMPLETED
- TASK_FAILED

**Behavior**:
- Subscribes to a **subset** (13 of 24) of RuntimeEventType.
- Calls `self._workbench.trace_timeline(event.task_id)` — reads from `Workbench` host.
- Calls `self._trace_workspace.append_event(timeline[-1])` — writes to `TraceWorkspaceItem` UI panel.

**Observation**: This is **the same Observation Consumer pattern** as ReplayService, but **embedded in the legacy WorkbenchUI**. It is a real-world example of Trace View consumer in production code.

**Implication**: The legacy UI has already proven the Observation (Trace View) consumer pattern works. Phase 2-D Renderer Migration can learn from this, but does NOT need to copy it.

**Location observation**: This consumer is in `agent_workbench/ui/workbench_ui_controller.py`, NOT in `v6/runtime/`. So it is "location-correct" (UI-side). It is deprecated legacy UI.

---

## Storage Consumer — Not Found

**Implication**: Audit Consumer does NOT exist as code yet. If a future Audit Consumer is needed, it must be created (not extracted). Creation must follow OD-G0-001 procedure.

**Recommended Action**: None. Phase 2-E.3 is observation only.

---

## Policy Consumer — Not Found

**Observation**: `Policy` (decision/policy.py) and `DecisionPolicy` (v6/runtime/decision_policy.py) are **policy check stubs**, NOT consumers. They do not subscribe to EventBus.

**Implication**: No Policy Consumer exists. Governance would require either:
1. Activating `Policy.check()` into an event-driven path (Runtime modification).
2. Building an external Governance Consumer that subscribes to RuntimeEvent and applies policy post-hoc (no Runtime modification).

Option 2 is preferred per Evidence ≠ Authority principle.

---

## Coordination / Optimization / Simulation Consumers — Not Found

These categories are speculative. They have NO existing implementation. No recommendation.

---

## Diversity Finding Summary

| Aspect | Status |
|--------|--------|
| Adapter Consumer validated | ✅ Yes (InteractionLayer) |
| Observation Consumer (Replay capability) | ✅ Yes (ReplayService) |
| Observation Consumer (Trace View) | ✅ Yes (WorkbenchUIController, legacy) |
| Storage Consumer | ❌ Not found |
| Policy Consumer | ❌ Not found |
| Coordination / Optimization / Simulation | ❌ Not found (speculative) |

**Conclusion**: Repository has **2 Adapter** + **2 Observation** capabilities, zero Storage / Policy consumers. The Runtime ecosystem is **observation-heavy** but **storage-light** and **policy-light**.

---

## Implication for Foundation / Runtime

- Runtime does not need to evolve to support Storage / Policy. Consumers can build on existing RuntimeEvent stream.
- Foundation Contract v0.5 does not need new symbols for Storage / Policy.
- Architecture Evolution Rule (OD-G0-001) holds: no abstraction created without evidence of repeated need.

---

## What This Probe Does NOT Do

- Does NOT recommend creating `consumer/` directory.
- Does NOT propose Audit / Governance products.
- Does NOT move `replay.py` out of `v6/runtime/`.
- Does NOT classify `WorkbenchUIController._on_trace_event` as the "new Debugger" (it is deprecated).
- Does NOT touch Runtime / EventBus / RuntimeTrace.

---

## Recommended Next Phase

Per Architecture Review, three options were considered:

| Option | Decision |
|--------|----------|
| A. Phase 2-E.4 Real-time Push | **Deferred** — requires push semantics design |
| B. Phase 2-D Closure | **Optional** — boundaries already proven |
| C. Continue Observation | **Selected (Phase 2-E.3 complete)** |

Recommended next after Phase 2-E.3:
- End Phase 2-E series (sufficient observation evidence collected).
- Resume Phase 2-D Workbench v6 closure (Renderer Migration final state).
- Phase 2-E.4+ only when a real Storage / Policy consumer is needed.

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Consumer Diversity Observation. 3 consumers found (1 Adapter + 2 Observation). 6 consumer categories absent (Storage / Policy / Coordination / Optimization / Simulation / Telemetry). Phase 2-E.3 closed. |