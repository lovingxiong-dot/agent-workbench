"""tools/insight/consumer/ — Phase 3.14 Step 3: Insight Consumer.

Read-only consumption example.

Allowed:
- InsightArtifact -> consumer output (to_dict / JSON)

Forbidden:
- Consumer -> Decision (Phase 3.15 separate)
- Consumer -> Memory (Phase 3.16 separate)
- Consumer -> Runtime
- Consumer -> Observation Store
- Consumer -> EventBus
- LLM / AI Summary generation
"""
from tools.insight.consumer.insight_consumer import InsightConsumer

__all__ = ["InsightConsumer"]