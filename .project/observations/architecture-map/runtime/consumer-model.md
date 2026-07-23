# Consumer Model (v0.x)

> **Layer**: 0 — Foundation Runtime (Consumer perspective)
> **Version**: Taxonomy v0.x (PROPOSAL, NOT FROZEN)
> **Behavior over Location** principle (OD-C0-001 v1.1)

---

## Source Evidence

- [OD-C0-001 Consumer Boundary Observation](../../OD-C0-001-consumer-boundary-observation.md) v1.1
- [OD-C0-002 Observation Consumer Feasibility](../../OD-C0-002-observation-consumer-feasibility.md) v1.1
- [OD-C0-003 Consumer Diversity Observation](../../OD-C0-003-consumer-diversity-observation.md) v1.0

## Consumer Taxonomy v0.x

```
Runtime Event Consumer
├── Adapter Consumer           # RuntimeEvent → InteractionEvent
│    InteractionLayer          # ✅ Active (UI layer)
├── Observation Consumer       # RuntimeEvent → Timeline / Debug view
│    ReplayService             # ⚠️ Existing, location-bound (v6/runtime/)
│    Debugger                  # ⏳ Future
├── Storage Consumer           # RuntimeEvent → Immutable log
│    Audit                     # ⏳ Out of Current Product Boundary
└── Policy Consumer            # RuntimeEvent → Policy observation
     Governance               # ⏳ Out of Current Product Boundary
```

## Validated Consumer Capabilities (3 of 8)

| Consumer | Capability Status | Full Pattern Status |
|----------|-------------------|---------------------|
| Adapter (InteractionLayer) | ✅ Capability validated | ✅ Production |
| Observation / Replay (ReplayService) | ✅ Capability validated | ⚠️ Lifecycle / deployment / permissions / storage not defined |
| Observation / TraceView (legacy WorkbenchUIController) | ⚠️ Embedded in deprecated UI | ⏳ Migration pending |

## 4 Foundational Questions (OD-C0-001)

| Question | Result |
|----------|--------|
| Q1 Existing Event Consumers | PASS (low diversity: 1 active external + 1 passive + 1 deprecated) |
| Q2 Event Stream Accessibility | PASS — `subscribe()` public, EventBus via Runtime reachable |
| Q3 Trace Reconstruction | PASS with caveats — OD-R0-004 Q5 gaps consumer-side resolvable |
| Q4 State Reconstruction | PASS — per-task snapshot, cross-task by consumer |

## 3 Capability Probe Questions (OD-C0-002)

| Question | Result |
|----------|--------|
| Q1 Event Stream sufficiency | PASS — 3 diagnostic questions confirmed |
| Q2 Runtime new field need | PASS — none required |
| Q3 Consumer independent evolution | PASS — for Phase 2-E.2 scope |

## Boundary Health Matrix

| Boundary | Health |
|----------|--------|
| Runtime ↔ Adapter Consumer | ✅ Stable |
| Runtime ↔ Observation (Replay) | ⚠️ Stable but location-bound |
| Runtime ↔ Observation (Debugger) | ⏳ Untested |
| Runtime ↔ Storage (Audit) | ⏳ Out of Current Product Boundary |
| Runtime ↔ Policy (Governance) | ⏳ Out of Current Product Boundary |

## Principles

- **Behavior > File Location**: ReplayService lives in `v6/runtime/` but is Consumer by behavior.
- **Validated Capability ≠ Full Pattern**: Capability (passive subscription) validated; lifecycle / deployment / multi-instance / permissions / storage strategy not yet defined.
- **Consumer Taxonomy v0.x**: PROPOSAL, NOT FROZEN. May add Coordination / Optimization / Simulation / etc.