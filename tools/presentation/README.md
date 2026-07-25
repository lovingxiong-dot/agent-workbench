# tools/presentation/ — Phase 3.13 Observation Presentation & Consumption Layer

> **Status**: Phase 3.13-A Architecture Gate Approved → Phase 3.13-B Implementation Complete
> **Date**: 2026-07-25
> **ADR**: [ADR-017 Observation Presentation Boundary](../../.project/decisions/ADR-017-observation-presentation-boundary.md)

## 1. Purpose

Phase 3.13 让系统产生可见能力（Visible Capability）：

- 人类可读：Runtime Observation Panel
- 程序可读：JSON / Snapshot Export
- 人工阅读：Markdown Export

**非目标**（继承 ADR-016 + ADR-017）：

- ❌ Alert Engine
- ❌ Auto Optimization
- ❌ Runtime Feedback Loop
- ❌ Policy Adjustment
- ❌ Scheduler Tuning

## 2. Architecture

```
ObservationReport (Phase 3.12 Frozen ADR-016)
    |
    | observation_to_view_model
    v
ObservationViewModel (frozen)
    |
    +-> export_json
    +-> export_markdown
    +-> export_snapshot
    |
    v
RuntimeObservationPanel (v6/presentation/observation/)
    |
    v
ObservationPanelRenderer
    |
    v
UI Display (Read-only)
```

## 3. Directory Structure

```
tools/presentation/                    # Phase 3.13 主位置
├── __init__.py
├── view_models/                       # Frozen ViewModel
│   ├── observation_view_model.py      # 聚合 4 View
│   ├── runtime_status_view.py
│   ├── performance_view.py
│   ├── resource_view.py
│   └── lifecycle_view.py
├── adapters/                          # Mapping Adapter
│   └── observation_to_view_model.py
└── exports/                           # 3 种格式
    ├── json_export.py
    ├── markdown_export.py
    └── snapshot_export.py

v6/presentation/observation/           # UI 集成（NEW）
├── observation_panel.py
└── observation_renderer.py
```

## 4. Boundary Rules (ADR-017)

| 类别 | 规则 |
|------|------|
| Allowed imports | tools.observation / v6.runtime.types (read-only) |
| Forbidden imports | v6.runtime.orchestrator / EngineManager / PlannerLoop / CapabilityRouter / agent_workbench.runtime.* |
| ViewModel | frozen dataclass（不可变） |
| Adapter | 单向数据流（ObservationReport → ViewModel） |
| Panel | Read-only（不订阅 EventBus，不持有 Runtime 引用） |
| Export | 遵守 observation.v0.1 schema |

## 5. Re-Entry Triggers

| # | Trigger |
|---|---------|
| 1-8 | 继承 ADR-016 |
| 9 | ViewModel 直接 import RuntimeEvent |
| 10 | Panel subscribe EventBus |
| 11 | Export 写入 Runtime Contract 字段 |
| 12 | UI 直接访问 Runtime Artifact |
| 13 | ViewModel 保存状态（mutable） |
| 14 | Presentation 层计算 Metrics |

## 6. Quick Start

```python
from tools.observation.reports.observation_report import (
    ObservationReport,
    ObservationMetrics,
)
from tools.presentation.adapters.observation_to_view_model import (
    observation_to_view_model,
)
from tools.presentation.exports.json_export import export_json
from v6.presentation.observation import RuntimeObservationPanel

# Build ObservationReport (from Phase 3.12 EvidenceCollector)
report = ObservationReport(
    execution_id="exec-1",
    task_id="t1",
    metrics=ObservationMetrics(execution_latency_ms=1500.0),
)

# Convert to ViewModel
vm = observation_to_view_model(report)

# Export
json_str = export_json(vm)

# Display
panel = RuntimeObservationPanel(vm)
display = panel.render()
```

## 7. References

- [ADR-017 Observation Presentation Boundary](../../.project/decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../../.project/decisions/ADR-016-observation-layer-contract.md)
- [Phase 3.13 Scope Definition](../../docs/v6/phase3-13-presentation-consumption-design.md)
- [Phase 3.13 UI Boundary Design](../../docs/v6/phase3-13-ui-boundary-design.md)
- [Phase 3.13 Execution Batch Plan](../../docs/v6/phase3-13-execution-batch-plan.md)
