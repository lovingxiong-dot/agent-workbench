"""tools/decision_support/contract/ — Phase 3.15 Decision Support Contract (Frozen).

Decision Support = "What should we consider" (NOT "what to do now").

Phase 3.15 边界:
- decision options layer (NOT action executor)
- 纯数据契约 (NOT planner / workflow engine)
- 平台无关 (NOT UI / Renderer)

Strict NOT in scope:
- execute / schedule / capability routing
- task mutation / memory write
- LLM autonomous decision
- ActionExecutor / AgentPlanner / WorkflowEngine
"""
from tools.decision_support.contract.decision_artifact import (
    DECISION_ARTIFACT_SCHEMA_VERSION,
    DecisionArtifact,
    DecisionOption,
    DecisionStrategy,
)

__all__ = [
    "DECISION_ARTIFACT_SCHEMA_VERSION",
    "DecisionArtifact",
    "DecisionOption",
    "DecisionStrategy",
]