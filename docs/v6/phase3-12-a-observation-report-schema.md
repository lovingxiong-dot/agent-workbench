# Phase 3.12-A — ObservationReport Schema

> **Status**: SCHEMA — v0.1
> **Date**: 2026-07-25
> **Phase**: 3.12-A.4
> **Depends on**: 3.12-A.4 Derived Metrics Algorithm Spec

---

## 1. Purpose

冻结 ObservationReport 序列化 schema（用于 stdout JSON Lines 输出 / 测试 fixture）。

**重要**：这是 Observation 内部 schema，**不进入 Runtime Contract**。

---

## 2. ObservationReport Schema（v0.1）

### 2.1 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ObservationReport",
  "type": "object",
  "required": ["schema_version", "execution_id", "observed_at"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "observation.v0.1"
    },
    "execution_id": {
      "type": "string",
      "description": "Unique execution identifier (from RuntimeEvent payload)"
    },
    "task_id": {
      "type": "string",
      "description": "Task identifier"
    },
    "observed_at": {
      "type": "number",
      "description": "Unix timestamp when observation was generated"
    },
    "observation_window_ms": {
      "type": "number",
      "description": "Time window this observation covers (milliseconds)"
    },
    "metrics": {
      "type": "object",
      "properties": {
        "execution_latency_ms": {
          "type": ["number", "null"],
          "description": "TASK_STARTED → terminal event latency"
        },
        "cancellation_propagation_ms": {
          "type": ["number", "null"],
          "description": "Cancel initiated_at → TASK_CANCELLED timestamp"
        },
        "deadline_error_ms": {
          "type": ["number", "null"],
          "description": "actual finish - deadline_at (positive = late)"
        },
        "event_throughput": {
          "type": ["number", "null"],
          "description": "Events per second in window"
        }
      }
    },
    "registry_footprint": {
      "type": "object",
      "properties": {
        "entries": { "type": "integer", "minimum": 0 },
        "active_entries": { "type": "integer", "minimum": 0 },
        "terminal_entries": { "type": "integer", "minimum": 0 },
        "max_depth": { "type": "integer", "minimum": -1 },
        "memory_estimate_bytes": { "type": "integer", "minimum": 0 },
        "sampled_at": { "type": "number" }
      }
    },
    "event_count": {
      "type": "integer",
      "description": "Total events processed in window"
    },
    "data_sources": {
      "type": "object",
      "description": "Which Frozen Artifact sources were consumed",
      "properties": {
        "runtime_events": { "type": "boolean" },
        "runtime_trace": { "type": "boolean" },
        "execution_metadata": { "type": "boolean" },
        "registry_snapshot": { "type": "boolean" }
      }
    }
  }
}
```

### 2.2 Python Dataclass（Mapped from Schema）

```python
# tools/observation/reports/observation_report.py

from dataclasses import dataclass, field
from typing import Optional, Dict
import time

OBSERVATION_SCHEMA_VERSION = "observation.v0.1"


@dataclass(frozen=True)
class ObservationMetrics:
    execution_latency_ms: Optional[float]
    cancellation_propagation_ms: Optional[float]
    deadline_error_ms: Optional[float]
    event_throughput: Optional[float]


@dataclass(frozen=True)
class ObservationReport:
    execution_id: str
    task_id: str
    observed_at: float = field(default_factory=time.time)
    observation_window_ms: float = 0.0
    metrics: ObservationMetrics = field(
        default_factory=lambda: ObservationMetrics(None, None, None, None)
    )
    registry_footprint: Optional["FootprintSnapshot"] = None
    event_count: int = 0
    data_sources: Dict[str, bool] = field(
        default_factory=lambda: {
            "runtime_events": False,
            "runtime_trace": False,
            "execution_metadata": False,
            "registry_snapshot": False,
        }
    )
    schema_version: str = OBSERVATION_SCHEMA_VERSION

    def to_dict(self) -> dict:
        """序列化为 dict（用于 JSON Lines 输出）."""
        return {
            "schema_version": self.schema_version,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "observed_at": self.observed_at,
            "observation_window_ms": self.observation_window_ms,
            "metrics": {
                "execution_latency_ms": self.metrics.execution_latency_ms,
                "cancellation_propagation_ms": self.metrics.cancellation_propagation_ms,
                "deadline_error_ms": self.metrics.deadline_error_ms,
                "event_throughput": self.metrics.event_throughput,
            },
            "registry_footprint": (
                self.registry_footprint.to_dict()
                if self.registry_footprint
                else None
            ),
            "event_count": self.event_count,
            "data_sources": self.data_sources,
        }
```

### 2.3 FootprintSnapshot Dataclass

```python
# tools/observation/reports/footprint_snapshot.py

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class FootprintSnapshot:
    entries: int
    active_entries: int
    terminal_entries: int
    max_depth: int
    memory_estimate_bytes: int
    sampled_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "entries": self.entries,
            "active_entries": self.active_entries,
            "terminal_entries": self.terminal_entries,
            "max_depth": self.max_depth,
            "memory_estimate_bytes": self.memory_estimate_bytes,
            "sampled_at": self.sampled_at,
        }
```

---

## 3. Schema 演进规则

### 3.1 向后兼容原则

新增字段：
- ✅ 添加 Optional 字段（默认 None）
- ✅ 在 Schema Version 标记 minor 升级

修改/删除字段：
- 🚫 禁止（仅 major 版本才允许）
- 必须新 ADR + Re-Freeze

### 3.2 版本规则

```
observation.v0.x → observation.v0.(x+1)
  - Additive Optional 字段
  - 不破坏现有消费者

observation.v0.x → observation.v1.x
  - 字段重命名或语义变化
  - 必须 major ADR
```

---

## 4. 数据来源标记（data_sources）

每份 ObservationReport 标记使用了哪些 Frozen 数据源：

```python
data_sources = {
    "runtime_events": False,        # RuntimeEvent 流是否参与
    "runtime_trace": False,         # RuntimeTrace 是否参与
    "execution_metadata": False,    # ExecutionMetadata 是否参与
    "registry_snapshot": False,     # ExecutionRegistry snapshot 是否参与
}
```

**用途**：
- 审计 Report 是否覆盖预期来源
- 未来 Phase 3.13+ 持久化层做数据血缘追踪

---

## 5. 输出约定

### 5.1 stdout（默认）

```
{"schema_version": "observation.v0.1", "execution_id": "exec-001", ...}
{"schema_version": "observation.v0.1", "execution_id": "exec-002", ...}
```

JSON Lines format（每行一个 Report）。

### 5.2 文件（可选，不引入持久化层）

`tools/observation/output/{timestamp}.jsonl`（仅 investigation 工具，非 Phase 3.12-A 核心）

---

## 6. Do Not Touch

| 禁止 | 原因 |
|------|------|
| 修改 RuntimeEvent 字段 | Frozen |
| 修改 TASK_CANCELLED payload | Frozen（Phase 3.11-D） |
| 修改 ExecutionMetadata schema | Frozen |
| 修改 ExecutionRegistry API | Frozen |
| 修改 CapabilityRegistry | v6.9.6 Frozen |

---

## 7. Status

| Plan | 内容 | 状态 |
|------|------|------|
| 3.12-A.1 | Design | ✅ APPROVED |
| 3.12-A.2 | Observation Contract | 🟡 Review |
| 3.12-A.3 | Evidence Collection | 🟡 Review |
| 3.12-A.4 | Derived Metrics Spec + Report Schema（本） | 🟡 Review |
| 3.12-A.5 | Validation Plan | ⏳ Next |
| 3.12-A.6 | Tool Implementation | ⏳ Pending |