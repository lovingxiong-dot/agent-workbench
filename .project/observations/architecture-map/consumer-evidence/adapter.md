# Adapter Consumer (InteractionLayer)

> **Type**: Validated Consumer Capability
> **Location**: `agent_workbench/runtime/interaction/layer.py`

---

## Role

```
RuntimeEvent (24 RuntimeEventType)
    ↓
WorkbenchInteractionLayer._on_event
    ↓
RuntimeEventMapper.map  ← single translation point
    ↓
InteractionEvent
    ↓
PresentationRuntime.dispatch_event
    ↓
active Renderer.render(InteractionEvent)
```

## Source Evidence

- [OD-C0-001 §Q1](../../OD-C0-001-consumer-boundary-observation.md) — Found Consumer #1
- [ADR-008.4.1-4 Stage Trace](../../decisions/ADR-008-runtime-closure-validation.md#45-phase-2d3--data-flow-validation-adr-008-2x) — 9-stage trace

## Subscribes To

```python
# agent_workbench/runtime/interaction/layer.py:211
event_bus.subscribe("*", self._callback)
```

(`*` = all event types via RuntimeEventBus)

## Boundary

| Aspect | Status |
|--------|--------|
| Boundary Adapter | ✅ YES (not Service Locator) |
| Single Entry Point | ✅ YES |
| Mutates Runtime? | ❌ NO (sink only) |
| Imports Runtime EventBus | ✅ YES (allowed for boundary adapter) |

## Allowed Methods

```
interaction_layer.submit_request(RuntimeRequest)
interaction_layer.list_conversation_groups()
interaction_layer.create_conversation()
interaction_layer.delete_conversation()
interaction_layer.get_session_metadata()
```

## Forbidden Methods (Constraint 1)

```
interaction_layer.runtime.xxx            # escape hatch
interaction_layer.session_module.xxx    # directly exposing Runtime internals
interaction_layer.decision_manager      # leaking Runtime control plane
interaction_layer.orchestrator          # leaking Runtime control plane
```

## Position

This is the **only active external Consumer** in the current Workbench v6 codebase. It serves the **UI Renderer** use case exclusively.

Future Consumers (Debugger / Audit / Governance) should follow this pattern, NOT replace it.