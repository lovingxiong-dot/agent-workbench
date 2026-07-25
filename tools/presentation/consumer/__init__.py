"""tools/presentation/consumer/ — Phase 3.13 Step 3: Presentation Consumer.

Read-only consumption example.

Allowed:
- ObservationViewModel → presentation output (to_dict / serialized JSON)

Forbidden (user spec):
- Consumer → Runtime
- Consumer → Observation Store
- Consumer → EventBus
"""
from tools.presentation.consumer.observation_consumer import ObservationConsumer

__all__ = ["ObservationConsumer"]
