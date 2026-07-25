"""tools/presentation/adapters/ — Phase 3.13 Mapping Adapter。

Adapter 单向数据流：ObservationReport → ObservationViewModel。
不修改 ObservationReport；不持有 Runtime 引用。
"""
from tools.presentation.adapters.observation_to_view_model import (
    observation_to_view_model,
)

__all__ = ["observation_to_view_model"]
