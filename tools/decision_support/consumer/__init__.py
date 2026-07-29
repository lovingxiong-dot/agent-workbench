"""tools/decision_support/consumer/ — Phase 3.15 Step 3: Decision Consumer.

Read-only consumption example.

Allowed:
- DecisionArtifact -> consumer output (to_dict / JSON)

Forbidden:
- Consumer -> Execution (NOT ActionExecutor)
- Consumer -> Memory (NOT memory write)
- Consumer -> Runtime
- Consumer -> Insight Store
- Consumer -> EventBus
- LLM / AI autonomous decision
"""
from tools.decision_support.consumer.decision_support_consumer import DecisionSupportConsumer

__all__ = ["DecisionSupportConsumer"]