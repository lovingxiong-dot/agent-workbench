"""tools/presentation/ — Phase 3.13 Observation Presentation & Consumption Layer。

Phase 3.13 目标：消费 ObservationReport，让系统产生可见能力（Visible Capability）。

边界（ADR-017）：
- 仅消费 tools.observation.ObservationReport（read-only）
- 禁止 import v6.runtime.orchestrator / EngineManager / PlannerLoop / CapabilityRouter
- 禁止 import agent_workbench.runtime.*
- 禁止 import v6.presentation.models（frozen）
- ViewModel 必须 frozen dataclass
- 不修改 ObservationReport；不订阅 EventBus 写事件
"""
from tools.presentation.view_models.observation_view_model import ObservationViewModel
from tools.presentation.view_models.runtime_status_view import RuntimeStatusView
from tools.presentation.view_models.performance_view import PerformanceView
from tools.presentation.view_models.resource_view import ResourceView
from tools.presentation.view_models.lifecycle_view import LifecycleView
from tools.presentation.adapters.observation_to_view_model import (
    observation_to_view_model,
)

__all__ = [
    "ObservationViewModel",
    "RuntimeStatusView",
    "PerformanceView",
    "ResourceView",
    "LifecycleView",
    "observation_to_view_model",
]
