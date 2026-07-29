"""tools/insight/contract/ — Phase 3.14 Insight Contract Schema (Frozen).

Insight = "What does it mean" (NOT "what happened", NOT "what to do").

Phase 3.14 边界:
- structured understanding layer (NOT AI Summary)
- 纯数据契约 (NOT LLM narrative)
- 平台无关 (NOT UI Model)

Strict NOT in scope:
- ❌ Memory / Persistence
- ❌ Decision / Recommendation / Action
- ❌ Planning
- ❌ AI generated narrative / LLM summary
"""
from tools.insight.contract.insight_artifact import (
    INSIGHT_ARTIFACT_SCHEMA_VERSION,
    InsightArtifact,
    InsightClassification,
    InsightPattern,
)

__all__ = [
    "INSIGHT_ARTIFACT_SCHEMA_VERSION",
    "InsightArtifact",
    "InsightClassification",
    "InsightPattern",
]