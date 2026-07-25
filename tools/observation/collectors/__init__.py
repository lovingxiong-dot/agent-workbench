"""tools/observation/collectors/ — Evidence Collection Orchestration。

EvidenceCollector 拼接 adapters → derived metrics → ObservationReport。
无 Runtime 引用，无 Worker 启动，无状态修改。
"""
from tools.observation.collectors.evidence_collector import EvidenceCollector

__all__ = ["EvidenceCollector"]
