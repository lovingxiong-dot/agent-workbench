# Observation Consumer / Replay (ReplayService)

> **Type**: Validated Capability (location-bound)
> **Location**: `v6/runtime/replay.py`

---

## Behavior Profile

```
subscribe(RuntimeEventType.ALL)
    ↓
ReplayRecord.from_event(event)
    ↓
ReplayLog.add(record)
    ↓
timeline(task_id) / filter / export
    ↓
NO Engine invocation
NO Session mutation
NO EventBus modification
```

## Source Evidence

- [OD-C0-001 §Q1](../../OD-C0-001-consumer-boundary-observation.md) — Found Consumer #2
- [OD-C0-002 Capability Probe](../../OD-C0-002-observation-consumer-feasibility.md) v1.1 — 3 questions PASS

## Location vs Behavior Tension

- **File Location**: `v6/runtime/replay.py` (Runtime package)
- **Behavior**: Passive Event Consumer (subscribes, converts, no invocation)

**Per OD-G0-001 (Behavior > File Location)**: ReplayService IS a Consumer by behavior, despite file location.

The fact that it lives in `v6/runtime/` is **a future extraction candidate**, not a reason to deny its Consumer nature.

## Public API

```python
# ReplayService
attach(event_bus)                  # bind + subscribe to all 24 RuntimeEventType
log                                # access ReplayLog
import_from_trace(trace, task_id)  # import existing RuntimeTrace steps

# ReplayLog
records()                          # all records (deep copy)
filter(task_id, component, event_type)
timeline(task_id)                  # sorted by timestamp
export()                           # full export
clear()

# ReplayRecord
from_event(event)
to_dict()
```

## Capability Status

| Aspect | Status |
|--------|--------|
| Passive Subscription | ✅ Capability validated |
| Per-task Evidence | ✅ Capability validated |
| Snapshot / Timeline / Filter / Export | ✅ Capability validated |
| Cross-task Aggregation | ✅ Possible (filter) |
| Real-time UI Rendering | ❌ Not built-in |
| Persistent Storage | ❌ Not built-in (in-memory) |

## Full Pattern Status

| Lifecycle Component | Status |
|---------------------|--------|
| Lifecycle | ⚠️ Not defined |
| Deployment | ⚠️ Not defined |
| Multi-instance | ⚠️ Not defined |
| Permissions | ⚠️ Not defined |
| Storage Strategy | ⚠️ Not defined (in-memory only) |

**Verdict**: Capability validated. Full Pattern NOT yet defined.

## Position

This is the **prototype Debugger Consumer** baseline. Future Debugger Consumer should EXTEND this capability, NOT replace it.