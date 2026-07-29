"""tools/insight/adapter/ — Phase 3.14 Step 2: Insight Adapter.

Pure function: ObservationArtifact -> InsightArtifact.

Rules (user spec):
- pure function
- stateless
- deterministic
- no storage
- no EventBus
- rule-based pattern (NOT AI)
"""
from tools.insight.adapter.observation_insight_adapter import ObservationInsightAdapter

__all__ = ["ObservationInsightAdapter"]