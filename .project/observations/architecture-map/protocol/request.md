# RuntimeRequest

> **Layer**: 1.5 — Protocol Contracts
> **Type**: Input boundary protocol

---

## Position

```
Caller (CLI / UI signal)
    ↓
RuntimeRequest (single input shape)
    ↓
WorkbenchInteractionLayer.submit_request
    ↓
DecisionManager → Task → Orchestrator → Engine → Renderer
```

## Validation

[ADR-008.4.1 Input Normalization Boundary](../../decisions/ADR-008-runtime-closure-validation.md#adr-00841--input-normalization-boundary)

- ✅ `WorkbenchInteractionLayer.submit_request(RuntimeRequest)` is the only entry that accepts user text
- ✅ RuntimeRequest is a single Protocol dataclass (text, session_id, correlation_id, metadata)
- ✅ All instantiations route through `interaction_layer.submit_request`
- ✅ No direct `runtime.session.create` / `runtime.session.append_message` calls

## Boundary Principle

```
Allowed:
    interaction_layer.submit_request(RuntimeRequest)

Forbidden:
    application builds ExecutionContext directly  (no context fabrication)
    presentation reads Session internal state     (no state reach-around)
```

## Position in 5-Layer Model

```
User Intent
    ↓
Layer 4 Application (CLI / UI Signal)
    ↓
Layer 1.5 Protocol Contract (RuntimeRequest)        ← THIS
    ↓
Layer 0 Runtime (InteractionLayer → DecisionManager → Task)
```