"""tools/decision_support/adapter/ — Phase 3.15 Step 2: Decision Adapter.

Pure function: InsightArtifact -> DecisionArtifact.

Rules (user spec):
- pure function
- stateless
- deterministic
- no storage
- no EventBus
- rule-based strategy (NOT AI autonomous)
- no execution
- no scheduling
- no capability routing
"""
from tools.decision_support.adapter.insight_decision_adapter import InsightDecisionAdapter

__all__ = ["InsightDecisionAdapter"]