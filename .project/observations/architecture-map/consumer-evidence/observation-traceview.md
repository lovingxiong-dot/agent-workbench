# Observation Consumer / TraceView (Legacy)

> **Type**: Existing in legacy UI (location: deprecated)
> **Location**: `agent_workbench/ui/workbench_ui_controller.py:464,846`

---

## Behavior

```
subscribe(13 RuntimeEventType subset)
    ↓
workbench.trace_timeline(event.task_id)
    ↓
TraceWorkspaceItem.append_event(timeline[-1])
```

## Source Evidence

- [OD-C0-003 Consumer Diversity Observation](../../OD-C0-003-consumer-diversity-observation.md) — Found Consumer #3

## Subscribes To (13 of 24)

```
TASK_STARTED, CAPABILITY_RESOLVED, ENGINE_SELECTED,
EXECUTION_STARTED, PROVIDER_SELECTED, REQUEST_SENT,
FIRST_TOKEN, CHUNK_RECEIVED, STREAM_FINISHED,
EXECUTION_FINISHED, ENGINE_COMPLETED,
TASK_COMPLETED, TASK_FAILED
```

## Boundary

| Aspect | Status |
|--------|--------|
| Subscribes EventBus | ✅ YES |
| Mutates Runtime | ❌ NO |
| UI-Embedded | ⚠️ YES (deprecated WorkbenchUI) |

## Position

This is the **third Consumer pattern** discovered. It is **embedded in the legacy WorkbenchUI** (deprecated in v6 migration).

This pattern demonstrates the **Observation / TraceView capability** in production code. Phase 2-D Renderer Migration can learn from this, but does NOT need to copy it.

## Lesson Learned

The legacy UI has already proven the Observation Consumer (Trace View) pattern works in production. When v6.10+ adds new Observation Consumers (e.g., Debugger), they should follow this pattern but with proper location (NOT inside deprecated UI).