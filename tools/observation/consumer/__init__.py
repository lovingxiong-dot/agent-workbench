"""tools/observation/consumer/ — Phase 3.12 Batch 2 RuntimeEvent Consumer.

Read-only Adapter (NOT Runtime subscription).

边界 (ADR-016 + 用户 Check 2):
- ✅ consume(RuntimeEvent) → ObservationArtifact (pure function)
- ✅ extract fields from event (type / task_id / source / trace_id / phase / payload / timestamp)
- ❌ runtime.submit() / dispatch() / task.update() (NO Runtime mutation)
- ❌ subscribe EventBus (NOT subscription)
- ❌ hold EventBus reference (NO state)

设计:
- RuntimeEventConsumer 是 **pure function style**
- 调用者负责传入 event (NO EventBus coupling)
- 输出 ObservationArtifact (frozen)
- 内部事件类型映射 (RuntimeEventType → ObservationType)
- 默认 relevance/confidence/stability = 1.0 for direct runtime events
"""
from tools.observation.consumer.runtime_event_consumer import RuntimeEventConsumer

__all__ = ["RuntimeEventConsumer"]
