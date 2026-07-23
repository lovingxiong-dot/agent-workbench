# Runtime Event Evidence

> **Layer**: 0 — Foundation Runtime
> **Source**: RuntimeEvent stream (Runtime = Evidence Producer)

---

## Source Evidence

- [OD-R0-004 Runtime Replay Validation Preparation](../../OD-R0-004-runtime-replay-preparation.md)
- [ADR-008 Runtime Closure Validation](../../decisions/ADR-008-runtime-closure-validation.md) §4.5

## RuntimeEventType Coverage (24 types)

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

## 9-Stage Data Flow Trace (ADR-008 §4.5)

| Stage | Owner | Event | State |
|-------|-------|-------|-------|
| 1 Input → RuntimeRequest | Caller | None | None |
| 2 → InteractionLayer | InteractionLayer | user_message | `_task_to_request` |
| 3 → DecisionManager | DecisionManager | user_message | None |
| 4 Decision → Task | DecisionManager | None | Task object |
| 5 Task → Orchestrator | Orchestrator | TASK_STARTED | Orchestrator State |
| 6 → Capability | CapabilityRouter | None | Registry |
| 7 Capability → Engine | EngineManager | ENGINE_SELECTED | Engine Manager |
| 8 → InteractionEvent | Mapper | MESSAGE_*, TOOL_* | None (stateless) |
| 9 → Renderer | Renderer | Renderer.render | Widget state |

## Critical Properties

| Property | Status | Evidence |
|----------|--------|----------|
| Event Completeness | ✅ PASS | 24 RuntimeEventType cover full chain |
| Event Ordering Determinism | ✅ PASS | Synchronous Trace Hook + single-consumer async loop |
| Hidden State Mutation | ✅ NOT OBSERVED | State mutations coupled with events |
| Trace Ownership | ✅ PASS | Runtime owns per-task evidence, not ecosystem history |
| Trace Semantic Stability | ⚠️ OBSERVATION REQUIRED | 4 gaps (trace_id/parent_id/phase/payload) — consumer-side resolvable |

## Principle

**Evidence ≠ Authority**: Runtime produces evidence. Runtime does NOT own policy, persistence, or history aggregation. Consumers (Debugger / Audit / Governance) build their own authority OUTSIDE Runtime.

## Position

RuntimeEvent stream is the **single public surface** for Runtime → external consumer interaction. It is NOT implementation detail — it is the **product-agnostic data contract**.